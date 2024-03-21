
const dragDropArea = document.getElementById('dragDropArea');
const fileNameElement = document.getElementById('fileName');
const deleteButton = document.getElementById('deleteButton');
const browseLabel = document.getElementById('browseLabel');

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dragDropArea.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    dragDropArea.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dragDropArea.addEventListener(eventName, unhighlight, false);
});

function highlight(e) {
    dragDropArea.classList.add('highlight');
}

function unhighlight(e) {
    dragDropArea.classList.remove('highlight');
}

dragDropArea.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
    displayFileName(files[0].name); // Display the file name
    deleteButton.style.display = 'inline-block'; // Show delete button
}

function handleFiles(files) {
    // Handle uploaded files here
    console.log(files);
}

function displayFileName(fileName) {
    fileNameElement.textContent = fileName;
}

deleteButton.addEventListener('click', deleteFile);

function deleteFile() {
    const fileInput = document.getElementById('file-upload');
    fileInput.value = ''; // Clear the file input
    fileNameElement.textContent = ''; // Clear the displayed file name
    deleteButton.style.display = 'none'; // Hide the delete button
}
// delete button upload through browse button
function displayFileName(fileName) {
    document.getElementById('fileName').textContent = fileName;
    document.getElementById('deleteButton').style.display = 'inline-block';
}

document.getElementById('deleteButton').addEventListener('click', function() {
    var fileInput = document.getElementById('file-upload');
    fileInput.value = ''; // Clear the file input
    document.getElementById('fileName').textContent = ''; // Clear the displayed file name
    document.getElementById('deleteButton').style.display = 'none'; // Hide the delete button
});