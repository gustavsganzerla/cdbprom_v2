document.getElementById("new-form").addEventListener("submit", async function(e) {
    e.preventDefault();

    const sequenceText = document.getElementById("id_sequence_text").value;
    const uploadedFile = document.getElementById("id_uploaded_file");

    let fastaContent = sequenceText;

    //if a file is uploaded, read it
    if (uploadedFile.files.length > 0){
        const file = uploadedFile.files[0];
        fastaContent = await file.text(); //here we override the text area if a file exists, and send it for parsing
    }
    const sequences = parseFasta(fastaContent);

    console.log("Sending to Flask API:", sequences);
    console.log(CONFIG.API_URL);

    try {
        const response = await fetch(CONFIG.API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sequences })
        });

        // Ensure response exists
        if (!response) {
            console.error("No response from Flask API");
            return;
        }

        // Check HTTP status first
        if (!response.ok) {
            console.error("HTTP error", response.status, response.statusText);
            // Try to get text safely
            const text = await response.text().catch(() => "<no response text>");
            console.error("Server response:", text);
            return;
        }

        // At this point, we expect JSON
        const data = await response.json().catch(() => null);

        if (data && data.output && data.output.length > 0) {
            console.log("Flask API response:", data);

            //download 
            const downloadContainer = document.getElementById('download-container');
            downloadContainer.innerHTML = "";

            const btn = document.createElement('button');
            btn.className = 'btn';
            btn.textContent = 'Download';

            btn.addEventListener('click', () => downloadPrediction(data.output));

            downloadContainer.appendChild(btn);

            
            // Build table
            const columnOrder = ["id", "Predicted class", "Probability promoter", "Probability non-promoter", "Coordinates", "Sequence", "Message"]
            buildTable("results-container", data.output, columnOrder);
            // Show results block
            document.getElementById("results-container").style.display = "block";

            
            
        } else {
            console.error("No results or failed to parse JSON response");
            
            // Hide results block if no data
            document.getElementById("results-container").style.display = "none";
        }

    } catch (error) {
        console.error("Error sending data to Flask API:", error);
    }
});


//FASTA parser
function parseFasta(fastaText) {
    const lines = fastaText.split("\n");
    const result = [];
    let currentSeq = null;

    for (let line of lines) {
        line = line.trim();
        if (line.length === 0) continue; // skip empty lines

        if (line.startsWith(">")) {
            // New sequence header
            if (currentSeq) {
                result.push(currentSeq);
            }
            currentSeq = { id: line.substring(1).trim(), seq: "" };
        } else if (currentSeq) {
            // Sequence line
            currentSeq.seq += line;
        }
    }

    // Push the last sequence
    if (currentSeq) result.push(currentSeq);

    return result;
}


//build table to show results
function buildTable(containerId, dataArray, columnOrder) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    if (!dataArray || dataArray.length === 0) {
        container.innerHTML = "<p>No results</p>";
        return;
    }

    const table = document.createElement("table");
    table.id = "results-table"; 

    const keys = columnOrder || Object.keys(dataArray[0]);

    

    // Create header
    const header = table.createTHead();
    const headerRow = header.insertRow(0);
    keys.forEach(key => {
        const th = document.createElement("th");
        th.innerText = key;
        headerRow.appendChild(th);
    });

    // Create body
    const tbody = table.createTBody();
    dataArray.forEach(rowData => {
        const row = tbody.insertRow();
        keys.forEach(key => {
            const cell = row.insertCell();
            cell.innerText = rowData[key];
        });
    });

    container.appendChild(table);
}


async function downloadPrediction(data){
    const response = await fetch("/api/downloadPredict", {
        method: "POST",
        headers: {
            "Content-Type":"application/json"
        },
        body: JSON.stringify({data})

    });
    
    //create a blob JS variable (binary large object) from the response that came from the API
    //in blob, i have all the data
    const blob = await response.blob();

    //creates a temporary url that points to the blob data (like a virtual file in the browser)
    const url = window.URL.createObjectURL(blob);

    //creates a <a> element
    const a = document.createElement("a");

    //links the <a> to the blob
    a.href = url;

    //download function to download the a anchor (that contains the blob)
    a.download = "results_prediction.csv";
    a.click();

    //cleanup
    a.remove();
}