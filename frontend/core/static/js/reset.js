///JS to clear the forms
document.addEventListener("DOMContentLoaded", () => {
  const form1 = document.getElementById("query-form");
  const resultsDiv = document.getElementById("results");
  const resultsTable = document.getElementById("results-table");
  const resultsCount = document.getElementById("results-count");
  const pagination = document.getElementById("pagination");
  const downloadContainer = document.getElementById('download-container');
  

  const clearBtn = document.getElementById("reset-form");

  clearBtn.addEventListener("click", () => {
    // clear form fields
    form1.reset();

    // clear results
    resultsDiv.innerHTML = "";
    resultsCount.innerHTML = "";
    pagination.innerHTML = "";
    downloadContainer.innerHTML = "";

    // clear table body and hide it
    resultsTable.querySelector("tbody").innerHTML = "";
    resultsTable.style.display = "none";
  });
});
