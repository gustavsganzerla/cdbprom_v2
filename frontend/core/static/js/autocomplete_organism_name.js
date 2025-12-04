document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("organism");
  const list = document.getElementById("autocomplete-list");



  if (!input || !list) return;

  input.addEventListener("input", function () {
    const term = this.value.trim();

    // clear previous suggestions
    list.innerHTML = "";
    list.style.display = "none"; // hide before repopulating

    if (!term) return;

    fetch(`/autocomplete_organism_name/?q=${encodeURIComponent(term)}`)
      .then(response => response.json())
      .then(data => {
        if (!data.length) return;
        console.log(data);

        data.forEach(item => {
          const li = document.createElement("li");
          li.textContent = item;
          li.addEventListener("click", () => {
            input.value = item; // set input value
            list.innerHTML = ""; // clear
            list.style.display = "none"; // hide suggestions
          });
          list.appendChild(li);
        });

        list.style.display = "block"; // <--- show results!
      });
  });

  // Optional: close the list if clicking outside
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".autocomplete-wrapper")) {
      list.innerHTML = "";
      list.style.display = "none";
    }
  });
});
