document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("organism");
  const list = document.getElementById("autocomplete-list");
  const MIN_LENGTH = 3;

  let currentIndex = -1;

  if (!input || !list) return;

  function clearList() {
    list.innerHTML = "";
    list.style.display = "none";
    currentIndex = -1;
  }

  function highlightMatch(text, term) {
    const regex = new RegExp(`(${term})`, "ig");
    return text.replace(regex, "<strong>$1</strong>");
  }

  input.addEventListener("input", function () {
    const term = this.value.trim();
    clearList();

    if (term.length < MIN_LENGTH) return;

    fetch(`/autocomplete_organism_name/?q=${encodeURIComponent(term)}`)
      .then(res => res.json())
      .then(data => {
        if (!data.length) return;

        data.forEach((item, index) => {
          const li = document.createElement("li");
          li.innerHTML = highlightMatch(item, term);
          li.dataset.index = index;

          li.addEventListener("click", () => {
            input.value = item;
            clearList();
          });

          list.appendChild(li);
        });

        list.style.display = "block";
      });
  });



  // Close when clicking outside
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".autocomplete-wrapper")) {
      clearList();
    }
  });
});
