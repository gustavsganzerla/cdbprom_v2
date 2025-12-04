

document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("download-container");

    container.addEventListener("click", (e) => {
        if (e.target && e.target.classList.contains("btn")) {
            //organism from button dataset
            const organism = e.target.dataset.organism?.trim() || "";

            //ther filters from form inputs if present
            const annotation = document.getElementById("annotation")?.value.trim();
            const ncbiId     = document.getElementById("ncbi")?.value.trim();

            if (!organism && !annotation && !ncbiId) {
                console.warn("No filters provided for download, aborting.");
                return;
            }

            const params = new URLSearchParams();
            if (organism) params.append("organism_name", organism);
            if (annotation) params.append("annotation", annotation);
            if (ncbiId) params.append("ncbi_id", ncbiId);

            fetch(`/api/download/?${params}`)
                .then(response => {
                    if (!response.ok) throw new Error("Network response was not ok");
                    return response.blob();
                })
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;


                    let fileName = "promoters";
                    if (organism) fileName += `_${organism}`;
                    if (annotation) fileName += `_annot_${annotation}`;
                    if (ncbiId) fileName += `_ncbi_${ncbiId}`;
                    fileName += ".csv";

                    a.download = fileName;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                })
                .catch(err => console.error("Fetch error:", err));
        }
    });
});