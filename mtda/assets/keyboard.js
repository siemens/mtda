/* ---------------------------------------------------------------------------
   Copyright (c) 2022 by Dom (https://codepen.io/dcode-software/pen/KYYKxP)
   ---------------------------------------------------------------------------
   SPDX-License-Identifier: MIT
   ---------------------------------------------------------------------------
*/

const Keyboard = {
  elements: {
    main: null,
    keysContainer: null,
    keys: []
  },

  eventHandlers: {
    oninput: null,
    onclose: null
  },

  properties: {
    value: "",
    capsLock: false
  },

  init() {
    // Create main elements
    this.elements.main = document.createElement("div");
    this.elements.keysContainer = document.createElement("div");

    // Setup main elements
    this.elements.main.classList.add("keyboard", "keyboard--hidden");
    this.elements.keysContainer.classList.add("keyboard__keys");
    this.elements.keysContainer.appendChild(this._createKeys());

    this.elements.keys = this.elements.keysContainer.querySelectorAll(".keyboard__key");

    // Add to DOM
    this.elements.main.appendChild(this.elements.keysContainer);
    document.body.appendChild(this.elements.main);

    // Automatically use keyboard for elements with .use-keyboard-input
    document.querySelectorAll(".use-keyboard-input").forEach(element => {
      element.addEventListener("focus", () => {
        this.open(element.value, currentValue => {
          element.value = currentValue;
        });
      });
    });
  },

  _createKeys() {
    const fragment = document.createDocumentFragment();
    const keyLayout = [
      "Esc", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "PrtSrc", "Insert", "Delete",
      "`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "Backspace",
      "Tab", "q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "[", "]", "\\",
      "Caps Lock", "a", "s", "d", "f", "g", "h", "j", "k", "l", ";", "'", "Enter",
      "Shift", "z", "x", "c", "v", "b", "n", "m", ",", ".", "/", "done",
      "Ctrl", "Alt", "Space", "Alt", "Ctrl", "Left", "Right", "Up", "Down"
    ];

    // Creates HTML for an icon
    const createIconHTML = (icon_name) => {
      return `<i class="material-icons">${icon_name}</i>`;
    };

    keyLayout.forEach(key => {
      const keyElement = document.createElement("button");
      const insertLineBreak = ["Delete", "Backspace", "\\", "Enter", "done"].indexOf(key) !== -1;

      // Add attributes/classes
      keyElement.setAttribute("type", "button");
      keyElement.classList.add("keyboard__key");

      switch (key) {
        case "Left":
          keyElement.classList.add("keyboard__key--tiny");
          keyElement.innerHTML = createIconHTML("arrow_back");

          keyElement.addEventListener("click", () => {
            this.properties.value = key;
            this._triggerEvent("oninput");
          });
          break;

        case "Right":
          keyElement.classList.add("keyboard__key--tiny");
          keyElement.innerHTML = createIconHTML("arrow_forward");

          keyElement.addEventListener("click", () => {
            this.properties.value = key;
            this._triggerEvent("oninput");
          });
          break;

        case "Up":
          keyElement.classList.add("keyboard__key--tiny");
          keyElement.innerHTML = createIconHTML("arrow_upward");

          keyElement.addEventListener("click", () => {
            this.properties.value = key;
            this._triggerEvent("oninput");
          });
          break;

        case "Down":
          keyElement.classList.add("keyboard__key--tiny");
          keyElement.innerHTML = createIconHTML("arrow_downward");

          keyElement.addEventListener("click", () => {
            this.properties.value = key;
            this._triggerEvent("oninput");
          });
          break;

        case "Backspace":
          keyElement.classList.add("keyboard__key--wide");
          keyElement.innerHTML = createIconHTML("backspace");

          keyElement.addEventListener("click", () => {
            this.properties.value = key;
            this._triggerEvent("oninput");
          });
          break;

        case "Caps Lock":
          keyElement.classList.add("keyboard__key--wide", "keyboard__key--activatable");
          keyElement.innerHTML = createIconHTML("keyboard_capslock");

          keyElement.addEventListener("click", () => {
            this.properties.value = key;
            this._triggerEvent("oninput");
            this._toggleCapsLock();
            keyElement.classList.toggle("keyboard__key--active", this.properties.capsLock);
          });
          break;

        case "Enter":
          keyElement.classList.add("keyboard__key--wide");
          keyElement.innerHTML = createIconHTML("keyboard_return");

          keyElement.addEventListener("click", () => {
            this.properties.value = key;
            this._triggerEvent("oninput");
          });
          break;

        case "Space":
          keyElement.classList.add("keyboard__key--extra-wide");
          keyElement.innerHTML = createIconHTML("space_bar");

          keyElement.addEventListener("click", () => {
            this.properties.value = " ";
            this._triggerEvent("oninput");
          });
          break;

        case "done":
          keyElement.classList.add("keyboard__key--wide", "keyboard__key--dark");
          keyElement.innerHTML = createIconHTML("keyboard_hide");

          keyElement.addEventListener("click", () => {
            this.close();
            this._triggerEvent("onclose");
          });
          break;

        default:
          keyElement.textContent = key
          if (key.length > 1) {
            keyElement.classList.add("keyboard__key--tiny");
          }
          keyElement.addEventListener("click", () => {
            this.properties.value = key;
            this._triggerEvent("oninput");
          });
          break;
      }

      fragment.appendChild(keyElement);
      if (insertLineBreak) {
        fragment.appendChild(document.createElement("br"));
      }
    });
    return fragment;
  },

  _triggerEvent(handlerName) {
    if (typeof this.eventHandlers[handlerName] == "function") {
      this.eventHandlers[handlerName](this.properties.value);
    }
  },

  _toggleCapsLock() {
    this.properties.capsLock = !this.properties.capsLock;

    for (const key of this.elements.keys) {
      if (key.childElementCount === 0) {
        text = key.textContent
        if (text.length == 1) {
          c = text.toLowerCase().charAt(0);
          if (c >= 'a' && c <= 'z') {
            key.textContent = this.properties.capsLock ? text.toUpperCase() : text.toLowerCase();
          }
          else {
            map = {
              '`': '~', '~': '`',
              '1': '!', '!': '1',
              '2': '@', '@': '2',
              '3': '#', '#': '3',
              '4': '$', '$': '4',
              '5': '%', '%': '5',
              '6': '^', '^': '6',
              '7': '&', '&': '7',
              '8': '*', '*': '8',
              '9': '(', '(': '9',
              '0': ')', ')': '0',
              '-': '_', '_': '-',
              '=': '+', '+': '=',
              '[': '{', '{': '[',
              ']': '}', '}': ']',
              '\\': '|', '|': '\\',
              ';': ':', ':': ';',
              '\'': '"', '"': '\'',
              ',': '<', '<': ',',
              '.': '>', '>': '.',
              '/': '?', '?': '/'
            }
            key.textContent = map[c]
          }
        }
      }
    }
  },

  open(initialValue, oninput, onclose) {
    this.properties.value = initialValue || "";
    this.eventHandlers.oninput = oninput;
    this.eventHandlers.onclose = onclose;
    this.elements.main.classList.remove("keyboard--hidden");
  },

  close() {
    this.properties.value = "";
    this.eventHandlers.oninput = oninput;
    this.eventHandlers.onclose = onclose;
    this.elements.main.classList.add("keyboard--hidden");
  }
};

window.addEventListener("DOMContentLoaded", function () {
  Keyboard.init();
});
