import os

with open('dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add script to make it interactive with FastAPI
script = '''
<script>
document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.querySelector('.border-dashed');
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.txt,.pdf,.docx';
    fileInput.style.display = 'none';
    document.body.appendChild(fileInput);

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#00236f';
        dropZone.style.backgroundColor = 'rgba(0, 35, 111, 0.05)';
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = '';
        dropZone.style.backgroundColor = '';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '';
        dropZone.style.backgroundColor = '';
        if (e.dataTransfer.files.length) {
            handleUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleUpload(e.target.files[0]);
        }
    });

    async function handleUpload(file) {
        dropZone.innerHTML = '<div class="flex flex-col items-center justify-center h-full w-full"><div class="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div><h3 class="font-h3 text-h3 text-primary mb-xs">Analyzing ' + file.name + '...</h3><p class="text-on-surface-variant">Please wait, extracting semantics and checking stylometry.</p></div>';
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/v1/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (res.ok) {
                pollStatus(data.job_id);
            } else {
                throw new Error(data.detail || 'Upload failed');
            }
        } catch (err) {
            alert('Upload failed: ' + err);
            dropZone.innerHTML = '<h3 class="font-h3 text-h3 text-error mb-xs">Upload Failed</h3>';
        }
    }

    async function pollStatus(jobId) {
        const interval = setInterval(async () => {
            try {
                const res = await fetch('/api/v1/status/' + jobId);
                const data = await res.json();
                
                if (data.status === 'done') {
                    clearInterval(interval);
                    fetchReport(jobId);
                } else if (data.status === 'error') {
                    clearInterval(interval);
                    dropZone.innerHTML = '<h3 class="font-h3 text-h3 text-error mb-xs">Analysis Error</h3><p>' + data.error_msg + '</p>';
                }
            } catch(e) {
                console.error('Polling error', e);
            }
        }, 1000);
    }

    async function fetchReport(jobId) {
        const res = await fetch('/api/v1/report/' + jobId);
        const report = await res.json();
        
        const sum = report.summary;
        const color = sum.authenticity_score >= 80 ? '#006c49' : sum.authenticity_score >= 50 ? '#ef9900' : '#ba1a1a';
        
        dropZone.innerHTML = `
            <div class="flex flex-col items-center justify-center w-full h-full p-lg">
                <h2 class="font-h2 text-h2 text-primary mb-lg">Analysis Complete</h2>
                <div class="flex gap-xl mb-lg">
                    <div class="text-center glass-card">
                        <p class="text-[64px] font-bold" style="color:${color}">${sum.authenticity_score.toFixed(1)}%</p>
                        <p class="text-label-md text-outline uppercase tracking-widest">Overall Authenticity</p>
                    </div>
                </div>
                <div class="grid grid-cols-3 gap-md w-full max-w-3xl">
                    <div class="text-center glass-card p-md">
                        <p class="text-[32px] font-bold text-error">${sum.plagiarism_score.toFixed(1)}%</p>
                        <p class="text-label-md text-outline">Plagiarism Risk</p>
                    </div>
                    <div class="text-center glass-card p-md">
                        <p class="text-[32px] font-bold text-primary-container">${sum.ai_probability.toFixed(1)}%</p>
                        <p class="text-label-md text-outline">AI Probability</p>
                    </div>
                    <div class="text-center glass-card p-md">
                        <p class="text-[32px] font-bold text-secondary">${sum.authorship_consistency.toFixed(1)}%</p>
                        <p class="text-label-md text-outline">Style Consistency</p>
                    </div>
                </div>
                <p class="mt-xl text-[18px] font-bold" style="color:${color}">${sum.interpretation}</p>
                <button onclick="location.reload()" class="mt-xl bg-primary text-white font-bold px-xl py-sm rounded-xl hover:bg-primary-container transition-colors shadow-lg">Analyze Another Document</button>
            </div>
        `;
        dropZone.style.minHeight = '500px';
        dropZone.classList.remove('border-dashed', 'cursor-pointer', 'hover:border-primary/40');
        dropZone.classList.add('border-solid');
    }
});
</script>
'''

html = html.replace('</body>', script + '</body>')

os.makedirs('templates', exist_ok=True)
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
