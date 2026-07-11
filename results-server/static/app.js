let allFiles = [];
let currentFilter = 'all';
let lastRenderedHash = '';
let currentWatchFile = null;

const videoExts = ['mp4', 'webm', 'mkv', 'avi', 'mov', 'flv', 'wmv'];
const audioExts = ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'wma'];
const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'];

function getExt(name) {
    return (name.split('.').pop() || '').toLowerCase();
}

function getType(name) {
    const ext = getExt(name);
    if (videoExts.includes(ext)) return 'video';
    if (audioExts.includes(ext)) return 'audio';
    if (imageExts.includes(ext)) return 'image';
    return 'other';
}

function getIcon(type) {
    switch (type) {
        case 'video': return '🎬';
        case 'audio': return '🎵';
        case 'image': return '🖼️';
        default: return '📄';
    }
}

function formatSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('id-ID', {
        day: 'numeric', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

async function fetchFiles() {
    if (allFiles.length === 0) document.getElementById('loading').style.display = 'block';
    document.getElementById('emptyState').style.display = 'none';

    try {
        const resp = await fetch('/results/api/files');
        if (!resp.ok) throw new Error('API error');
        allFiles = await resp.json();
    } catch (e) {
        allFiles = [];
    }

    document.getElementById('loading').style.display = 'none';
    updateStats();
    filterFiles();
}

function updateStats() {
    document.getElementById('totalFiles').textContent = allFiles.length;
    const total = allFiles.reduce((s, f) => s + (f.size || 0), 0);
    document.getElementById('totalSize').textContent = formatSize(total);
}

function filterFiles() {
    const search = document.getElementById('searchInput').value.toLowerCase();
    const sort = document.getElementById('sortSelect').value;

    let filtered = allFiles.filter(f => {
        const type = getType(f.name);
        const matchFilter = currentFilter === 'all' || type === currentFilter;
        const matchSearch = f.name.toLowerCase().includes(search);
        return matchFilter && matchSearch;
    });

    filtered.sort((a, b) => {
        switch (sort) {
            case 'newest': return new Date(b.modified) - new Date(a.modified);
            case 'oldest': return new Date(a.modified) - new Date(b.modified);
            case 'name': return a.name.localeCompare(b.name);
            case 'size': return (b.size || 0) - (a.size || 0);
        }
    });

    renderFiles(filtered);
}

function setFilter(filter) {
    currentFilter = filter;
    filterFiles();
}

function handleSearchKey(event) {
    if (event.key === 'Enter') filterFiles();
}

function renderFiles(files) {
    const grid = document.getElementById('fileGrid');
    const empty = document.getElementById('emptyState');

    if (files.length === 0) {
        grid.innerHTML = '';
        empty.style.display = 'block';
        return;
    }

    empty.style.display = 'none';
    const hash = files.map(f => f.name + f.size + f.modified).join('');
    if (hash === lastRenderedHash) return;
    lastRenderedHash = hash;
    grid.innerHTML = files.map(f => {
        const type = getType(f.name);
        const ext = getExt(f.name);
        let preview = '';

        if (type === 'video') {
            const thumb = encodeURIComponent(f.name.replace(/\.mp4$/, '.jpg'));
            preview = `<img src="/results/thumbs/${thumb}" onerror="this.onerror=null; this.src='/results/files/${encodeURIComponent(f.name)}#t=0.1'; this.outerHTML='<video src=\''+this.src+'\' preload=\'metadata\' muted></video>';" alt="${f.name}" loading="lazy">`;
        } else if (type === 'image') {
            preview = `<img src="/results/files/${encodeURIComponent(f.name)}" alt="${f.name}" loading="lazy">`;
        } else if (type === 'audio') {
            preview = `<div class="file-icon">🎵</div>`;
        } else {
            preview = `<div class="file-icon">${getIcon(type)}</div>`;
        }

        return `
                <div class="file-card" onclick="handleFileOpen('${encodeURIComponent(f.name)}', '${type}', '${formatSize(f.size)}', '${formatDate(f.modified)}')">
                    <div class="file-preview">${preview}</div>
                    <div class="file-info">
                        <div class="file-name" title="${f.name}">${f.name}</div>
                        <div class="file-meta">
                            <span class="file-type type-${type}">${ext}</span>
                            <span>${formatSize(f.size)}</span>
                        </div>
                    </div>
                </div>
            `;
    }).join('');
}

function handleFileOpen(encodedName, type, size, date) {
    if (type === 'video') {
        openWatch(encodedName);
        return;
    }
    openPreview(encodedName, type, size, date);
}

function openPreview(encodedName, type, size, date) {
    const name = decodeURIComponent(encodedName);
    const url = `/results/files/${encodedName}`;

    document.getElementById('modalTitle').textContent = name;
    document.getElementById('modalMeta').textContent = `${size} • ${date}`;
    document.getElementById('modalDownload').href = url;
    document.getElementById('modalDownload').download = name;

    const body = document.getElementById('modalBody');

    if (type === 'video') {
        body.innerHTML = `<video src="${url}" controls autoplay style="max-width:100%;max-height:70vh;border-radius:8px;"></video>`;
    } else if (type === 'audio') {
        body.innerHTML = `<div style="text-align:center"><div style="font-size:5rem;margin-bottom:1rem;">🎵</div><audio src="${url}" controls autoplay style="width:100%;max-width:500px;"></audio></div>`;
    } else if (type === 'image') {
        body.innerHTML = `<img src="${url}" style="max-width:100%;max-height:70vh;border-radius:8px;">`;
    } else {
        body.innerHTML = `<div style="text-align:center"><div style="font-size:5rem;margin-bottom:1rem;">📄</div><p style="color:#a1a1aa;">${name}</p></div>`;
    }

    document.getElementById('modal').classList.add('active');
    document.addEventListener('keydown', escHandler);
}

function closeModal(e) {
    if (e && e.target && !e.target.classList.contains('modal-overlay')) return;
    document.getElementById('modal').classList.remove('active');
    document.getElementById('modalBody').innerHTML = '';
    document.removeEventListener('keydown', escHandler);
}

function escHandler(e) { if (e.key === 'Escape') closeModal(); }

async function refreshFiles() {
    const btn = document.getElementById('refreshBtn');
    btn.classList.add('spinning');
    await fetchFiles();
    setTimeout(() => btn.classList.remove('spinning'), 500);
}



const stageLabels = {
    '1_download': 'Download Video',
    '2_transcribe': 'Transcribe Audio',
    '3_director_analysis': 'Director Analysis',
    '4_cut_video': 'Cut Video',
    '5_add_caption': 'Add Caption'
};

function switchTab(tab) {
    document.getElementById('filesPanel').classList.toggle('active', tab === 'files');
    document.getElementById('progressPanel').classList.toggle('active', tab === 'progress');
    document.getElementById('historyPanel').classList.toggle('active', tab === 'history');
    document.getElementById('watchPanel').classList.toggle('active', tab === 'watch');

    document.getElementById('tabFilesBtn').classList.toggle('active', tab === 'files');
    document.getElementById('tabProgressBtn').classList.toggle('active', tab === 'progress');
    document.getElementById('tabHistoryBtn').classList.toggle('active', tab === 'history');

    if (tab === 'progress') fetchState();
    if (tab === 'history') fetchHistory();
}

function statusClass(status) {
    return `status-${(status || 'pending').replace(/[^a-zA-Z0-9_]/g, '_')}`;
}

function fmtTime(seconds) {
    if (seconds === undefined || seconds === null || seconds === '') return '-';
    const s = Math.floor(Number(seconds));
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    return h ? `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}` : `${m}:${String(sec).padStart(2, '0')}`;
}

async function fetchState() {
    const loading = document.getElementById('progressLoading');
    const content = document.getElementById('progressContent');
    loading.style.display = 'block';
    try {
        const resp = await fetch('/results/api/state');
        const state = resp.ok ? await resp.json() : {};
        renderState(state);
    } catch (e) {
        content.innerHTML = `<div class="empty-state"><div class="icon">⚠️</div><h2>Gagal memuat state</h2><p>${e.message}</p></div>`;
    } finally {
        loading.style.display = 'none';
    }
}

function renderState(state) {
    const content = document.getElementById('progressContent');
    if (!state || Object.keys(state).length === 0) {
        content.innerHTML = `<div class="empty-state"><div class="icon">📭</div><h2>Belum ada progress</h2><p>File state.json belum tersedia.</p></div>`;
        return;
    }
    const stages = state.stages || {};
    const keys = Object.keys(stages).sort();
    const completed = keys.filter(k => stages[k].status === 'completed').length;
    const percent = keys.length ? Math.round((completed / keys.length) * 100) : 0;
    const finalStage = stages['3_director_analysis'] || {};
    const stageCards = keys.map(k => {
        const s = stages[k] || {};
        const extra = [];
        if (s.method) extra.push(`<strong>Method:</strong> ${s.method}`);
        if (s.provider) extra.push(`<strong>Provider:</strong> ${s.provider}`);
        if (s.start !== undefined || s.end !== undefined) extra.push(`<strong>Clip:</strong> ${fmtTime(s.start)} - ${fmtTime(s.end)}`);
        if (s.title) extra.push(`<strong>Title:</strong> ${s.title}`);
        if (s.reason) extra.push(`<strong>Reason:</strong> ${s.reason}`);
        return `<div class="stage-card">
                <div class="stage-head">
                    <div class="stage-name">${stageLabels[k] || k}</div>
                    <span class="status-pill ${statusClass(s.status)}">${s.status || 'pending'}</span>
                </div>
                <div class="stage-details">${extra.length ? extra.join('<br>') : 'Tidak ada detail tambahan.'}</div>
            </div>`;
    }).join('');
    const paths = state.paths || {};
    const pathRows = Object.entries(paths).map(([k, v]) => `<div><strong>${k}:</strong> ${v}</div>`).join('');
    content.innerHTML = `<div class="progress-summary">
            <div class="progress-summary-top">
                <div>
                    <div class="progress-title">${finalStage.title || 'Clipper Stage Progress'}</div>
                    <div class="progress-url">${state.url || '-'}</div>
                </div>
                <span class="status-pill ${statusClass(state.global_status)}">${state.global_status || 'unknown'} • ${percent}%</span>
            </div>
            <div class="progress-bar"><div class="progress-fill" style="width:${percent}%"></div></div>
            ${pathRows ? `<div class="path-list">${pathRows}</div>` : ''}
        </div>
        <div class="stage-list">${stageCards}</div>`;
}


async function fetchHistory() {
    const loading = document.getElementById('historyLoading');
    const content = document.getElementById('historyContent');
    loading.style.display = 'block';
    try {
        const resp = await fetch('/results/api/history');
        const data = resp.ok ? await resp.json() : {};
        renderHistory(data);
    } catch (e) {
        content.innerHTML = `<div class="empty-state"><div class="icon">⚠️</div><h2>Gagal memuat history</h2><p>${e.message}</p></div>`;
    } finally {
        loading.style.display = 'none';
    }
}

function renderHistory(data) {
    const content = document.getElementById('historyContent');

    // Data sekarang berupa array of objects
    if (!data || !Array.isArray(data) || data.length === 0) {
        content.innerHTML = `<div class="empty-state"><div class="icon">📭</div><h2>Belum ada history</h2><p>Data clip history belum tersedia.</p></div>`;
        return;
    }

    let html = '<div class="history-list">';

    data.forEach(item => {
        const videoTitle = item.video_title || '';
        const videoUrl = item.video_url || '';
        const clips = Array.isArray(item.clip_data) ? item.clip_data : [];

        if (clips.length === 0) return;

        const cards = clips.map((c, i) => `
                <div class="history-item">
                    <div class="history-item-title">Clip ${i + 1}: ${c.title || 'Tanpa Judul'}</div>
                    <div class="history-item-meta"><span>⏱️ ${fmtTime(c.start)} - ${fmtTime(c.end)}</span></div>
                    <div class="history-item-reason">${c.reason || ''}</div>
                </div>`).join('');

        html += `
                <div class="history-group">
                    <div class="history-group-header" onclick="this.parentElement.classList.toggle('collapsed')">
                        <span class="collapse-icon">▼</span>
                        <span class="yt-icon">▶</span>
                        <span class="history-group-url" onclick="event.stopPropagation()">${videoTitle ? `<strong>${videoTitle}</strong> — ` : ''}<a href="${videoUrl}" target="_blank">${videoUrl || 'URL tidak tersedia'}</a></span>
                        ${videoUrl ? `<button class="action-btn" onclick="event.stopPropagation(); triggerReclip('${videoUrl}', this)">✂️ Buat Clip Baru</button>` : ''}
                    </div>
                    <div class="history-group-content">
                        ${cards}
                    </div>
                </div>`;
    });

    html += '</div>';

    if (html === '<div class="history-list"></div>') {
        content.innerHTML = `<div class="empty-state"><div class="icon">📭</div><h2>Belum ada history</h2><p>Data clip history belum tersedia.</p></div>`;
    } else {
        content.innerHTML = html;
    }
}


async function triggerReclip(url, btnElement) {
    btnElement.disabled = true;
    const originalText = btnElement.innerHTML;
    btnElement.innerHTML = '⏳ Memproses...';

    try {
        const resp = await fetch('/results/api/reclip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        if (resp.ok) {
            btnElement.innerHTML = '✅ Berhasil Diminta';
            btnElement.style.color = '#22c55e';
            btnElement.style.borderColor = 'rgba(34, 197, 94, 0.3)';
            btnElement.style.background = 'rgba(34, 197, 94, 0.1)';
        } else {
            throw new Error('Gagal');
        }
    } catch (e) {
        alert('Gagal membuat request clip baru: ' + e.message);
        btnElement.innerHTML = originalText;
        btnElement.disabled = false;
    }

    setTimeout(() => {
        if (btnElement.innerHTML === '✅ Berhasil Diminta') {
            btnElement.innerHTML = originalText;
            btnElement.disabled = false;
            btnElement.style = '';
        }
    }, 5000);
}


function getVideoFiles() {
    return allFiles.filter(f => getType(f.name) === 'video');
}

function getFileByEncodedName(encodedName) {
    const name = decodeURIComponent(encodedName);
    return allFiles.find(f => f.name === name);
}

function thumbUrlFor(name) {
    return `/results/thumbs/${encodeURIComponent(name.replace(/\.mp4$/i, '.jpg'))}`;
}

function openWatch(encodedName) {
    window.location.hash = `watch=${encodedName}`;
    showWatch(encodedName);
}

function showWatch(encodedName) {
    const file = getFileByEncodedName(encodedName);
    if (!file) return;

    currentWatchFile = file.name;
    switchTab('watch');

    const url = `/results/files/${encodeURIComponent(file.name)}`;
    const player = document.getElementById('watchPlayer');
    if (player.getAttribute('src') !== url) {
        player.src = url;
        player.load();
        player.play().catch(() => { });
    }

    document.getElementById('watchTitle').textContent = file.name;
    document.getElementById('watchMeta').textContent = `${formatSize(file.size || 0)} • ${formatDate(file.modified)}`;
    const download = document.getElementById('watchDownload');
    download.href = url;
    download.download = file.name;
    renderWatchPlaylist(file.name);
}

function renderWatchPlaylist(activeName) {
    const list = document.getElementById('watchPlaylist');
    const query = (document.getElementById('watchSearchInput')?.value || '').toLowerCase().trim();
    const videos = getVideoFiles()
        .filter(f => !query || f.name.toLowerCase().includes(query))
        .sort((a, b) => new Date(b.modified) - new Date(a.modified));
    if (videos.length === 0) {
        list.innerHTML = `<div class="watch-empty">${query ? 'Tidak ada video yang cocok.' : 'Belum ada video.'}</div>`;
        return;
    }
    list.innerHTML = videos.map(f => {
        const encoded = encodeURIComponent(f.name);
        return `<div class="watch-item ${f.name === activeName ? 'active' : ''}" onclick="openWatch('${encoded}')">
            <div class="watch-thumb"><img src="${thumbUrlFor(f.name)}" onerror="this.onerror=null;this.parentElement.innerHTML='🎬';" alt="${f.name}"></div>
            <div>
                <div class="watch-item-title" title="${f.name}">${f.name}</div>
                <div class="watch-item-meta">${formatSize(f.size || 0)} • ${formatDate(f.modified)}</div>
            </div>
        </div>`;
    }).join('');
}

function backToResults() {
    history.pushState('', document.title, window.location.pathname + window.location.search);
    currentWatchFile = null;
    const player = document.getElementById('watchPlayer');
    player.pause();
    player.removeAttribute('src');
    player.load();
    switchTab('files');
}

async function copyWatchLink() {
    if (!currentWatchFile) return;
    const url = `${window.location.origin}${window.location.pathname}#watch=${encodeURIComponent(currentWatchFile)}`;
    try {
        await navigator.clipboard.writeText(url);
        alert('Link video sudah dicopy.');
    } catch (e) {
        prompt('Copy link ini:', url);
    }
}

function handleHashRoute() {
    const hash = window.location.hash || '';
    if (!hash.startsWith('#watch=')) return;
    const encodedName = hash.slice('#watch='.length);
    if (allFiles.length === 0) return;
    showWatch(encodedName);
}

// Init
fetchFiles().then(handleHashRoute);
// Auto refresh every 30 seconds
// setInterval(fetchFiles, 30000);
// setInterval(() => { if (document.getElementById('progressPanel').classList.contains('active')) fetchState();
//     if (document.getElementById('historyPanel').classList.contains('active')) fetchHistory(); }, 10000);

window.addEventListener('hashchange', handleHashRoute);
