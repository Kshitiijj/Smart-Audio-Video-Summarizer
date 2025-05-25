document.getElementById('uploadForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const formData = new FormData();
    const fileInput = document.getElementById('audioFile');
    const youtubeLink = document.getElementById('youtubeLink').value;

    if (fileInput.files.length === 0 && youtubeLink === '') {
        alert("Please select a file or enter a YouTube link.");
        return;
    }

    if (fileInput.files.length > 0) {
        formData.append('audioFile', fileInput.files[0]);
    } else {
        formData.append('youtubeLink', youtubeLink);
    }

    // Show loading indicator
    const loadingIndicator = document.getElementById('loading');
    loadingIndicator.style.display = 'block';

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            document.getElementById('transcribedText').innerText = data.transcribedText;
            document.getElementById('summary').innerText = data.summary;
            document.getElementById('keywords').innerText = data.keywords;
            document.getElementById('downloadPdf').style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error:', error);
    })
    .finally(() => {
        // Hide loading indicator
        loadingIndicator.style.display = 'none';
    });
});

document.getElementById('downloadPdf').addEventListener('click', function() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    const transcribedText = document.getElementById('transcribedText').innerText;
    const summary = document.getElementById('summary').innerText;
    const keywords = document.getElementById('keywords').innerText;

    // Add transcribed text
    doc.autoTable({
        head: [['Transcribed Text']],
        body: [[transcribedText]],
        startY: 10,
        theme: 'striped',
        styles: { fontSize: 10, cellWidth: 'wrap' }
    });

    // Add summary
    doc.autoTable({
        head: [['Summary']],
        body: [[summary]],
        startY: doc.lastAutoTable.finalY + 10,
        theme: 'striped',
        styles: { fontSize: 10, cellWidth: 'wrap' }
    });

    // Add keywords
    doc.autoTable({
        head: [['Keywords']],
        body: [[keywords]],
        startY: doc.lastAutoTable.finalY + 10,
        theme: 'striped',
        styles: { fontSize: 10, cellWidth: 'wrap' }
    });

    doc.save('output.pdf');
});