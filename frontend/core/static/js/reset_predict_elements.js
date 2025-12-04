///JS to clear the forms
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("new-form");
    const resultsContainer = document.getElementById("results-container");
    const downloadContainer = document.getElementById("download-container");
    const clearBtn = document.getElementById("reset-form");
  
    clearBtn.addEventListener("click", () => {
      // clear form fields
      form.reset();
  
      // clear results
      resultsContainer.innerHTML = "";
      downloadContainer.innerHTML = "";
  
    });
  });
  