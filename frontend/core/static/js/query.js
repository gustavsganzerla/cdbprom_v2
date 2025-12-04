let currentPage = 1;


let originalThead = null;
let originalTbody = null;

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById('results-table');
  if (table) {
    originalThead = table.querySelector('thead').innerHTML;
    originalTbody = table.querySelector('tbody').innerHTML;
  }


  const form = document.getElementById("query-form");
  if (form) {
    form.addEventListener("submit", function(e) {
      e.preventDefault();
      fetchData(1);
    });
  }


  document.addEventListener("click", (e) => {
    if (e.target.classList.contains("view-icon")) {
      const organismName = e.target.dataset.organism;
      fetchData(1, organismName);
    }
  });
});

function renderPaginationControls(totalPages, currentPage) {
  const container = document.getElementById('pagination');
  if (!container) return; // skip if no pagination element

  container.innerHTML = '';

  const createButton = (label, page, disabled = false) => {
    const btn = document.createElement('button');
    btn.textContent = label;
    btn.disabled = disabled;
    btn.onclick = () => fetchData(page);
    return btn;
  };

  container.appendChild(createButton("First", 1, currentPage === 1));
  container.appendChild(createButton("Prev", Math.max(1, currentPage - 1), currentPage === 1));

  container.appendChild(createButton(1, 1, currentPage === 1));

  if (currentPage > 4) {
    const ellipsisLeft = document.createElement('span');
    ellipsisLeft.textContent = '...';
    ellipsisLeft.style.margin = '0 5px';
    container.appendChild(ellipsisLeft);
  }

  const startPage = Math.max(2, currentPage - 1);
  const endPage = Math.min(totalPages - 1, currentPage + 1);
  for (let i = startPage; i <= endPage; i++) {
    container.appendChild(createButton(i, i, currentPage === i));
  }

  if (currentPage < totalPages - 3) {
    const ellipsisRight = document.createElement('span');
    ellipsisRight.textContent = '...';
    ellipsisRight.style.margin = '0 5px';
    container.appendChild(ellipsisRight);
  }

  if (totalPages > 1) {
    container.appendChild(createButton(totalPages, totalPages, currentPage === totalPages));
  }

  container.appendChild(createButton("Next", Math.min(totalPages, currentPage + 1), currentPage === totalPages));
  container.appendChild(createButton("Last", totalPages, currentPage === totalPages));
}

function fetchData(page = 1, organismOverride = null) {
  currentPage = page;


  const organismField = document.getElementById("organism");
  const annotationField = document.getElementById("annotation");
  const ncbiField = document.getElementById("ncbi");

  const organism = organismOverride
      ? encodeURIComponent(organismOverride)
      : (organismField ? encodeURIComponent(organismField.value) : '');
  const annotation = annotationField ? encodeURIComponent(annotationField.value) : '';
  const ncbiID = ncbiField ? encodeURIComponent(ncbiField.value) : '';

  const params = new URLSearchParams();
  if (organism) params.append("organism_name", organism);
  if (annotation) params.append("annotation", annotation);
  if (ncbiID) params.append("ncbi_id", ncbiID);
  params.append("page", page);

  fetch(`/api/query/?${params.toString()}`)
    .then(response => response.json())
    .then(data => {
      const table = document.getElementById('results-table');
      if (!table) return;

      const tbody = table.querySelector('tbody');
      const thead = table.querySelector('thead');

      // total records
      const resultsCount = document.getElementById('results-count');
      if (resultsCount) {
        resultsCount.innerHTML = `Total records: <strong>${data.count}</strong>`;
      }

      //downloa button
      const downloadContainer = document.getElementById('download-container');
      if (downloadContainer) {
        downloadContainer.innerHTML = "";
        if (data.results.length > 0) {
          const btn = document.createElement('button');
          btn.className = 'btn';
          btn.textContent = 'Download';

          btn.dataset.organism = organismOverride || (document.getElementById("organism")?.value || "");

          
          downloadContainer.appendChild(btn);
        }
      }

      if (data.results && data.results.length > 0) {
        // Update table header for query results
        thead.innerHTML = `
          <tr>
            <th>NCBI ID</th>
            <th>Organism Name</th>
            <th>Sequence</th>
            <th>Annotation</th>
          </tr>
        `;

        // Fill table body
        tbody.innerHTML = data.results.map(item => `
          <tr>
            <td>${item.ncbi_id}</td>
            <td>${item.organism_name}</td>
            <td>${item.sequence}</td>
            <td>${item.annotation}</td>
          </tr>
        `).join('');
        table.style.display = 'table';
      } else {
        // If no results, restore original organisms table
        thead.innerHTML = originalThead;
        tbody.innerHTML = originalTbody;
        table.style.display = 'table';
      }

      //pagination
      const totalPages = Math.ceil(data.count / 10);
      renderPaginationControls(totalPages, page);
    })
    .catch(err => {
      console.error(err);
      const resultsCount = document.getElementById('results-count');
      if (resultsCount) resultsCount.textContent = 'Error fetching data.';
    });
}
