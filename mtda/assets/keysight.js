/* ---------------------------------------------------------------------------
   Copyright (c) 2013 by fresheneesz (https://github.com/fresheneesz/keysight)
   ---------------------------------------------------------------------------
   SPDX-License-Identifier: MIT
   ---------------------------------------------------------------------------
*/

! function(e, n) {
    "object" == typeof exports && "object" == typeof module ? module.exports = n() : "function" == typeof define && define.amd ? define(n) : "object" == typeof exports ? exports.keysight = n() : e.keysight = n()
}(this, function() {
    return function(e) {
        function n(t) {
            if (r[t]) return r[t].exports;
            var f = r[t] = {
                exports: {},
                id: t,
                loaded: !1
            };
            return e[t].call(f.exports, f, f.exports, n), f.loaded = !0, f.exports
        }
        var r = {};
        return n.m = e, n.c = r, n.p = "", n(0)
    }([function(e) {
        function n(e) {
            var n = String.fromCharCode(e);
            return n in t ? t[n] : n in s ? s[n] : n.toLowerCase()
        }
        var r = {
                "/": "?",
                ".": ">",
                ",": "<",
                "'": '"',
                ";": ":",
                "[": "{",
                "]": "}",
                "\\": "|",
                "`": "~",
                "=": "+",
                "-": "_",
                1: "!",
                2: "@",
                3: "#",
                4: "$",
                5: "%",
                6: "^",
                7: "&",
                8: "*",
                9: "(",
                0: ")"
            },
            t = {};
        for (var f in r) {
            var o = r[f];
            t[o] = f
        }
        var i = {
                0: "\\",
                8: "\b",
                9: "	",
                12: "num",
                13: "\n",
                16: "shift",
                17: "meta",
                18: "alt",
                19: "pause",
                20: "caps",
                27: "esc",
                32: " ",
                33: "pageup",
                34: "pagedown",
                35: "end",
                36: "home",
                37: "left",
                38: "up",
                39: "right",
                40: "down",
                44: "print",
                45: "insert",
                46: "delete",
                91: "cmd",
                92: "cmd",
                93: "cmd",
                96: "num0",
                97: "num1",
                98: "num2",
                99: "num3",
                100: "num4",
                101: "num5",
                102: "num6",
                103: "num7",
                104: "num8",
                105: "num9",
                106: "*",
                107: "+",
                108: "num_enter",
                109: "num_subtract",
                110: "num_decimal",
                111: "num_divide",
                112: "f1",
                113: "f2",
                114: "f3",
                115: "f4",
                116: "f5",
                117: "f6",
                118: "f7",
                119: "f8",
                120: "f9",
                121: "f10",
                122: "f11",
                123: "f12",
                124: "print",
                144: "num",
                145: "scroll",
                173: "-",
                186: ";",
                187: "=",
                188: ",",
                189: "-",
                190: ".",
                191: "/",
                192: "`",
                219: "[",
                220: "\\",
                221: "]",
                222: "'",
                223: "`",
                224: "cmd",
                225: "alt",
                57392: "ctrl",
                63289: "num"
            },
            a = {};
        for (var f in i) {
            var u = i[f];
            a[u] = f
        }
        var s = {
                "\r": "\n"
            },
            d = {
                num_subtract: "-",
                num_enter: "\n",
                num_decimal: ".",
                num_divide: "/"
            };
        e.exports = function(e) {
            if ("keypress" === e.type) var t = n(e.charCode);
            else if (void 0 !== e.keyCode)
                if (e.keyCode in i) var t = i[e.keyCode];
                else var t = String.fromCharCode(e.keyCode).toLowerCase();
            else if (0 === e.charCode) var t = "\n";
            if (e.shiftKey && t in r) var f = r[t];
            else if (!e.shiftKey || t in a)
                if (t in d) var f = d[t];
                else var f = t;
            else var f = t.toUpperCase();
            return {
                "char": f,
                key: t
            }
        }, e.exports.unprintableKeys = {
            "\b": 1,
            num: 1,
            shift: 1,
            meta: 1,
            alt: 1,
            pause: 1,
            caps: 1,
            esc: 1,
            pageup: 1,
            pagedown: 1,
            end: 1,
            home: 1,
            left: 1,
            up: 1,
            right: 1,
            down: 1,
            print: 1,
            insert: 1,
            "delete": 1,
            cmd: 1,
            f1: 1,
            f2: 1,
            f3: 1,
            f4: 1,
            f5: 1,
            f6: 1,
            f7: 1,
            f8: 1,
            f9: 1,
            f10: 1,
            f11: 1,
            f12: 1,
            scroll: 1,
            ctrl: 1
        }
    }])
});
