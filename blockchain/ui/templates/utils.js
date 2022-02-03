function toggleButtonColumns(button) {
    let items = document.querySelectorAll(".collapsible");
    let button_value = button.getAttribute("value");
    if (button_value.startsWith("Show")) {
        let value = button_value.replace("Show", "Hide");
        value = value.replace(">", "<");
        button.setAttribute("value", value);
        items.forEach(function(el) {
            el.classList.remove("collapsed");
        });
    }
    else {
        let value = button_value.replace("Hide", "Show");
        value = value.replace("<", ">");
        button.setAttribute("value", value);
        items.forEach(function(el) {
            el.classList.add("collapsed");
        });
    }
}
