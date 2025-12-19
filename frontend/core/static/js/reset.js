document.addEventListener("DOMContentLoaded", () => {
  const clearBtn = document.getElementById("reset-form");
  if (!clearBtn) return; // exit if no reset button found

  clearBtn.addEventListener("click", () => {
    // Try to reset a form if it exists
    const form = document.getElementById("query-form");
    if (form) form.reset();

    // List of result elements to clear (update IDs as needed)
    const elementsToClear = [
      "results",
      "results-table",
      "results-query",
      "results-count",
      "pagination",
      "download-container",
      "results-container"
    ];

    elementsToClear.forEach(id => {
      const el = document.getElementById(id);
      if (!el) return;
      
      // clear table body and hide table
      if (el.tagName === "TABLE") {
        const tbody = el.querySelector("tbody");
        if (tbody) tbody.innerHTML = "";
        el.style.display = "none";
      } else {
        el.innerHTML = "";
      }
    });

    // Optionally clear all inputs outside a form
    document.querySelectorAll("input, textarea, select").forEach(input => input.value = "");
  });
});
