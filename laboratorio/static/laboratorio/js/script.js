function change(title) {
    let mapping = {"1": "Listado de laboratorios", "2": "Listado de directores", "3": "Listado de productos"}
    if (Object.keys(mapping).includes(title)) {
        document.getElementById("current-title").innerText = mapping[title];
    }
    document.getElementById("change_target").close();
}

function update_total(value) {
    let number = document.getElementById("id_cantidad").value;
    document.getElementById("subtotal").innerText = `Subtotal: $${Number.parseInt(number) * value}`;
}