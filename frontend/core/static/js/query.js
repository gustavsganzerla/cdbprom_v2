let currentPage = 1;
let originalThead = null;
let originalTbody = null;

let currentOrganismOverride = null;
let currentFamilyOverride = null;

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
      currentOrganismOverride = null;
      fetchData(1);
    });
  }

  document.addEventListener("click", (e) => {
    if (e.target.classList.contains("view-icon")) {
      currentOrganismOverride = e.target.dataset.organismId;
      fetchData(1);
    }
    if (e.target.classList.contains("view-family-icon")) {
      currentFamilyOverride = e.target.dataset.family;
      currentOrganismOverride = null; 
      fetchData(1);
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

  if (organismOverride !== null) {
    currentOrganismOverride = organismOverride;
  }

  const organismField = document.getElementById("organism");
  const annotationField = document.getElementById("annotation");
  const ncbiField = document.getElementById("ncbi");
  

  const organismName =
    currentOrganismOverride === null
    ? (organismField ? encodeURIComponent(organismField.value) : '')
    : '';

  const organismId =
    currentOrganismOverride !== null
    ? currentOrganismOverride
    : '';
  
  const annotation = annotationField ? annotationField.value : '';
  const ncbiID = ncbiField ? encodeURIComponent(ncbiField.value) : '';

  const family = currentFamilyOverride || '';


  const params = new URLSearchParams();
  if (organismName) params.append("organism_name", organismName);
  if (annotation) params.append("annotation", annotation);
  if (ncbiID) params.append("ncbi_id", ncbiID);
  if (family) params.append("family", family);
  if (organismId) params.append("organism_id", organismId);

  

  params.append("page", page);
  
  

  fetch(`/api/query/?${params.toString()}`)
    .then(response => response.json())
    .then(data => {
      const resultsCard = document.getElementById('results-card');
      resultsCard.style.display = 'block';
      const table = document.getElementById('results-table');
      if (!table) return;
      const tbody = table.querySelector('tbody');
      const thead = table.querySelector('thead');

      //show the query
      const resultsQuery = document.getElementById('results-query');

      if (resultsQuery) {
        let content = [];
        if (organismName) content.push(`Organism: <strong>${organismName}</strong>`);
        if (annotation)content.push(`Annotation: <strong>${decodeURIComponent(annotation)}</strong>`);
        if (ncbiID) content.push(`NCBI ID: <strong>${ncbiID}</strong>`);
        if (family) content.push(`Family name: <strong>${family}</strong>`);
        resultsQuery.innerHTML = content.join('<br>');
      }

      // total records for the query
      const resultsCount = document.getElementById('results-count');
      if (resultsCount) {
        resultsCount.innerHTML = `Total records: <strong>${data.count}</strong>`;
      }
      console.log(data)
      //downloa button
      const downloadContainer = document.getElementById('download-container');
      if (downloadContainer) {
        downloadContainer.innerHTML = "";
        
        // Only create button if the results card is visible (or data.results exists)
        const btn = document.createElement('button');
        btn.className = 'btn';
        btn.textContent = 'Download';
        
        // Store all possible query params as data attributes
        btn.dataset.organism = currentOrganismOverride || (organismField?.value || "");
        btn.dataset.family = currentFamilyOverride || "";
        btn.dataset.annotation = annotation || "";
        btn.dataset.ncbi = ncbiID || "";
        
        downloadContainer.appendChild(btn);
      }

      ///i will branch the rendering of the table based on sequence or family
      if (data.results && data.results.length > 0) {
        
        if (data.level === 'family'){
          thead.innerHTML = `
            <tr>
              <th>Organism Name</th>
              <th>Number of Promoters</th>
              <th>Actions</th>
            <tr>
          `;
          tbody.innerHTML = data.results.map(item => `
            <tr>
              <td>${item.organism_name}</td>
              <td>${item.sequence_count}</td>
              <td>
                <i class="fa-solid fa-eye view-icon" data-organism-id="${item.id}"></i>
              </td>
            </tr>
          `).join('')
        }
        else{
        console.log(params.toString());

        // Update table header for query results
        thead.innerHTML = `
          <tr>
            <th>NCBI ID</th>
            <th>Organism Name</th>
            <th>Sequence</th>
            <th>Annotation</th>
          </tr>
        `;

        // Fill table body with truncation
        tbody.innerHTML = data.results.map(item => {
          const annotation = item.annotation || '';
          const maxLength = 50;

          if (annotation.length > maxLength) {
            const shortAnnotation = annotation.slice(0, maxLength) + "...";
            return `
              <tr>
                <td>${item.ncbi_id}</td>
                <td>${item.organism_name}</td>
                <td>${item.sequence}</td>
                <td class="annotation-cell" data-full="${annotation}">
                  ${shortAnnotation} <span class="expand-btn" style="color:blue; cursor:pointer;">[expand]</span>
                </td>
              </tr>
            `;
          } else {
            return `
              <tr>
                <td>${item.ncbi_id}</td>
                <td>${item.organism_name}</td>
                <td>${item.sequence}</td>
                <td>${annotation}</td>
              </tr>
            `;
          }
        }).join('');
        tbody.querySelectorAll('.annotation-cell').forEach(cell => {
          const btn = cell.querySelector('.expand-btn');
          if (!btn) return;
        
          // store the original short text
          const fullText = cell.dataset.full;
          const maxLength = 50;
          const shortText = fullText.slice(0, maxLength) + "...";
        
          // initial state
          cell.dataset.expanded = "false";
        
          btn.addEventListener('click', () => {
            const expanded = cell.dataset.expanded === "true";
            if (!expanded) {
              cell.firstChild.textContent = fullText + " "; // set full text
              btn.textContent = "[collapse]";
              cell.dataset.expanded = "true";
            } else {
              cell.firstChild.textContent = shortText + " "; // set truncated text
              btn.textContent = "[expand]";
              cell.dataset.expanded = "false";
            }
          });
        });
        }
        
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
    

