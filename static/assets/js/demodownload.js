 // download example
 document.getElementById('download-btn').addEventListener('click', function() {
    // Get the table
    var table = document.getElementById('myTable');
    // Initialize empty CSV string
    var csv = '';
  
    // Loop through rows
    for (var i = 0; i < table.rows.length; i++) {
      var row = table.rows[i];
      // Loop through cells
      for (var j = 0; j < row.cells.length; j++) {
        // Append cell value to CSV string
        csv += '"' + row.cells[j].innerText.trim().replace(/"/g, '""') + '"';
        // Add comma except for the last cell
        if (j < row.cells.length - 1) {
          csv += ',';
        }
      }
      // Add newline character except for the last row
      if (i < table.rows.length - 1) {
        csv += '\n';
      }
    }
  
    // Create a hidden link element
    var link = document.createElement('a');
    link.style.display = 'none';
    document.body.appendChild(link);
  
    // Set the CSV data to the link's href attribute
    link.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv));
    link.setAttribute('download', 'Demo.csv');
  
    // Trigger click event to start download
    link.click();
  });
