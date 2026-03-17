# ---------------------------------------------------------------------------
# MTDA gRPC Servicer
# ---------------------------------------------------------------------------
#
# This software is a part of MTDA.
# Copyright (C) 2026 Siemens AG
#
# ---------------------------------------------------------------------------
# SPDX-License-Identifier: MIT
# ---------------------------------------------------------------------------

import json
import queue

import grpc

from mtda.grpc import mtda_pb2
from mtda.grpc import mtda_pb2_grpc


def _session(context):
    """Extract the mtda-session value from gRPC call metadata."""
    for key, value in context.invocation_metadata():
        if key == 'mtda-session':
            return value
    return None


def _str_response(value):
    if value is None:
        return mtda_pb2.StringResponse(has_value=False, value='')
    return mtda_pb2.StringResponse(has_value=True, value=str(value))


def _bool_response(value):
    return mtda_pb2.BoolResponse(value=bool(value))


class MtdaServicer(mtda_pb2_grpc.MtdaServiceServicer):
    """gRPC servicer that delegates every call to a MultiTenantDeviceAccess
    instance.  Exceptions raised by the agent are converted to gRPC status
    codes so callers receive proper RPC errors."""

    def __init__(self, agent):
        self._agent = agent

    # ------------------------------------------------------------------
    # Agent
    # ------------------------------------------------------------------

    def AgentVersion(self, request, context):
        try:
            ver = self._agent.agent_version(session=_session(context))
            return mtda_pb2.AgentVersionResponse(version=ver or '')
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    # ------------------------------------------------------------------
    # Power / command
    # ------------------------------------------------------------------

    def Command(self, request, context):
        try:
            result = self._agent.command(request.args,
                                         session=_session(context))
            return _bool_response(result)
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def ConfigSetPowerTimeout(self, request, context):
        try:
            prev = self._agent.config_set_power_timeout(
                request.timeout, session=_session(context))
            return mtda_pb2.Int32Response(value=int(prev or 0))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def ConfigSetSessionTimeout(self, request, context):
        try:
            prev = self._agent.config_set_session_timeout(
                request.timeout, session=_session(context))
            return mtda_pb2.Int32Response(value=int(prev or 0))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    # ------------------------------------------------------------------
    # Console
    # ------------------------------------------------------------------

    def ConsoleClear(self, request, context):
        try:
            return _str_response(
                self._agent.console_clear(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def ConsoleDump(self, request, context):
        try:
            return _str_response(
                self._agent.console_dump(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def ConsoleFlush(self, request, context):
        try:
            return _str_response(
                self._agent.console_flush(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def ConsoleHead(self, request, context):
        try:
            return _str_response(
                self._agent.console_head(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def ConsoleLines(self, request, context):
        try:
            n = self._agent.console_lines(session=_session(context))
            return mtda_pb2.ConsoleLinesResponse(lines=int(n or 0))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def ConsolePrint(self, request, context):
        try:
            return _str_response(
                self._agent.console_print(request.data,
                                          session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def ConsolePrompt(self, request, context):
        try:
            new_prompt = None if request.get_only else request.new_prompt
            return _str_response(
                self._agent.console_prompt(new_prompt,
                                           session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def ConsoleRun(self, request, context):
        try:
            return _str_response(
                self._agent.console_run(request.cmd,
                                        session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def ConsoleSend(self, request, context):
        try:
            return _str_response(
                self._agent.console_send(request.data, request.raw,
                                         session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def ConsoleTail(self, request, context):
        try:
            return _str_response(
                self._agent.console_tail(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def ConsoleToggle(self, request, context):
        try:
            self._agent.console_toggle(session=_session(context))
            return mtda_pb2.Empty()
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def ConsoleWait(self, request, context):
        """Server-streaming: stream matched output lines back to the client."""
        try:
            timeout = request.timeout if request.timeout > 0 else None
            result = self._agent.console_wait(request.what, timeout,
                                              session=_session(context))
            if result is not None:
                for line in str(result).splitlines():
                    yield mtda_pb2.ConsoleLineResponse(line=line)
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    # ------------------------------------------------------------------
    # Env
    # ------------------------------------------------------------------

    def EnvGet(self, request, context):
        try:
            return _str_response(
                self._agent.env_get(request.name, request.default or None,
                                    session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def EnvSet(self, request, context):
        try:
            return _str_response(
                self._agent.env_set(request.name, request.value,
                                    session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    # ------------------------------------------------------------------
    # Events / console subscription
    # ------------------------------------------------------------------

    def Subscribe(self, request, context):
        """Long-lived server-streaming RPC.  Pushes console bytes (topic CON
        or MON) and async events (topic EVT) to the client as they occur.
        The stream stays open until the client cancels or disconnects."""
        q = self._agent.subscribe()
        try:
            while context.is_active():
                try:
                    topic, data = q.get(timeout=1.0)
                except queue.Empty:
                    continue
                if isinstance(topic, bytes):
                    topic = topic.decode("utf-8")
                if isinstance(data, str):
                    data = data.encode("utf-8")
                yield mtda_pb2.EventMessage(topic=topic, data=data)
        finally:
            self._agent.unsubscribe(q)

    # ------------------------------------------------------------------
    # Keyboard
    # ------------------------------------------------------------------

    def KeyboardPress(self, request, context):
        try:
            return _str_response(
                self._agent.keyboard_press(
                    request.key, request.repeat,
                    request.ctrl, request.shift, request.alt, request.meta,
                    session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def KeyboardWrite(self, request, context):
        try:
            return _str_response(
                self._agent.keyboard_write(request.what,
                                           session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    # ------------------------------------------------------------------
    # Mouse
    # ------------------------------------------------------------------

    def MouseMove(self, request, context):
        try:
            return _str_response(
                self._agent.mouse_move(request.x, request.y, request.buttons,
                                       session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    # ------------------------------------------------------------------
    # Monitor
    # ------------------------------------------------------------------

    def MonitorSend(self, request, context):
        try:
            return _str_response(
                self._agent.monitor_send(request.data, request.raw,
                                         session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def MonitorWait(self, request, context):
        try:
            timeout = request.timeout if request.timeout > 0 else None
            result = self._agent.monitor_wait(request.what, timeout,
                                              session=_session(context))
            if result is not None:
                for line in str(result).splitlines():
                    yield mtda_pb2.ConsoleLineResponse(line=line)
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------

    def StorageBmapDict(self, request, context):
        try:
            bmap = json.loads(request.json) if request.has_dict else None
            result = self._agent.storage_bmap_dict(bmap,
                                                   session=_session(context))
            return _bool_response(result)
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def StorageClose(self, request, context):
        try:
            return _bool_response(
                self._agent.storage_close(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def StorageCommit(self, request, context):
        try:
            return _bool_response(
                self._agent.storage_commit(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def StorageCompression(self, request, context):
        try:
            # compression is transmitted as a decimal string of the IMAGE enum
            # integer value; convert it back before passing to the agent.
            comp = request.compression
            if comp:
                try:
                    comp = int(comp)
                except ValueError:
                    pass
            return _str_response(
                self._agent.storage_compression(comp,
                                                session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def StorageFlush(self, request, context):
        try:
            return _bool_response(
                self._agent.storage_flush(request.size,
                                          session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def StorageMount(self, request, context):
        try:
            part = request.part if request.has_part else None
            return _bool_response(
                self._agent.storage_mount(part, session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def StorageNetwork(self, request, context):
        try:
            return _bool_response(
                self._agent.storage_network(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def StorageOpen(self, request, context):
        try:
            self._agent.storage_open(request.size,
                                     session=_session(context))
            return mtda_pb2.StorageOpenResponse()
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def StorageRollback(self, request, context):
        try:
            return _bool_response(
                self._agent.storage_rollback(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def StorageStatus(self, request, context):
        try:
            status, writing, written = self._agent.storage_status(
                session=_session(context))
            return mtda_pb2.StorageStatusResponse(
                status=str(status or ''),
                writing=bool(writing),
                written=int(written or 0))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def StorageSwap(self, request, context):
        try:
            result = self._agent.storage_swap(session=_session(context))
            return mtda_pb2.StorageToggleResponse(status=str(result or ''))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def StorageToHost(self, request, context):
        try:
            return _bool_response(
                self._agent.storage_to_host(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def StorageToTarget(self, request, context):
        try:
            return _bool_response(
                self._agent.storage_to_target(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def StorageToggle(self, request, context):
        try:
            result = self._agent.storage_toggle(session=_session(context))
            return mtda_pb2.StorageToggleResponse(status=str(result or ''))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def StorageUpdate(self, request, context):
        try:
            self._agent.storage_update(request.dst, request.size,
                                       session=_session(context))
            return mtda_pb2.StorageOpenResponse()
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def StorageWrite(self, request_iterator, context):
        """Client-streaming RPC: receive image chunks and push them to the
        background writer via agent.storage_write().  An empty data field
        (b'') signals end-of-transfer."""
        session = _session(context)
        ok = True
        try:
            for req in request_iterator:
                # Push each chunk (including the empty sentinel) to the writer
                self._agent.storage_write(req.data, session=session)
                if not req.data:
                    # sentinel received — stop iterating
                    break
        except Exception as e:
            ok = False
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        return mtda_pb2.StorageWriteResponse(ok=ok)

    # ------------------------------------------------------------------
    # Target / power
    # ------------------------------------------------------------------

    def TargetLock(self, request, context):
        try:
            return _bool_response(
                self._agent.target_lock(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def TargetLocked(self, request, context):
        try:
            return _bool_response(
                self._agent.target_locked(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def TargetOff(self, request, context):
        try:
            return _bool_response(
                self._agent.target_off(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def TargetOn(self, request, context):
        try:
            return _bool_response(
                self._agent.target_on(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def TargetStatus(self, request, context):
        try:
            result = self._agent.target_status(session=_session(context))
            return mtda_pb2.TargetStatusResponse(status=str(result or ''))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def TargetToggle(self, request, context):
        try:
            result = self._agent.target_toggle(session=_session(context))
            return mtda_pb2.TargetStatusResponse(status=str(result or ''))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def TargetUnlock(self, request, context):
        try:
            return _bool_response(
                self._agent.target_unlock(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def TargetUptime(self, request, context):
        try:
            result = self._agent.target_uptime(session=_session(context))
            return mtda_pb2.TargetUptimeResponse(uptime=float(result or 0))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def ToggleTimestamps(self, request, context):
        try:
            return _bool_response(
                self._agent.toggle_timestamps(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    # ------------------------------------------------------------------
    # USB
    # ------------------------------------------------------------------

    def UsbFindByClass(self, request, context):
        try:
            sw = self._agent.usb_find_by_class(request.class_name,
                                               session=_session(context))
            # Return the class name of the found switch, or empty if None
            return _str_response(
                getattr(sw, 'className', None) if sw is not None else None)
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def UsbHasClass(self, request, context):
        try:
            return _bool_response(
                self._agent.usb_has_class(request.class_name,
                                          session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def UsbOff(self, request, context):
        try:
            self._agent.usb_off(request.ndx, session=_session(context))
            return mtda_pb2.Empty()
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def UsbOffByClass(self, request, context):
        try:
            return _bool_response(
                self._agent.usb_off_by_class(request.class_name,
                                             session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def UsbOn(self, request, context):
        try:
            self._agent.usb_on(request.ndx, session=_session(context))
            return mtda_pb2.Empty()
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def UsbOnByClass(self, request, context):
        try:
            return _bool_response(
                self._agent.usb_on_by_class(request.class_name,
                                            session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def UsbPorts(self, request, context):
        try:
            return mtda_pb2.UsbPortsResponse(
                ports=self._agent.usb_ports(session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def UsbStatus(self, request, context):
        try:
            result = self._agent.usb_status(request.ndx,
                                            session=_session(context))
            return mtda_pb2.UsbStatusResponse(status=str(result or ''))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def UsbToggle(self, request, context):
        try:
            self._agent.usb_toggle(request.ndx, session=_session(context))
            return mtda_pb2.Empty()
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    # ------------------------------------------------------------------
    # Video
    # ------------------------------------------------------------------

    def VideoFormat(self, request, context):
        try:
            result = self._agent.video_format(session=_session(context))
            if result is None:
                return mtda_pb2.VideoFormatResponse(has_value=False, value='')
            return mtda_pb2.VideoFormatResponse(has_value=True,
                                                value=str(result))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))

    def VideoUrl(self, request, context):
        try:
            opts = request.opts if request.has_opts else None
            return _str_response(
                self._agent.video_url(request.host, opts,
                                      session=_session(context)))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))
