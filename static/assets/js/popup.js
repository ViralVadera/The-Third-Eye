window.onload = function() {
    const modal = document.getElementById("myModal");
    const span = document.getElementsByClassName("close")[0];
    const messageText = document.getElementById("messageText");

    const urlParams = new URLSearchParams(window.location.search);
    const message = urlParams.get('message');
    if (message) {
        messageText.textContent = message;
        modal.style.display = "block";
        window.history.pushState({path: window.location.pathname}, '', window.location.pathname);
    }

    // When the user clicks on <span> (x), close the modal
    span.onclick = function() {
        modal.style.display = "none";
    }

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    }
};

document.getElementById('clearNotificationButton').addEventListener('click', async () => {
    try {
        const response = await fetch('/clearnoti/123', { method: 'GET' });
        const data = await response.json();
        const notificationResultDiv = document.getElementById('notificationResult');
        notificationResultDiv.textContent = data.query_string;
    } catch (error) {
        console.error('Error:', error);
    }
});
