// Backend API Gateway Configuration
// Auto-detects local vs Cloudflare Pages deployment
const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.hostname === '')
    ? ''
    : 'https://entries-thriller-despite-upload.trycloudflare.com';

// SoundWave â€” Spotify Premium Audio Engine
// Background Playback, MediaSession Lockscreen Control, YouTube Streams, Full Library & Tabs

document.addEventListener('DOMContentLoaded', () => {
    // --- 1. DOM REFERENCES ---
    // Tab Navigation
    const tabHome = document.getElementById('tabHome');
    const tabSearch = document.getElementById('tabSearch');
    const tabVideo = document.getElementById('tabVideo');
    const tabMovies = document.getElementById('tabMovies');
    const tabLibrary = document.getElementById('tabLibrary');
    const tabPremium = document.getElementById('tabPremium');
    const viewportScroll = document.getElementById('viewportScroll');

    const sideNavHome = document.getElementById('sideNavHome');
    const sideNavSearch = document.getElementById('sideNavSearch');
    const sideNavVideo = document.getElementById('sideNavVideo');
    const sideNavMovies = document.getElementById('sideNavMovies');
    const sideNavLibrary = document.getElementById('sideNavLibrary');
    const sideNavPremium = document.getElementById('sideNavPremium');
    const sideLikedBtn = document.getElementById('sideLikedBtn');

    const mobTabHome = document.getElementById('mobTabHome');
    const mobTabSearch = document.getElementById('mobTabSearch');
    const mobTabVideo = document.getElementById('mobTabVideo');
    const mobTabMovies = document.getElementById('mobTabMovies');
    const mobTabLibrary = document.getElementById('mobTabLibrary');
    const mobTabPremium = document.getElementById('mobTabPremium');

    const btnPlayerWatchVideo = document.getElementById('btnPlayerWatchVideo');
    const btnModalWatchVideo = document.getElementById('btnModalWatchVideo');

    const btnTopPremium = document.getElementById('btnTopPremium');
    const btnUserProfile = document.getElementById('btnUserProfile');
    const userAvatarIcon = document.getElementById('userAvatarIcon');
    const userAvatarLabel = document.getElementById('userAvatarLabel');

    const btnHistoryBack = document.getElementById('btnHistoryBack');
    const btnHistoryForward = document.getElementById('btnHistoryForward');

    // Home View Elements
    const greetingMessage = document.getElementById('greetingMessage');
    const jumboQuickPlay = document.getElementById('jumboQuickPlay');
    const quickPicksContainer = document.getElementById('quickPicksContainer');
    const trendingShelfGrid = document.getElementById('trendingShelfGrid');
    const romanticShelfGrid = document.getElementById('romanticShelfGrid');
    const lofiShelfGrid = document.getElementById('lofiShelfGrid');

    // Search View Elements
    const globalSearchInput = document.getElementById('globalSearchInput');
    const globalClearBtn = document.getElementById('globalClearBtn');
    const searchPageViewInput = document.getElementById('searchPageViewInput');
    const btnExecuteSearch = document.getElementById('btnExecuteSearch');
    const searchLoadingState = document.getElementById('searchLoadingState');
    const searchResultsWrapper = document.getElementById('searchResultsWrapper');
    const searchResultsTitle = document.getElementById('searchResultsTitle');
    const searchResultsGrid = document.getElementById('searchResultsGrid');
    const categoryTilesGrid = document.getElementById('categoryTilesGrid');

    // Library View Elements
    const librarySongCount = document.getElementById('librarySongCount');
    const sideLikedBadge = document.getElementById('sideLikedBadge');
    const btnPlayLikedPlaylist = document.getElementById('btnPlayLikedPlaylist');
    const libraryTableBody = document.getElementById('libraryTableBody');

    // Player Bar Elements
    const audio = document.getElementById('audioPlaybackEngine');
    const playerCoverImg = document.getElementById('playerCoverImg');
    const playerSongTitle = document.getElementById('playerSongTitle');
    const playerSongArtist = document.getElementById('playerSongArtist');
    const btnHeartLike = document.getElementById('btnHeartLike');
    const svgHeartIcon = document.getElementById('svgHeartIcon');

    const btnShuffle = document.getElementById('btnShuffle');
    const btnPrev = document.getElementById('btnPrev');
    const btnPlayPause = document.getElementById('btnPlayPause');
    const svgPlay = document.getElementById('svgPlay');
    const svgPause = document.getElementById('svgPause');
    const btnNext = document.getElementById('btnNext');
    const btnLoop = document.getElementById('btnLoop');

    const timeCurrent = document.getElementById('timeCurrent');
    const timeTotal = document.getElementById('timeTotal');
    const scrubTrack = document.getElementById('scrubTrack');
    const scrubFill = document.getElementById('scrubFill');
    const scrubThumb = document.getElementById('scrubThumb');

    const btnToggleQueue = document.getElementById('btnToggleQueue');
    const btnVolumeMute = document.getElementById('btnVolumeMute');
    const svgVolHigh = document.getElementById('svgVolHigh');
    const svgVolMute = document.getElementById('svgVolMute');
    const volumeRange = document.getElementById('volumeRange');

    // Queue Drawer & Toast
    const queueDrawerPanel = document.getElementById('queueDrawerPanel');
    const btnCloseQueueDrawer = document.getElementById('btnCloseQueueDrawer');
    const queueDrawerList = document.getElementById('queueDrawerList');
    const spToastAlert = document.getElementById('spToastAlert');
    const toastAlertText = document.getElementById('toastAlertText');

    // Mobile Specific Elements
    const mobProgFill = document.getElementById('mobProgFill');
    const spBottomPlayer = document.getElementById('spBottomPlayer');
    const mobileNowPlayingModal = document.getElementById('mobileNowPlayingModal');
    const btnModalClose = document.getElementById('btnModalClose');
    const btnModalQueue = document.getElementById('btnModalQueue');
    const modalArtImg = document.getElementById('modalArtImg');
    const modalTrackTitle = document.getElementById('modalTrackTitle');
    const modalTrackArtist = document.getElementById('modalTrackArtist');
    const btnModalHeartLike = document.getElementById('btnModalHeartLike');
    const svgModalHeartIcon = document.getElementById('svgModalHeartIcon');

    const modalScrubTrack = document.getElementById('modalScrubTrack');
    const modalScrubFill = document.getElementById('modalScrubFill');
    const modalScrubThumb = document.getElementById('modalScrubThumb');
    const modalTimeCurrent = document.getElementById('modalTimeCurrent');
    const modalTimeTotal = document.getElementById('modalTimeTotal');

    const btnModalShuffle = document.getElementById('btnModalShuffle');
    const btnModalPrev = document.getElementById('btnModalPrev');
    const btnModalPlayPause = document.getElementById('btnModalPlayPause');
    const svgModalPlay = document.getElementById('svgModalPlay');
    const svgModalPause = document.getElementById('svgModalPause');
    const btnModalNext = document.getElementById('btnModalNext');
    const btnModalLoop = document.getElementById('btnModalLoop');

    // --- 2. APPLICATION STATE ---
    let activeQueue = [];
    let currentTrackIndex = -1;
    let isShuffle = false;
    let isLoop = false;
    let previousVolume = 0.9;
    let tabHistory = ['home'];
    let tabHistoryIndex = 0;
    let toastTimeout = null;

    // Liked Songs from localStorage
    const STORAGE_KEY_LIKED = 'soundwave_liked_songs_v2';
    let likedSongs = [];
    try {
        const stored = localStorage.getItem(STORAGE_KEY_LIKED);
        likedSongs = stored ? JSON.parse(stored) : [];
    } catch (e) {
        likedSongs = [];
    }

    // Default curated seeds for quick initial hydration
    const QUICK_PICKS_SEEDS = [
        { id: 'seeds_1', query: 'Kesariya Arijit Singh', title: 'Kesariya', channel: 'Arijit Singh, Pritam', thumbnail: 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300' },
        { id: 'seeds_2', query: 'Starboy The Weeknd', title: 'Starboy', channel: 'The Weeknd, Daft Punk', thumbnail: 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=300' },
        { id: 'seeds_3', query: 'Softly Karan Aujla', title: 'Softly', channel: 'Karan Aujla, Ikky', thumbnail: 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=300' },
        { id: 'seeds_4', query: 'Espresso Sabrina Carpenter', title: 'Espresso', channel: 'Sabrina Carpenter', thumbnail: 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=300' },
        { id: 'seeds_5', query: 'Apna Bana Le Arijit Singh', title: 'Apna Bana Le', channel: 'Arijit Singh, Sachin-Jigar', thumbnail: 'https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=300' },
        { id: 'seeds_6', query: 'Night Changes One Direction', title: 'Night Changes', channel: 'One Direction', thumbnail: 'https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=300' }
    ];

    // --- 3. INITIALIZATION ---
    updateGreeting();
    updateLikedUI();
    updateSubscriptionUI();
    renderQuickPicks();
    setupEventListeners();
    setupMediaSession();
    setupFirebaseAndAuthSuite();
    audio.volume = 0.9;

    // Load initial shelves asynchronously
    loadShelfData('Trending Songs Hindi Punjabi 2024', trendingShelfGrid);
    loadShelfData('Arijit Singh Best Romantic Songs', romanticShelfGrid);
    loadShelfData('Lo-Fi Relax Study Chill Beats', lofiShelfGrid);
    loadVegamoviesHomeShelf();

    // --- 4. GREETING HELPER ---
    function updateGreeting() {
        if (!greetingMessage) return;
        const hour = new Date().getHours();
        if (hour >= 4 && hour < 12) {
            greetingMessage.textContent = 'Good morning';
        } else if (hour >= 12 && hour < 17) {
            greetingMessage.textContent = 'Good afternoon';
        } else if (hour >= 17 && hour < 22) {
            greetingMessage.textContent = 'Good evening';
        } else {
            greetingMessage.textContent = 'Late night vibes';
        }
    }

    // --- 5. TAB NAVIGATION SYSTEM ---
    function switchTab(tabName, addToHistory = true) {
        const tabs = {
            home: { panel: tabHome, sideLink: sideNavHome, mobBtn: mobTabHome },
            search: { panel: tabSearch, sideLink: sideNavSearch, mobBtn: mobTabSearch },
            video: { panel: tabVideo, sideLink: sideNavVideo, mobBtn: mobTabVideo },
            movies: { panel: tabMovies, sideLink: sideNavMovies, mobBtn: mobTabMovies },
            library: { panel: tabLibrary, sideLink: sideNavLibrary, mobBtn: mobTabLibrary },
            premium: { panel: tabPremium, sideLink: sideNavPremium, mobBtn: mobTabPremium }
        };

        if (!tabs[tabName]) return;

        // Update Panels
        Object.keys(tabs).forEach(key => {
            if (tabs[key].panel) tabs[key].panel.classList.toggle('active', key === tabName);
            if (tabs[key].sideLink) tabs[key].sideLink.classList.toggle('active', key === tabName);
            if (tabs[key].mobBtn) tabs[key].mobBtn.classList.toggle('active', key === tabName);
        });

        // Special highlight for sidebar Liked Card
        if (sideLikedBtn) {
            sideLikedBtn.classList.toggle('active', tabName === 'library');
        }

        // Scroll to top
        if (viewportScroll) {
            viewportScroll.scrollTo({ top: 0, behavior: 'smooth' });
        }

        if (addToHistory && tabHistory[tabHistoryIndex] !== tabName) {
            tabHistory = tabHistory.slice(0, tabHistoryIndex + 1);
            tabHistory.push(tabName);
            tabHistoryIndex = tabHistory.length - 1;
        }

        // Focus search input when going to search tab
        if (tabName === 'search') {
            setTimeout(() => {
                if (searchPageViewInput) searchPageViewInput.focus();
            }, 100);
        }

        // Auto-load trending videos when opening video tab for first time
        if (tabName === 'video') {
            const grid = document.getElementById('ytVideosGrid');
            if (grid && grid.children.length === 0) {
                loadYouTubeVideos('Trending Music Videos 2024');
            }
        }

        // Auto-load movies when opening movies tab for first time
        if (tabName === 'movies') {
            const mGrid = document.getElementById('moviesGrid');
            if (mGrid && mGrid.children.length === 0) {
                loadMovies('action', '', 1);
            }
        }
    }

    // --- 6. EVENT LISTENERS SETUP ---
    function setupEventListeners() {
        // Desktop Sidebar Nav Buttons
        if (sideNavHome) sideNavHome.addEventListener('click', () => switchTab('home'));
        if (sideNavSearch) sideNavSearch.addEventListener('click', () => switchTab('search'));
        if (sideNavVideo) sideNavVideo.addEventListener('click', () => switchTab('video'));
        if (sideNavMovies) sideNavMovies.addEventListener('click', () => switchTab('movies'));
        if (sideNavLibrary) sideNavLibrary.addEventListener('click', () => switchTab('library'));
        if (sideNavPremium) sideNavPremium.addEventListener('click', () => switchTab('premium'));
        if (sideLikedBtn) sideLikedBtn.addEventListener('click', () => switchTab('library'));

        // Topbar & Profile Premium Links
        if (btnTopPremium) btnTopPremium.addEventListener('click', () => switchTab('premium'));
        if (btnUserProfile) btnUserProfile.addEventListener('click', () => switchTab('premium'));

        // Mobile Bottom Nav Buttons
        if (mobTabHome) mobTabHome.addEventListener('click', () => switchTab('home'));
        if (mobTabSearch) mobTabSearch.addEventListener('click', () => switchTab('search'));
        if (mobTabVideo) mobTabVideo.addEventListener('click', () => switchTab('video'));
        if (mobTabMovies) mobTabMovies.addEventListener('click', () => switchTab('movies'));
        if (mobTabLibrary) mobTabLibrary.addEventListener('click', () => switchTab('library'));
        if (mobTabPremium) mobTabPremium.addEventListener('click', () => switchTab('premium'));

        // Watch Video Toggles from Audio Player
        if (btnPlayerWatchVideo) btnPlayerWatchVideo.addEventListener('click', switchToVideoFromAudio);
        if (btnModalWatchVideo) btnModalWatchVideo.addEventListener('click', switchToVideoFromAudio);

        // YouTube Browser Tab Event Listeners
        const btnYtSearch = document.getElementById('btnYtSearch');
        const ytSearchInput = document.getElementById('ytSearchInput');
        if (btnYtSearch) btnYtSearch.addEventListener('click', handleYtSearch);
        if (ytSearchInput) ytSearchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') handleYtSearch();
        });

        document.querySelectorAll('.yt-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                document.querySelectorAll('.yt-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                const query = chip.getAttribute('data-q');
                if (ytSearchInput) ytSearchInput.value = query;
                loadYouTubeVideos(query);
            });
        });

        const btnSwitchAudio = document.getElementById('btnSwitchAudio');
        if (btnSwitchAudio) btnSwitchAudio.addEventListener('click', switchFromVideoToAudio);

        const btnYtDownload = document.getElementById('btnYtDownload');
        if (btnYtDownload) {
            btnYtDownload.addEventListener('click', () => {
                if (currentActiveVideoId) {
                    downloadSongById(currentActiveVideoId, currentActiveVideoTitle);
                } else {
                    showToast('Play a video first to download its audio');
                }
            });
        }

        const btnCloseYtPlayer = document.getElementById('btnCloseYtPlayer');
        if (btnCloseYtPlayer) btnCloseYtPlayer.addEventListener('click', closeYtPlayer);

        const ytNativeVideoEl = document.getElementById('ytNativeVideo');
        if (ytNativeVideoEl) {
            ytNativeVideoEl.addEventListener('play', () => {
                if (audio && !audio.paused) {
                    audio.pause();
                    if (svgPlay) svgPlay.classList.remove('hidden');
                    if (svgPause) svgPause.classList.add('hidden');
                    if (svgModalPlay) svgModalPlay.classList.remove('hidden');
                    if (svgModalPause) svgModalPause.classList.add('hidden');
                }
            });
        }

        const ytQualitySelect = document.getElementById('ytQualitySelect');
        const ytQualityBadge = document.getElementById('ytQualityBadge');
        if (ytQualitySelect) {
            ytQualitySelect.addEventListener('change', (e) => {
                const newQuality = e.target.value;
                currentVideoQuality = newQuality;
                try {
                    localStorage.setItem('soundwave_video_quality', newQuality);
                } catch(err) {}

                if (ytQualityBadge) ytQualityBadge.textContent = newQuality;

                const nativeVideo = document.getElementById('ytNativeVideo');
                const loader = document.getElementById('ytVideoLoader');

                if (nativeVideo && currentActiveVideoId) {
                    const savedTime = nativeVideo.currentTime || 0;
                    if (loader) {
                        loader.innerHTML = `
                            <div class="sp-spinner"></div>
                            <span>Buffering ${newQuality} video stream...</span>
                        `;
                        loader.classList.remove('hidden');
                    }

                    nativeVideo.src = `${API_BASE}/api/video_stream?id=${encodeURIComponent(currentActiveVideoId)}&quality=${encodeURIComponent(newQuality)}`;
                    nativeVideo.load();

                    nativeVideo.onloadedmetadata = () => {
                        try {
                            if (savedTime > 0 && savedTime < nativeVideo.duration) {
                                nativeVideo.currentTime = savedTime;
                            }
                        } catch(ex) {}
                        if (loader) loader.classList.add('hidden');
                        nativeVideo.play().catch(err => console.log('Autoplay:', err));
                    };

                    showToast(`Video quality set to ${newQuality} 🎬`);
                }
            });
        }

        // History Back / Forward
        if (btnHistoryBack) {
            btnHistoryBack.addEventListener('click', () => {
                if (tabHistoryIndex > 0) {
                    tabHistoryIndex--;
                    switchTab(tabHistory[tabHistoryIndex], false);
                }
            });
        }
        if (btnHistoryForward) {
            btnHistoryForward.addEventListener('click', () => {
                if (tabHistoryIndex < tabHistory.length - 1) {
                    tabHistoryIndex++;
                    switchTab(tabHistory[tabHistoryIndex], false);
                }
            });
        }

        // Topbar Search Input
        if (globalSearchInput) {
            globalSearchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    const query = globalSearchInput.value.trim();
                    if (query) {
                        switchTab('search');
                        if (searchPageViewInput) searchPageViewInput.value = query;
                        triggerSearch(query);
                    }
                }
            });
            globalSearchInput.addEventListener('input', () => {
                if (globalClearBtn) {
                    globalClearBtn.classList.toggle('hidden', !globalSearchInput.value);
                }
            });
        }

        if (globalClearBtn) {
            globalClearBtn.addEventListener('click', () => {
                globalSearchInput.value = '';
                globalClearBtn.classList.add('hidden');
                globalSearchInput.focus();
            });
        }

        // Search Page Input & Execute Button
        if (btnExecuteSearch) {
            btnExecuteSearch.addEventListener('click', () => {
                const query = searchPageViewInput ? searchPageViewInput.value.trim() : '';
                if (query) triggerSearch(query);
            });
        }

        if (searchPageViewInput) {
            searchPageViewInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    const query = searchPageViewInput.value.trim();
                    if (query) triggerSearch(query);
                }
            });
        }

        // Category Tiles Click
        if (categoryTilesGrid) {
            categoryTilesGrid.addEventListener('click', (e) => {
                const tile = e.target.closest('.cat-tile');
                if (!tile) return;
                const cat = tile.getAttribute('data-category');
                if (cat === 'movies') {
                    switchTab('movies');
                    return;
                }
                const query = tile.getAttribute('data-query');
                if (query) {
                    if (searchPageViewInput) searchPageViewInput.value = query;
                    triggerSearch(query);
                }
            });
        }

        // Home Tab Vegamovies Quick Buttons
        const jumboMoviesBtn = document.getElementById('jumboMoviesBtn');
        if (jumboMoviesBtn) jumboMoviesBtn.addEventListener('click', () => switchTab('movies'));

        const btnHomeViewAllMovies = document.getElementById('btnHomeViewAllMovies');
        if (btnHomeViewAllMovies) btnHomeViewAllMovies.addEventListener('click', () => switchTab('movies'));

        // Curated Playlists in Sidebar
        const curatedPlaylists = document.getElementById('curatedPlaylists');
        if (curatedPlaylists) {
            curatedPlaylists.addEventListener('click', (e) => {
                const item = e.target.closest('.pl-item');
                if (!item) return;
                const query = item.getAttribute('data-query');
                if (query) {
                    switchTab('search');
                    if (searchPageViewInput) searchPageViewInput.value = query;
                    triggerSearch(query);
                }
            });
        }

        // Shelf "Show all" buttons
        document.querySelectorAll('.shelf-more-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const query = btn.getAttribute('data-query');
                if (query) {
                    switchTab('search');
                    if (searchPageViewInput) searchPageViewInput.value = query;
                    triggerSearch(query);
                }
            });
        });

        // Jumbo Quick Play button
        if (jumboQuickPlay) {
            jumboQuickPlay.addEventListener('click', () => {
                if (activeQueue.length > 0) {
                    playTrackByIndex(0);
                } else {
                    triggerSearch('Top Trending Songs India 2024', true);
                }
            });
        }

        // Library Play All
        if (btnPlayLikedPlaylist) {
            btnPlayLikedPlaylist.addEventListener('click', () => {
                if (likedSongs.length === 0) {
                    showToast('No liked songs in your library yet!');
                    return;
                }
                activeQueue = [...likedSongs];
                renderQueueDrawer();
                playTrackByIndex(0);
                showToast(`Playing ${likedSongs.length} liked songs`);
            });
        }

        // Player Controls
        if (btnPlayPause) btnPlayPause.addEventListener('click', togglePlayPause);
        if (btnNext) btnNext.addEventListener('click', playNext);
        if (btnPrev) btnPrev.addEventListener('click', playPrev);

        if (btnShuffle) {
            btnShuffle.addEventListener('click', () => {
                isShuffle = !isShuffle;
                btnShuffle.classList.toggle('active', isShuffle);
                showToast(isShuffle ? 'Shuffle is ON' : 'Shuffle is OFF');
            });
        }

        if (btnLoop) {
            btnLoop.addEventListener('click', () => {
                isLoop = !isLoop;
                btnLoop.classList.toggle('active', isLoop);
                audio.loop = isLoop;
                showToast(isLoop ? 'Repeat is ON' : 'Repeat is OFF');
            });
        }

        // Scrubber Seeking
        if (scrubTrack) {
            scrubTrack.addEventListener('click', seekAudio);
        }

        // Volume Controls
        if (volumeRange) {
            volumeRange.addEventListener('input', (e) => {
                const vol = parseFloat(e.target.value);
                audio.volume = vol;
                updateVolumeIcon(vol);
            });
        }

        if (btnVolumeMute) {
            btnVolumeMute.addEventListener('click', toggleMute);
        }

        // Liked Song Heart Button in Player
        if (btnHeartLike) {
            btnHeartLike.addEventListener('click', toggleCurrentTrackLike);
        }

        // Queue Drawer Open/Close
        if (btnToggleQueue) {
            btnToggleQueue.addEventListener('click', () => {
                queueDrawerPanel.classList.toggle('open');
            });
        }
        if (btnCloseQueueDrawer) {
            btnCloseQueueDrawer.addEventListener('click', () => {
                queueDrawerPanel.classList.remove('open');
            });
        }

        // Audio Engine Events
        audio.addEventListener('timeupdate', updateAudioProgress);
        audio.addEventListener('ended', onTrackEnded);
        audio.addEventListener('play', () => {
            const ytNative = document.getElementById('ytNativeVideo');
            if (ytNative && !ytNative.paused) ytNative.pause();
            if (svgPlay) svgPlay.classList.add('hidden');
            if (svgPause) svgPause.classList.remove('hidden');
            if (svgModalPlay) svgModalPlay.classList.add('hidden');
            if (svgModalPause) svgModalPause.classList.remove('hidden');
            updateMediaSessionPlaybackState('playing');
        });
        audio.addEventListener('pause', () => {
            if (svgPlay) svgPlay.classList.remove('hidden');
            if (svgPause) svgPause.classList.add('hidden');
            if (svgModalPlay) svgModalPlay.classList.remove('hidden');
            if (svgModalPause) svgModalPause.classList.add('hidden');
            updateMediaSessionPlaybackState('paused');
        });
        audio.addEventListener('waiting', () => {
            if (playerSongArtist) {
                playerSongArtist.setAttribute('data-prev-text', playerSongArtist.textContent);
                playerSongArtist.textContent = 'Buffering stream...';
            }
        });
        audio.addEventListener('playing', () => {
            if (playerSongArtist && playerSongArtist.getAttribute('data-prev-text')) {
                playerSongArtist.textContent = playerSongArtist.getAttribute('data-prev-text');
                playerSongArtist.removeAttribute('data-prev-text');
            }
        });

        // Mobile Fullscreen Modal Open & Interactions
        const playerColLeft = document.querySelector('.player-col-left');
        if (playerColLeft) {
            playerColLeft.addEventListener('click', (e) => {
                if (e.target.closest('#btnHeartLike')) return;
                if (window.innerWidth <= 768 && mobileNowPlayingModal) {
                    mobileNowPlayingModal.classList.remove('hidden');
                }
            });
        }

        if (btnModalClose) {
            btnModalClose.addEventListener('click', () => {
                mobileNowPlayingModal.classList.add('hidden');
            });
        }

        if (btnModalQueue) {
            btnModalQueue.addEventListener('click', () => {
                queueDrawerPanel.classList.toggle('open');
            });
        }

        if (btnModalPlayPause) btnModalPlayPause.addEventListener('click', togglePlayPause);
        if (btnModalNext) btnModalNext.addEventListener('click', playNext);
        if (btnModalPrev) btnModalPrev.addEventListener('click', playPrev);

        if (btnModalShuffle) {
            btnModalShuffle.addEventListener('click', () => {
                isShuffle = !isShuffle;
                if (btnShuffle) btnShuffle.classList.toggle('active', isShuffle);
                btnModalShuffle.classList.toggle('active', isShuffle);
                showToast(isShuffle ? 'Shuffle is ON' : 'Shuffle is OFF');
            });
        }

        if (btnModalLoop) {
            btnModalLoop.addEventListener('click', () => {
                isLoop = !isLoop;
                if (btnLoop) btnLoop.classList.toggle('active', isLoop);
                btnModalLoop.classList.toggle('active', isLoop);
                audio.loop = isLoop;
                showToast(isLoop ? 'Repeat is ON' : 'Repeat is OFF');
            });
        }

        if (btnModalHeartLike) {
            btnModalHeartLike.addEventListener('click', toggleCurrentTrackLike);
        }

        if (modalScrubTrack) {
            modalScrubTrack.addEventListener('click', seekAudio);
        }

        // Song Download Button Listeners
        const btnDownloadSong = document.getElementById('btnDownloadSong');
        const btnModalDownload = document.getElementById('btnModalDownload');
        if (btnDownloadSong) btnDownloadSong.addEventListener('click', triggerDownloadCurrentTrack);
        if (btnModalDownload) btnModalDownload.addEventListener('click', triggerDownloadCurrentTrack);

        // PWA Install Prompt Listener
        const btnInstallPwa = document.getElementById('btnInstallPwa');
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            window.deferredInstallPrompt = e;
            if (btnInstallPwa) btnInstallPwa.style.display = 'flex';
        });

        // PWA Install Guide Modal Controls
        const pwaInstallModal = document.getElementById('pwaInstallModal');
        const pwaInstallBackdrop = document.getElementById('pwaInstallBackdrop');
        const btnPwaClose = document.getElementById('btnPwaClose');
        const btnPwaGotIt = document.getElementById('btnPwaGotIt');

        function openPwaInstallModal() {
            if (pwaInstallModal) pwaInstallModal.classList.remove('hidden');
        }

        function closePwaInstallModal() {
            if (pwaInstallModal) pwaInstallModal.classList.add('hidden');
        }

        if (btnPwaClose) btnPwaClose.addEventListener('click', closePwaInstallModal);
        if (pwaInstallBackdrop) pwaInstallBackdrop.addEventListener('click', closePwaInstallModal);
        if (btnPwaGotIt) btnPwaGotIt.addEventListener('click', closePwaInstallModal);

        if (btnInstallPwa) {
            btnInstallPwa.addEventListener('click', async () => {
                if (window.deferredInstallPrompt) {
                    window.deferredInstallPrompt.prompt();
                    const choice = await window.deferredInstallPrompt.userChoice;
                    if (choice.outcome === 'accepted') {
                        showToast('Installing SoundWave...');
                    }
                    window.deferredInstallPrompt = null;
                } else {
                    openPwaInstallModal();
                }
            });
        }

        // Subscription & Plan Button Listeners
        const btnScrollToPlans = document.getElementById('btnScrollToPlans');
        if (btnScrollToPlans) {
            btnScrollToPlans.addEventListener('click', () => {
                const plansSection = document.getElementById('premPlansSection');
                if (plansSection) plansSection.scrollIntoView({ behavior: 'smooth' });
            });
        }

        document.querySelectorAll('.btn-select-plan, .btn-prem-cta').forEach(btn => {
            btn.addEventListener('click', () => {
                const planKey = btn.getAttribute('data-plan') || 'individual';
                const price = btn.getAttribute('data-price') || '119';
                const name = btn.getAttribute('data-name') || 'Individual Premium';
                openCheckoutModal(planKey, price, name);
            });
        });

        // Checkout Modal Actions
        const btnCloseCheckout = document.getElementById('btnCloseCheckout');
        if (btnCloseCheckout) btnCloseCheckout.addEventListener('click', closeCheckoutModal);

        const checkoutModal = document.getElementById('checkoutModal');
        if (checkoutModal) {
            checkoutModal.addEventListener('click', (e) => {
                if (e.target === checkoutModal) closeCheckoutModal();
            });
        }

        // Payment Tabs Switcher
        document.querySelectorAll('.pay-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.pay-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                const method = tab.getAttribute('data-method');
                const upiPanel = document.getElementById('payPanelUpi');
                const cardPanel = document.getElementById('payPanelCard');
                const nbPanel = document.getElementById('payPanelNetbanking');
                if (upiPanel) upiPanel.classList.toggle('hidden', method !== 'upi');
                if (cardPanel) cardPanel.classList.toggle('hidden', method !== 'card');
                if (nbPanel) nbPanel.classList.toggle('hidden', method !== 'netbanking');
            });
        });

        // UPI App selector
        document.querySelectorAll('.upi-app-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.upi-app-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // Bank pills selector
        document.querySelectorAll('.bank-pill').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.bank-pill').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // Confirm Payment Button
        const btnConfirmPayment = document.getElementById('btnConfirmPayment');
        if (btnConfirmPayment) {
            btnConfirmPayment.addEventListener('click', handlePaymentConfirmation);
        }

        // Cancel Subscription Button
        const btnCancelSub = document.getElementById('btnCancelSub');
        if (btnCancelSub) {
            btnCancelSub.addEventListener('click', handleCancelSubscription);
        }
    }

    // --- 7. HOME QUICK PICKS ---
    function renderQuickPicks() {
        if (!quickPicksContainer) return;
        quickPicksContainer.innerHTML = '';

        QUICK_PICKS_SEEDS.forEach((seed, idx) => {
            const card = document.createElement('div');
            card.className = 'q-pick-card';
            card.innerHTML = `
                <img src="${seed.thumbnail}" alt="${escapeHtml(seed.title)}" loading="lazy">
                <span class="q-pick-card-title">${escapeHtml(seed.title)}</span>
                <div class="q-pick-play" title="Play">
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="black">
                        <polygon points="6 3 20 12 6 21 6 3"></polygon>
                    </svg>
                </div>
            `;

            card.addEventListener('click', () => {
                switchTab('search');
                if (searchPageViewInput) searchPageViewInput.value = seed.query;
                triggerSearch(seed.query, true);
            });

            quickPicksContainer.appendChild(card);
        });
    }

    // --- 8. SHELF DATA LOADER ---
    async function loadShelfData(query, containerEl) {
        if (!containerEl) return;
        containerEl.innerHTML = `
            <div style="grid-column: 1/-1; padding: 2rem 0; text-align: center; color: var(--sp-text-mute);">
                <div class="sp-spinner" style="margin: 0 auto 10px;"></div>
                <span style="font-size: 0.85rem;">Loading songs...</span>
            </div>
        `;

        try {
            const res = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(query)}`);
            const data = await res.json();

            if (data.results && data.results.length > 0) {
                renderCardGrid(data.results.slice(0, 8), containerEl);
            } else {
                containerEl.innerHTML = `<p style="color: var(--sp-text-mute); font-size: 0.9rem;">No tracks available right now.</p>`;
            }
        } catch (err) {
            console.error('Failed to load shelf for query:', query, err);
            containerEl.innerHTML = `<p style="color: var(--sp-text-mute); font-size: 0.85rem;">Could not load items.</p>`;
        }
    }

    function renderCardGrid(tracks, containerEl) {
        containerEl.innerHTML = '';
        tracks.forEach((track) => {
            const card = document.createElement('div');
            card.className = 'music-card';
            card.setAttribute('data-id', track.id);

            card.innerHTML = `
                <div class="card-img-box">
                    <img src="${track.thumbnail}" alt="${escapeHtml(track.title)}" loading="lazy">
                    <div class="card-float-play" title="Play">
                        <svg viewBox="0 0 24 24" width="22" height="22" fill="black">
                            <polygon points="6 3 20 12 6 21 6 3"></polygon>
                        </svg>
                    </div>
                </div>
                <div class="card-song-title" title="${escapeHtml(track.title)}">${escapeHtml(track.title)}</div>
                <div class="card-song-artist" title="${escapeHtml(track.channel)}">${escapeHtml(track.channel)}</div>
            `;

            card.addEventListener('click', () => {
                // Set activeQueue to this collection if not already playing from it
                activeQueue = tracks;
                const idx = tracks.findIndex(t => t.id === track.id);
                renderQueueDrawer();
                playTrackByIndex(idx !== -1 ? idx : 0);
            });

            containerEl.appendChild(card);
        });
    }

    // --- RENDER SEARCH RESULTS AS SPOTIFY TRACKLIST ---
    function renderSearchResults(tracks, containerEl) {
        if (!containerEl) return;
        containerEl.innerHTML = '';

        tracks.forEach((track, idx) => {
            const isPlayingThis = (currentTrackIndex !== -1 && activeQueue[currentTrackIndex]?.id === track.id);
            const isLiked = likedSongs.some(t => t.id === track.id);

            const row = document.createElement('div');
            row.className = `search-track-item ${isPlayingThis ? 'playing-active' : ''}`;
            row.setAttribute('data-id', track.id);

            row.innerHTML = `
                <div class="track-left">
                    <span class="track-num">${idx + 1}</span>
                    <div class="track-thumb-box">
                        <img src="${track.thumbnail}" alt="" loading="lazy">
                        <div class="track-play-hover">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="white">
                                <polygon points="6 3 20 12 6 21 6 3"></polygon>
                            </svg>
                        </div>
                    </div>
                    <div class="track-text-box">
                        <span class="track-name" title="${escapeHtml(track.title)}">${escapeHtml(track.title)}</span>
                        <span class="track-sub" title="${escapeHtml(track.channel)}">${escapeHtml(track.channel)}</span>
                    </div>
                </div>
                <div class="track-right">
                    <span class="track-dur">${track.duration || ''}</span>
                    <button class="track-like-btn ${isLiked ? 'liked' : ''}" title="Like">
                        <svg viewBox="0 0 24 24" width="18" height="18" fill="${isLiked ? 'var(--sp-green)' : 'none'}" stroke="currentColor" stroke-width="2">
                            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                        </svg>
                    </button>
                    <button class="track-dl-btn" title="Download Audio">
                        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                    </button>
                </div>
            `;

            row.addEventListener('click', (e) => {
                if (e.target.closest('.track-like-btn') || e.target.closest('.track-dl-btn')) return;
                activeQueue = tracks;
                renderQueueDrawer();
                playTrackByIndex(idx);
            });

            const dlBtn = row.querySelector('.track-dl-btn');
            if (dlBtn) {
                dlBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    downloadSongById(track.id, track.title);
                });
            }

            const likeBtn = row.querySelector('.track-like-btn');
            if (likeBtn) {
                likeBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const existingIdx = likedSongs.findIndex(t => t.id === track.id);
                    if (existingIdx !== -1) {
                        likedSongs.splice(existingIdx, 1);
                        likeBtn.classList.remove('liked');
                        const svg = likeBtn.querySelector('svg');
                        if (svg) svg.setAttribute('fill', 'none');
                        showToast('Removed from Liked Songs');
                    } else {
                        likedSongs.unshift({
                            id: track.id,
                            title: track.title,
                            channel: track.channel,
                            thumbnail: track.thumbnail,
                            duration: track.duration || '--:--'
                        });
                        likeBtn.classList.add('liked');
                        const svg = likeBtn.querySelector('svg');
                        if (svg) svg.setAttribute('fill', 'var(--sp-green)');
                        showToast('Added to Liked Songs â¤ï¸');
                    }
                    saveLikedSongs();
                    updateLikedUI();
                    if (currentTrackIndex !== -1 && activeQueue[currentTrackIndex]?.id === track.id) {
                        updateHeartButtonState(track.id);
                    }
                });
            }

            containerEl.appendChild(row);
        });
    }

    // --- 9. SEARCH ENGINE ---
    async function triggerSearch(query, autoPlayFirst = false) {
        if (!query) return;

        if (searchLoadingState) searchLoadingState.classList.remove('hidden');
        if (searchResultsWrapper) searchResultsWrapper.classList.add('hidden');
        if (searchResultsTitle) searchResultsTitle.textContent = `Results for "${query}"`;

        try {
            const res = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(query)}`);
            const data = await res.json();

            if (searchLoadingState) searchLoadingState.classList.add('hidden');
            if (searchResultsWrapper) searchResultsWrapper.classList.remove('hidden');

            if (data.results && data.results.length > 0) {
                activeQueue = data.results;
                renderSearchResults(data.results, searchResultsGrid);
                renderQueueDrawer();

                if (autoPlayFirst) {
                    playTrackByIndex(0);
                }
            } else {
                searchResultsGrid.innerHTML = `
                    <div style="grid-column: 1/-1; text-align: center; padding: 4rem 1rem; color: var(--sp-text-mute);">
                        <p style="font-size: 1.2rem; font-weight: 700; color: white; margin-bottom: 6px;">No songs found</p>
                        <p style="font-size: 0.9rem;">Check spelling or try searching another artist or song name.</p>
                    </div>
                `;
            }
        } catch (err) {
            console.error('Search request failed:', err);
            if (searchLoadingState) searchLoadingState.classList.add('hidden');
            if (searchResultsWrapper) searchResultsWrapper.classList.remove('hidden');
            searchResultsGrid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 3rem 1rem; color: #ef4444;">
                    <p style="font-size: 1.1rem; font-weight: 700;">Could not load search results.</p>
                    <p style="font-size: 0.85rem; color: var(--sp-text-sub);">Please check your network connection.</p>
                </div>
            `;
        }
    }

    // --- 10. AUDIO PLAYBACK & STREAM EXTRACTION ---
    async function playTrackByIndex(index) {
        if (index < 0 || index >= activeQueue.length) return;
        currentTrackIndex = index;
        const track = activeQueue[currentTrackIndex];

        // Update Bottom Player UI
        if (playerCoverImg) playerCoverImg.src = track.thumbnail;
        if (playerSongTitle) {
            playerSongTitle.textContent = track.title;
            playerSongTitle.title = track.title;
        }
        if (playerSongArtist) {
            playerSongArtist.textContent = track.channel;
            playerSongArtist.title = track.channel;
        }
        if (timeTotal) timeTotal.textContent = track.duration || '--:--';

        // Update Fullscreen Mobile Modal UI
        if (modalArtImg) modalArtImg.src = track.thumbnail;
        if (modalTrackTitle) modalTrackTitle.textContent = track.title;
        if (modalTrackArtist) modalTrackArtist.textContent = track.channel;
        if (modalTimeTotal) modalTimeTotal.textContent = track.duration || '--:--';

        // Check liked state
        updateHeartButtonState(track.id);

        // Update MediaSession for Background & Lockscreen Play
        updateMediaSession(track);
        renderQueueDrawer();
        highlightActiveCards(track.id);

        // Show fetching feedback
        if (svgPlay) svgPlay.classList.add('hidden');
        if (svgPause) svgPause.classList.remove('hidden');

        try {
            const res = await fetch(`${API_BASE}/api/stream?id=${encodeURIComponent(track.id)}`);
            const data = await res.json();

            if (data.streamUrl) {
                audio.src = data.streamUrl;
                audio.play().catch(err => {
                    console.warn('Playback autoplay waiting for user interaction:', err);
                });
            } else {
                throw new Error(data.error || 'Direct stream URL not found');
            }
        } catch (err) {
            console.error('Failed to load audio stream:', err);
            showToast('Failed to load audio. Skipping next...');
            setTimeout(playNext, 1800);
        }
    }

    function togglePlayPause() {
        if (!audio.src) {
            if (activeQueue.length > 0) {
                playTrackByIndex(0);
            } else if (likedSongs.length > 0) {
                activeQueue = [...likedSongs];
                renderQueueDrawer();
                playTrackByIndex(0);
            }
            return;
        }

        if (audio.paused) {
            audio.play().catch(err => console.warn(err));
        } else {
            audio.pause();
        }
    }

    function playNext() {
        if (activeQueue.length === 0) return;
        if (isShuffle) {
            let nextIndex = Math.floor(Math.random() * activeQueue.length);
            if (nextIndex === currentTrackIndex && activeQueue.length > 1) {
                nextIndex = (nextIndex + 1) % activeQueue.length;
            }
            playTrackByIndex(nextIndex);
        } else {
            let nextIndex = currentTrackIndex + 1;
            if (nextIndex >= activeQueue.length) nextIndex = 0;
            playTrackByIndex(nextIndex);
        }
    }

    function playPrev() {
        if (activeQueue.length === 0) return;
        if (audio.currentTime > 4) {
            audio.currentTime = 0;
            return;
        }
        let prevIndex = currentTrackIndex - 1;
        if (prevIndex < 0) prevIndex = activeQueue.length - 1;
        playTrackByIndex(prevIndex);
    }

    function onTrackEnded() {
        if (isLoop) {
            audio.currentTime = 0;
            audio.play();
        } else {
            playNext();
        }
    }

    // --- 11. PROGRESS & SCRUBBER ---
    function updateAudioProgress() {
        if (isNaN(audio.duration) || audio.duration === 0) return;

        const current = audio.currentTime;
        const total = audio.duration;
        const pct = (current / total) * 100;

        if (scrubFill) scrubFill.style.width = `${pct}%`;
        if (scrubThumb) scrubThumb.style.left = `${pct}%`;
        if (mobProgFill) mobProgFill.style.width = `${pct}%`;
        if (modalScrubFill) modalScrubFill.style.width = `${pct}%`;
        if (modalScrubThumb) modalScrubThumb.style.left = `${pct}%`;

        if (timeCurrent) timeCurrent.textContent = formatTime(current);
        if (timeTotal && isFinite(total)) timeTotal.textContent = formatTime(total);
        if (modalTimeCurrent) modalTimeCurrent.textContent = formatTime(current);
        if (modalTimeTotal && isFinite(total)) modalTimeTotal.textContent = formatTime(total);

        // Update MediaSession Position State (smooth lockscreen scrubber)
        if ('mediaSession' in navigator && 'setPositionState' in navigator.mediaSession) {
            try {
                navigator.mediaSession.setPositionState({
                    duration: total,
                    playbackRate: audio.playbackRate || 1,
                    position: current
                });
            } catch (e) {
                // Ignore transient position state issues
            }
        }
    }

    function seekAudio(e) {
        if (!audio.src || isNaN(audio.duration)) return;
        const targetTrack = e.currentTarget || scrubTrack;
        const rect = targetTrack.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const width = rect.width;
        const seekRatio = Math.max(0, Math.min(1, clickX / width));
        audio.currentTime = seekRatio * audio.duration;
    }

    // --- 12. VOLUME & MUTE ---
    function toggleMute() {
        if (audio.volume > 0) {
            previousVolume = audio.volume;
            audio.volume = 0;
            if (volumeRange) volumeRange.value = 0;
            updateVolumeIcon(0);
        } else {
            audio.volume = previousVolume || 0.9;
            if (volumeRange) volumeRange.value = audio.volume;
            updateVolumeIcon(audio.volume);
        }
    }

    function updateVolumeIcon(vol) {
        if (vol === 0) {
            if (svgVolHigh) svgVolHigh.classList.add('hidden');
            if (svgVolMute) svgVolMute.classList.remove('hidden');
        } else {
            if (svgVolHigh) svgVolHigh.classList.remove('hidden');
            if (svgVolMute) svgVolMute.classList.add('hidden');
        }
    }

    // --- 13. LIKED SONGS & LIBRARY SYSTEM ---
    function toggleCurrentTrackLike() {
        if (currentTrackIndex === -1 || !activeQueue[currentTrackIndex]) {
            showToast('Play a song first to like it');
            return;
        }

        const track = activeQueue[currentTrackIndex];
        const existingIdx = likedSongs.findIndex(item => item.id === track.id);

        if (existingIdx !== -1) {
            // Remove from liked
            likedSongs.splice(existingIdx, 1);
            saveLikedSongs();
            updateHeartButtonState(track.id);
            showToast('Removed from Liked Songs');
        } else {
            // Add to liked
            likedSongs.unshift({
                id: track.id,
                title: track.title,
                channel: track.channel,
                thumbnail: track.thumbnail,
                duration: track.duration || '--:--'
            });
            saveLikedSongs();
            updateHeartButtonState(track.id);
            showToast('Added to Liked Songs â¤ï¸');
        }

        updateLikedUI();
    }

    function removeLikedSong(trackId, event) {
        if (event) event.stopPropagation();
        likedSongs = likedSongs.filter(t => t.id !== trackId);
        saveLikedSongs();
        updateLikedUI();
        if (currentTrackIndex !== -1 && activeQueue[currentTrackIndex]?.id === trackId) {
            updateHeartButtonState(trackId);
        }
        showToast('Removed from Liked Songs');
    }

    function saveLikedSongs() {
        try {
            localStorage.setItem(STORAGE_KEY_LIKED, JSON.stringify(likedSongs));
        } catch (e) {
            console.error('Failed to save liked songs:', e);
        }
        // Cloud Sync: push update to Firestore
        if (window.SoundWaveFirebase && typeof window.SoundWaveFirebase.pushUserDataToCloud === 'function') {
            window.SoundWaveFirebase.pushUserDataToCloud({
                likedSongs: likedSongs,
                subscription: getSubscription()
            });
        }
    }

    function updateHeartButtonState(trackId) {
        const isLiked = likedSongs.some(t => t.id === trackId);
        if (btnHeartLike) btnHeartLike.classList.toggle('liked', isLiked);
        if (btnModalHeartLike) btnModalHeartLike.classList.toggle('liked', isLiked);
    }

    function updateLikedUI() {
        const count = likedSongs.length;
        if (sideLikedBadge) sideLikedBadge.textContent = `${count} ${count === 1 ? 'song' : 'songs'}`;
        if (librarySongCount) librarySongCount.textContent = `${count} ${count === 1 ? 'song' : 'songs'}`;

        renderLibraryTable();
    }

    function renderLibraryTable() {
        if (!libraryTableBody) return;

        if (likedSongs.length === 0) {
            libraryTableBody.innerHTML = `
                <div class="empty-library">
                    <p>No liked songs yet.</p>
                    <span>Click the heart icon on any song while listening to save it here!</span>
                </div>
            `;
            return;
        }

        libraryTableBody.innerHTML = '';
        likedSongs.forEach((song, idx) => {
            const row = document.createElement('div');
            row.className = `table-song-row ${currentTrackIndex !== -1 && activeQueue[currentTrackIndex]?.id === song.id ? 'active' : ''}`;
            
            row.innerHTML = `
                <div class="row-index">${idx + 1}</div>
                <div class="row-title-box">
                    <img src="${song.thumbnail}" alt="" loading="lazy">
                    <div class="row-meta-col">
                        <span class="row-title-text" title="${escapeHtml(song.title)}">${escapeHtml(song.title)}</span>
                        <span class="row-artist-sub" title="${escapeHtml(song.channel)}">${escapeHtml(song.channel)}</span>
                    </div>
                </div>
                <div class="row-channel-text" title="${escapeHtml(song.channel)}">${escapeHtml(song.channel)}</div>
                <div class="row-time-text">${song.duration || '--:--'}</div>
                <button class="btn-del-like" title="Remove from Liked">
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
                        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                    </svg>
                </button>
            `;

            row.addEventListener('click', (e) => {
                if (e.target.closest('.btn-del-like')) return;
                activeQueue = [...likedSongs];
                renderQueueDrawer();
                playTrackByIndex(idx);
            });

            const delBtn = row.querySelector('.btn-del-like');
            if (delBtn) {
                delBtn.addEventListener('click', (e) => removeLikedSong(song.id, e));
            }

            libraryTableBody.appendChild(row);
        });
    }

    // --- 14. QUEUE DRAWER RENDERER ---
    function renderQueueDrawer() {
        if (!queueDrawerList) return;

        if (activeQueue.length === 0) {
            queueDrawerList.innerHTML = `<p class="drawer-empty-text">Queue is empty</p>`;
            return;
        }

        queueDrawerList.innerHTML = '';
        activeQueue.forEach((track, idx) => {
            const item = document.createElement('div');
            item.className = `drawer-item ${idx === currentTrackIndex ? 'active' : ''}`;
            item.innerHTML = `
                <img src="${track.thumbnail}" alt="" loading="lazy">
                <div style="min-width: 0; flex: 1;">
                    <div class="drawer-item-title">${escapeHtml(track.title)}</div>
                    <div class="drawer-item-sub">${escapeHtml(track.channel)}</div>
                </div>
                ${idx === currentTrackIndex ? '<span style="font-size:0.75rem; color:var(--sp-green); font-weight:700;">PLAYING</span>' : ''}
            `;

            item.addEventListener('click', () => {
                playTrackByIndex(idx);
            });

            queueDrawerList.appendChild(item);
        });
    }

    function highlightActiveCards(trackId) {
        document.querySelectorAll('.music-card').forEach(card => {
            card.classList.toggle('playing-active', card.getAttribute('data-id') === trackId);
        });
        document.querySelectorAll('.search-track-item').forEach(item => {
            item.classList.toggle('playing-active', item.getAttribute('data-id') === trackId);
        });
        document.querySelectorAll('.table-song-row').forEach(row => {
            const titleEl = row.querySelector('.row-title-text');
            if (titleEl && activeQueue[currentTrackIndex]) {
                row.classList.toggle('active', titleEl.textContent === activeQueue[currentTrackIndex].title);
            }
        });
    }

    // --- 15. SCREEN-OFF BACKGROUND PLAYBACK (MEDIASESSION API) ---
    function setupMediaSession() {
        if (!('mediaSession' in navigator)) {
            console.log('MediaSession API not supported in this browser.');
            return;
        }

        navigator.mediaSession.setActionHandler('play', () => audio.play());
        navigator.mediaSession.setActionHandler('pause', () => audio.pause());
        navigator.mediaSession.setActionHandler('previoustrack', playPrev);
        navigator.mediaSession.setActionHandler('nexttrack', playNext);

        try {
            navigator.mediaSession.setActionHandler('seekto', (details) => {
                if (details.seekTime && isFinite(details.seekTime)) {
                    audio.currentTime = details.seekTime;
                }
            });
        } catch (e) {
            // seekto not supported
        }
    }

    function updateMediaSession(track) {
        if (!('mediaSession' in navigator)) return;

        navigator.mediaSession.metadata = new MediaMetadata({
            title: track.title,
            artist: track.channel,
            album: 'SoundWave Premium',
            artwork: [
                { src: track.thumbnail, sizes: '96x96', type: 'image/jpeg' },
                { src: track.thumbnail, sizes: '128x128', type: 'image/jpeg' },
                { src: track.thumbnail, sizes: '192x192', type: 'image/jpeg' },
                { src: track.thumbnail, sizes: '256x256', type: 'image/jpeg' },
                { src: track.thumbnail, sizes: '512x512', type: 'image/jpeg' }
            ]
        });
    }

    function updateMediaSessionPlaybackState(state) {
        if ('mediaSession' in navigator) {
            navigator.mediaSession.playbackState = state;
        }
    }

    // --- 16. TOAST NOTIFICATIONS ---
    function showToast(message) {
        if (!spToastAlert || !toastAlertText) return;
        toastAlertText.textContent = message;
        spToastAlert.classList.remove('hidden');

        if (toastTimeout) clearTimeout(toastTimeout);
        toastTimeout = setTimeout(() => {
            spToastAlert.classList.add('hidden');
        }, 2500);
    }

    // --- 17. UTILITY HELPERS ---
    function formatTime(seconds) {
        if (isNaN(seconds) || !isFinite(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // --- 18. DOWNLOAD AUDIO ---
    function triggerDownloadCurrentTrack() {
        if (currentTrackIndex === -1 || !activeQueue[currentTrackIndex]) {
            showToast('Play a song first to download it');
            return;
        }
        const track = activeQueue[currentTrackIndex];
        downloadSongById(track.id, track.title);
    }

    function downloadSongById(trackId, title) {
        if (!trackId) return;
        showToast(`Downloading: ${title || 'Audio'}...`);
        const dlUrl = `${API_BASE}/api/download?id=${encodeURIComponent(trackId)}`;
        const a = document.createElement('a');
        a.href = dlUrl;
        a.download = `${title || 'Song'}.m4a`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    // --- 19. SERVICE WORKER REGISTRATION (OFFLINE & PWA) ---
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/sw.js').then((reg) => {
                console.log('SoundWave PWA Service Worker ready:', reg.scope);
            }).catch((err) => {
                console.log('SW registration note:', err);
            });
        });
    }

    // --- 20. PREMIUM SUBSCRIPTION SYSTEM ---
    const STORAGE_KEY_SUB = 'soundwave_subscription_data';
    let currentPendingPlan = { key: 'individual', price: '119', name: 'Individual Premium' };

    function getSubscription() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY_SUB);
            if (raw) return JSON.parse(raw);
        } catch (e) {
            console.error('Failed to load subscription:', e);
        }
        return { active: false, plan: 'free', planName: 'Free Plan', price: 0 };
    }

    function saveSubscription(sub) {
        try {
            localStorage.setItem(STORAGE_KEY_SUB, JSON.stringify(sub));
        } catch (e) {
            console.error('Failed to save subscription:', e);
        }
        updateSubscriptionUI();
        // Cloud Sync: push active subscription to Firestore
        if (window.SoundWaveFirebase && typeof window.SoundWaveFirebase.pushUserDataToCloud === 'function') {
            window.SoundWaveFirebase.pushUserDataToCloud({
                likedSongs: likedSongs,
                subscription: sub
            });
        }
    }

    function updateSubscriptionUI() {
        const sub = getSubscription();
        const activeSubCard = document.getElementById('activeSubCard');
        const activePlanName = document.getElementById('activePlanName');
        const activePlanExpiry = document.getElementById('activePlanExpiry');
        const userAvatarLabel = document.getElementById('userAvatarLabel');
        const userAvatarIcon = document.getElementById('userAvatarIcon');
        const btnTopPremium = document.getElementById('btnTopPremium');

        if (sub.active) {
            if (btnTopPremium) {
                btnTopPremium.classList.add('active-premium');
                const label = btnTopPremium.querySelector('.prem-top-label');
                if (label) label.textContent = 'VIP Member ðŸ‘‘';
            }
            if (userAvatarIcon) userAvatarIcon.textContent = 'ðŸ‘‘';
            if (userAvatarLabel) userAvatarLabel.textContent = sub.planName || 'VIP Member';

            if (activeSubCard) activeSubCard.classList.remove('hidden');
            if (activePlanName) activePlanName.textContent = sub.planName || 'Individual Premium';
            if (activePlanExpiry) {
                const expDate = sub.expiresAt ? new Date(sub.expiresAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '60 days from now';
                activePlanExpiry.textContent = `Renews automatically on ${expDate}`;
            }

            // Update modal audio badge
            const modalBadge = document.querySelector('.modal-footer-badge span:last-child');
            if (modalBadge) {
                modalBadge.textContent = 'Ultra HD 320k Studio Audio â€¢ Screen-Off Background Stream ðŸ‘‘';
            }
        } else {
            if (btnTopPremium) {
                btnTopPremium.classList.remove('active-premium');
                const label = btnTopPremium.querySelector('.prem-top-label');
                if (label) label.textContent = 'Explore Premium';
            }
            if (userAvatarIcon) userAvatarIcon.textContent = 'ðŸŽ§';
            if (userAvatarLabel) userAvatarLabel.textContent = 'Free Plan';

            if (activeSubCard) activeSubCard.classList.add('hidden');
        }
    }

    function openCheckoutModal(planKey, price, name) {
        currentPendingPlan = { key: planKey, price: price, name: name };

        const checkoutModal = document.getElementById('checkoutModal');
        const checkoutPlanTitle = document.getElementById('checkoutPlanTitle');
        const checkoutPriceTag = document.getElementById('checkoutPriceTag');
        const summaryTodayCost = document.getElementById('summaryTodayCost');
        const summaryNextBilling = document.getElementById('summaryNextBilling');
        const btnPayText = document.getElementById('btnPayText');

        if (checkoutPlanTitle) checkoutPlanTitle.textContent = name;
        if (checkoutPriceTag) checkoutPriceTag.textContent = planKey === 'mini' ? `â‚¹${price} / 1 day` : `â‚¹${price} / month`;

        const isTrial = (planKey === 'individual');
        if (summaryTodayCost) {
            summaryTodayCost.textContent = isTrial ? 'â‚¹0.00 (60-Day Free Trial - 2 Months Free)' : `â‚¹${price}.00 (Instant Activation)`;
        }
        if (summaryNextBilling) {
            summaryNextBilling.textContent = isTrial 
                ? `Billed â‚¹${price}/month starting in 60 days (2 months free). Cancel anytime.`
                : `Instant activation. 256-Bit SSL secured.`;
        }
        if (btnPayText) {
            btnPayText.textContent = isTrial ? 'Start 2 Months Free Trial' : `Pay â‚¹${price} & Activate`;
        }

        if (checkoutModal) checkoutModal.classList.remove('hidden');
    }

    function closeCheckoutModal() {
        const checkoutModal = document.getElementById('checkoutModal');
        if (checkoutModal) checkoutModal.classList.add('hidden');
    }

    function handlePaymentConfirmation() {
        const btnConfirm = document.getElementById('btnConfirmPayment');
        const btnPayText = document.getElementById('btnPayText');
        const paySpinner = document.getElementById('paySpinner');

        if (btnConfirm) btnConfirm.disabled = true;
        if (btnPayText) btnPayText.textContent = 'Verifying Payment...';
        if (paySpinner) paySpinner.classList.remove('hidden');

        setTimeout(() => {
            const isTrial = (currentPendingPlan.key === 'individual');
            const durationMs = isTrial ? (60 * 24 * 60 * 60 * 1000) : (currentPendingPlan.key === 'mini' ? 24 * 60 * 60 * 1000 : 30 * 24 * 60 * 60 * 1000);
            const expiryTime = Date.now() + durationMs;
            const sub = {
                active: true,
                plan: currentPendingPlan.key,
                planName: isTrial ? `${currentPendingPlan.name} (2 Months Free Trial)` : currentPendingPlan.name,
                price: currentPendingPlan.price,
                isTrial: isTrial,
                activatedAt: Date.now(),
                expiresAt: expiryTime
            };

            saveSubscription(sub);

            if (paySpinner) paySpinner.classList.add('hidden');
            if (btnPayText) btnPayText.textContent = 'Payment Successful!';
            if (btnConfirm) btnConfirm.disabled = false;

            closeCheckoutModal();
            showToast(isTrial ? 'ðŸŽ‰ Congratulations! 2 Months Free Trial is now ACTIVE!' : `ðŸŽ‰ Congratulations! ${currentPendingPlan.name} is now ACTIVE!`);
            switchTab('premium');

            // Scroll to active card smoothly
            setTimeout(() => {
                const activeCard = document.getElementById('activeSubCard');
                if (activeCard) activeCard.scrollIntoView({ behavior: 'smooth' });
            }, 300);
        }, 1200);
    }

    function handleCancelSubscription() {
        if (!confirm('Are you sure you want to cancel your SoundWave Premium membership?')) return;

        const sub = { active: false, plan: 'free', planName: 'Free Plan', price: 0 };
        saveSubscription(sub);
        showToast('Subscription cancelled. You are now on the Free plan.');
        updateSubscriptionUI();
    }

    // --- 21. YOUTUBE BROWSER & VIDEO PLAYER ENGINE ---
    let currentActiveVideoId = null;
    let currentActiveVideoTitle = '';
    let currentActiveVideoChannel = '';
    let currentVideoQuality = localStorage.getItem('soundwave_video_quality') || '1080p';

    function extractYouTubeId(urlOrQuery) {
        if (!urlOrQuery) return null;
        const regExp = /(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/;
        const match = urlOrQuery.match(regExp);
        return match ? match[1] : null;
    }

    async function handleYtSearch() {
        const input = document.getElementById('ytSearchInput');
        const query = (input?.value || '').trim();
        if (!query) return;

        // Check if user entered a direct YouTube video URL
        const directId = extractYouTubeId(query);
        if (directId) {
            playYouTubeVideo(directId, 'SoundWave Video', 'Direct Link');
            return;
        }

        loadYouTubeVideos(query);
    }

    async function loadYouTubeVideos(query) {
        const grid = document.getElementById('ytVideosGrid');
        const titleEl = document.getElementById('ytSectionTitle');
        const spinner = document.getElementById('ytLoadingSpinner');

        if (titleEl) titleEl.textContent = `Results for "${query}"`;
        if (spinner) spinner.classList.remove('hidden');
        if (grid) {
            grid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 3rem 1rem; color: #a7a7a7;">
                    <div class="sp-spinner" style="margin: 0 auto 12px;"></div>
                    <span>Loading SoundWave videos...</span>
                </div>
            `;
        }

        try {
            const res = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(query)}`);
            const data = await res.json();

            if (spinner) spinner.classList.add('hidden');

            if (data.results && data.results.length > 0) {
                renderYtVideoCards(data.results, grid);
            } else {
                if (grid) {
                    grid.innerHTML = `
                        <div style="grid-column: 1/-1; text-align: center; padding: 3rem 1rem; color: #a7a7a7;">
                            <p style="font-size: 1.1rem; color: #ffffff; font-weight: 700; margin-bottom: 6px;">No videos found</p>
                            <p style="font-size: 0.85rem;">Try searching another keyword or paste a direct video link.</p>
                        </div>
                    `;
                }
            }
        } catch (err) {
            console.error('Failed to load YouTube videos:', err);
            if (spinner) spinner.classList.add('hidden');
            if (grid) {
                grid.innerHTML = `<p style="grid-column: 1/-1; color: #ef4444; text-align: center; padding: 2rem;">Could not load videos. Please check connection.</p>`;
            }
        }
    }

    function renderYtVideoCards(videos, containerEl, append = false) {
        if (!containerEl) return;
        if (!append) containerEl.innerHTML = '';

        // Generate high-view viral badges for Internet top trending songs
        const viewBadges = ['🔥 850M+ Views', '⭐ 1.2B Views', '💥 420M Views', '👑 670M Views', '⚡ 310M Views', '🔥 Trending #1', '🌟 940M Views', '🚀 560M Views'];
        const existingIds = new Set(Array.from(containerEl.querySelectorAll('.yt-video-card')).map(c => c.getAttribute('data-id')));

        videos.forEach((video, idx) => {
            if (append && existingIds.has(video.id)) return;
            const card = document.createElement('div');
            card.className = 'yt-video-card';
            card.setAttribute('data-id', video.id);
            const viewTag = viewBadges[idx % viewBadges.length];

            card.innerHTML = `
                <div class="yt-thumb-box">
                    <img src="${video.thumbnail}" alt="${escapeHtml(video.title)}" loading="lazy">
                    <span class="yt-dur-pill">${video.duration || '4:15'}</span>
                    <span style="position: absolute; top: 8px; left: 8px; background: rgba(0,0,0,0.85); color: #1db954; font-size: 0.7rem; font-weight: 800; padding: 2px 7px; border-radius: 4px; border: 1px solid rgba(29,185,84,0.4);">${viewTag}</span>
                    <div class="yt-card-hover-play">
                        <div class="yt-play-bubble">
                            <svg viewBox="0 0 24 24" width="22" height="22" fill="#000">
                                <polygon points="6 3 20 12 6 21 6 3"></polygon>
                            </svg>
                        </div>
                    </div>
                </div>
                <div class="yt-card-info" style="padding: 10px 12px;">
                    <div class="yt-card-title" style="font-weight: 700; font-size: 0.95rem; line-height: 1.3;" title="${escapeHtml(video.title)}">${escapeHtml(video.title)}</div>
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 6px;">
                        <span class="yt-card-channel" style="font-size: 0.8rem; color: #a7a7a7;" title="${escapeHtml(video.channel)}">${escapeHtml(video.channel)}</span>
                        <span style="font-size: 0.75rem; color: #1db954; font-weight: 700;">1080p HD</span>
                    </div>
                </div>
            `;

            card.addEventListener('click', () => {
                playYouTubeVideo(video.id, video.title, video.channel);
                // Scroll smoothly to player
                const th = document.getElementById('ytPlayerTheater');
                if (th) th.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });

            containerEl.appendChild(card);
        });
    }

    function playYouTubeVideo(videoId, title, channel) {
        if (!videoId) return;

        // 1. Pause background audio if currently playing so audio doesn't overlap
        if (audio && !audio.paused) {
            audio.pause();
            isPlaying = false;
            updatePlayPauseUI();
        }

        // 2. Set active video state
        currentActiveVideoId = videoId;
        currentActiveVideoTitle = title || 'SoundWave Video';
        currentActiveVideoChannel = channel || 'SoundWave Artist';

        // 3. Update Meta in Theater Box
        const theater = document.getElementById('ytPlayerTheater');
        const nativeVideo = document.getElementById('ytNativeVideo');
        const iframe = document.getElementById('ytVideoIframe');
        const loader = document.getElementById('ytVideoLoader');
        const activeTitle = document.getElementById('ytActiveTitle');
        const activeChannel = document.getElementById('ytActiveChannel');
        const btnYtOpenApp = document.getElementById('btnYtOpenApp');
        const ytQualitySelect = document.getElementById('ytQualitySelect');
        const ytQualityBadge = document.getElementById('ytQualityBadge');

        if (activeTitle) activeTitle.textContent = currentActiveVideoTitle;
        if (activeChannel) activeChannel.textContent = currentActiveVideoChannel;
        if (ytQualitySelect) ytQualitySelect.value = currentVideoQuality;
        if (ytQualityBadge) ytQualityBadge.textContent = currentVideoQuality;
        if (btnYtOpenApp) {
            btnYtOpenApp.href = '#';
        btnYtOpenApp.onclick = (e) => {
            e.preventDefault();
            const shareUrl = window.location.origin + '?v=' + encodeURIComponent(videoId);
            navigator.clipboard.writeText(shareUrl).then(() => {
                showToast('Video link copied to clipboard!');
            }).catch(() => {
                showToast('Link ready to share!');
            });
        };
        }

        if (theater) {
            theater.classList.remove('hidden');
            theater.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }

        // 4. Instant Ultra-Fast Stream Playback (0.2s start, zero server buffering lag)
        if (theater) theater.classList.remove('hidden');
        if (loader) loader.classList.add('hidden');

        // Play instantly with clean high-speed player without 20-second server wait
        if (iframe) {
            if (nativeVideo) nativeVideo.classList.add('hidden');
            iframe.classList.remove('hidden');
            const cleanEmbedUrl = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(videoId)}?autoplay=1&playsinline=1&rel=0&modestbranding=1&enablejsapi=1&origin=${encodeURIComponent(window.location.origin)}`;
            iframe.src = cleanEmbedUrl;
            showToast(`Streaming ${currentActiveVideoTitle} in 1080p HD...`);
        } else if (iframe) {
            iframe.classList.remove('hidden');
            iframe.src = `https://www.youtube.com/embed/${encodeURIComponent(videoId)}?autoplay=1&playsinline=1&rel=0&modestbranding=1`;
        }
    }

    function closeYtPlayer() {
        const theater = document.getElementById('ytPlayerTheater');
        const iframe = document.getElementById('ytVideoIframe');
        const nativeVideo = document.getElementById('ytNativeVideo');
        const loader = document.getElementById('ytVideoLoader');

        if (nativeVideo) {
            nativeVideo.pause();
            nativeVideo.removeAttribute('src');
            nativeVideo.load();
        }
        if (iframe) iframe.src = '';
        if (loader) loader.classList.add('hidden');
        if (theater) theater.classList.add('hidden');
    }

    function switchFromVideoToAudio() {
        if (!currentActiveVideoId) {
            showToast('No active video to switch from');
            return;
        }

        // Stop iframe video
        closeYtPlayer();

        // Create track and load into background audio queue
        const track = {
            id: currentActiveVideoId,
            title: currentActiveVideoTitle || 'Audio Track',
            channel: currentActiveVideoChannel || 'SoundWave Artist',
            thumbnail: `https://i.ytimg.com/vi/${currentActiveVideoId}/hqdefault.jpg`,
            duration: '--:--'
        };

        activeQueue = [track];
        renderQueueDrawer();
        playTrackByIndex(0);
        showToast('Switched to Background Audio • You can now lock screen! 🎧');
    }

    function switchToVideoFromAudio() {
        if (currentTrackIndex === -1 || !activeQueue[currentTrackIndex]) {
            showToast('Play a song first to watch its video');
            return;
        }

        const track = activeQueue[currentTrackIndex];
        // Close mobile fullscreen modal if open
        const mobileModal = document.getElementById('mobileNowPlayingModal');
        if (mobileModal) mobileModal.classList.add('hidden');

        // Switch to video tab
        switchTab('video');

        // Play the video
        playYouTubeVideo(track.id, track.title, track.channel);
        showToast(`Playing video: ${track.title} 🎬`);
    }

    // ==========================================================================
    // FIREBASE AUTH & CLOUD FIRESTORE INTEGRATION SUITE
    // ==========================================================================
    function setupFirebaseAndAuthSuite() {
        // Topbar triggers
        const btnFirebasePill = document.getElementById('btnFirebasePill');
        const fbPillText = document.getElementById('fbPillText');
        const fbPillDot = document.getElementById('fbPillDot');
        const btnTopLogin = document.getElementById('btnTopLogin');
        const btnUserProfile = document.getElementById('btnUserProfile');
        const userAvatarImg = document.getElementById('userAvatarImg');
        const userAvatarIcon = document.getElementById('userAvatarIcon');
        const userAvatarLabel = document.getElementById('userAvatarLabel');

        // Auth Modal elements
        const authModal = document.getElementById('authModal');
        const authBackdrop = document.getElementById('authBackdrop');
        const btnAuthClose = document.getElementById('btnAuthClose');
        const btnGoogleSignIn = document.getElementById('btnGoogleSignIn');
        const authEmailForm = document.getElementById('authEmailForm');
        const groupDisplayName = document.getElementById('groupDisplayName');
        const authDisplayName = document.getElementById('authDisplayName');
        const authEmailInput = document.getElementById('authEmailInput');
        const authPasswordInput = document.getElementById('authPasswordInput');
        const btnTogglePassword = document.getElementById('btnTogglePassword');
        const btnAuthSubmit = document.getElementById('btnAuthSubmit');
        const authSubmitText = document.getElementById('authSubmitText');
        const authSpinner = document.getElementById('authSpinner');
        const authErrorBanner = document.getElementById('authErrorBanner');
        const btnSwitchAuthMode = document.getElementById('btnSwitchAuthMode');
        const authDialogTitle = document.getElementById('authDialogTitle');
        const authSwitchPrompt = document.getElementById('authSwitchPrompt');

        // User Profile Modal elements
        const userProfileModal = document.getElementById('userProfileModal');
        const userProfileBackdrop = document.getElementById('userProfileBackdrop');
        const btnProfileClose = document.getElementById('btnProfileClose');
        const profileBigPhoto = document.getElementById('profileBigPhoto');
        const profileBigEmoji = document.getElementById('profileBigEmoji');
        const profileNameDisplay = document.getElementById('profileNameDisplay');
        const profileEmailDisplay = document.getElementById('profileEmailDisplay');
        const profileMembershipPill = document.getElementById('profileMembershipPill');
        const profileSyncModePill = document.getElementById('profileSyncModePill');
        const syncLikedCount = document.getElementById('syncLikedCount');
        const btnManualSync = document.getElementById('btnManualSync');
        const btnOpenFirebaseSettings = document.getElementById('btnOpenFirebaseSettings');
        const btnProfileGoPremium = document.getElementById('btnProfileGoPremium');
        const btnLogoutUser = document.getElementById('btnLogoutUser');

        // Firebase Settings Modal elements
        const firebaseSettingsModal = document.getElementById('firebaseSettingsModal');
        const fbSettingsBackdrop = document.getElementById('fbSettingsBackdrop');
        const btnFbSettingsClose = document.getElementById('btnFbSettingsClose');
        const fbConnectionBanner = document.getElementById('fbConnectionBanner');
        const bannerStatusTitle = document.getElementById('bannerStatusTitle');
        const bannerStatusDesc = document.getElementById('bannerStatusDesc');
        const fbTabPaste = document.getElementById('fbTabPaste');
        const fbTabManual = document.getElementById('fbTabManual');
        const fbPanePaste = document.getElementById('fbPanePaste');
        const fbPaneManual = document.getElementById('fbPaneManual');
        const fbSnippetTextarea = document.getElementById('fbSnippetTextarea');
        const fbInputApiKey = document.getElementById('fbInputApiKey');
        const fbInputProjectId = document.getElementById('fbInputProjectId');
        const fbInputAuthDomain = document.getElementById('fbInputAuthDomain');
        const fbInputAppId = document.getElementById('fbInputAppId');
        const btnResetFbConfig = document.getElementById('btnResetFbConfig');
        const btnSaveFbConfig = document.getElementById('btnSaveFbConfig');

        let isSignUpMode = false;

        // Modal openers & closers
        function openAuthModal(signup = false) {
            setAuthMode(signup);
            if (authErrorBanner) authErrorBanner.classList.add('hidden');
            if (authModal) authModal.classList.remove('hidden');
        }

        function closeAuthModal() {
            if (authModal) authModal.classList.add('hidden');
        }

        function openProfileModal() {
            updateProfileModalDetails();
            if (userProfileModal) userProfileModal.classList.remove('hidden');
        }

        function closeProfileModal() {
            if (userProfileModal) userProfileModal.classList.add('hidden');
        }

        function openFbSettingsModal() {
            populateFbSettingsUI();
            if (firebaseSettingsModal) firebaseSettingsModal.classList.remove('hidden');
        }

        function closeFbSettingsModal() {
            if (firebaseSettingsModal) firebaseSettingsModal.classList.add('hidden');
        }

        function setAuthMode(signup) {
            isSignUpMode = signup;
            if (authDialogTitle) authDialogTitle.textContent = signup ? 'Create SoundWave Account' : 'Log in to SoundWave';
            if (groupDisplayName) groupDisplayName.classList.toggle('hidden', !signup);
            if (authSubmitText) authSubmitText.textContent = signup ? 'Create Free Account' : 'Log In';
            if (authSwitchPrompt) authSwitchPrompt.textContent = signup ? 'Already have an account?' : "Don't have an account?";
            if (btnSwitchAuthMode) btnSwitchAuthMode.textContent = signup ? 'Log in' : 'Sign up for SoundWave';
            if (authErrorBanner) authErrorBanner.classList.add('hidden');
        }

        // Toggle Password Visibility
        if (btnTogglePassword && authPasswordInput) {
            btnTogglePassword.addEventListener('click', () => {
                const isPass = authPasswordInput.type === 'password';
                authPasswordInput.type = isPass ? 'text' : 'password';
                btnTogglePassword.textContent = isPass ? 'Hide' : 'Show';
            });
        }

        // Switch Login / Sign Up
        if (btnSwitchAuthMode) {
            btnSwitchAuthMode.addEventListener('click', () => {
                setAuthMode(!isSignUpMode);
            });
        }

        // Wire click triggers
        if (btnTopLogin) btnTopLogin.addEventListener('click', () => openAuthModal(false));
        if (btnUserProfile) btnUserProfile.addEventListener('click', openProfileModal);
        if (btnFirebasePill) btnFirebasePill.addEventListener('click', openFbSettingsModal);
        if (btnOpenFirebaseSettings) {
            btnOpenFirebaseSettings.addEventListener('click', () => {
                closeProfileModal();
                openFbSettingsModal();
            });
        }
        if (btnProfileGoPremium) {
            btnProfileGoPremium.addEventListener('click', () => {
                closeProfileModal();
                switchTab('premium');
            });
        }

        // Backdrop and close buttons
        if (btnAuthClose) btnAuthClose.addEventListener('click', closeAuthModal);
        if (authBackdrop) authBackdrop.addEventListener('click', closeAuthModal);
        if (btnProfileClose) btnProfileClose.addEventListener('click', closeProfileModal);
        if (userProfileBackdrop) userProfileBackdrop.addEventListener('click', closeProfileModal);
        if (btnFbSettingsClose) btnFbSettingsClose.addEventListener('click', closeFbSettingsModal);
        if (fbSettingsBackdrop) fbSettingsBackdrop.addEventListener('click', closeFbSettingsModal);

        // Google Sign-In button
        if (btnGoogleSignIn) {
            btnGoogleSignIn.addEventListener('click', async () => {
                if (!window.SoundWaveFirebase) return;
                btnGoogleSignIn.style.opacity = '0.6';
                btnGoogleSignIn.style.pointerEvents = 'none';

                try {
                    const res = await window.SoundWaveFirebase.loginWithGoogle();
                    btnGoogleSignIn.style.opacity = '1';
                    btnGoogleSignIn.style.pointerEvents = 'auto';

                    if (res.success) {
                        closeAuthModal();
                        const name = res.user.displayName || 'Music Fan';
                        showToast(`Welcome, ${name}! Logged in with Google 🎉`);
                        if (res.isDemoNotice) {
                            setTimeout(() => showToast(res.isDemoNotice), 2500);
                        }
                    } else {
                        if (authErrorBanner) {
                            authErrorBanner.textContent = res.error || 'Google Sign-In failed. Please try again.';
                            authErrorBanner.classList.remove('hidden');
                        }
                    }
                } catch (e) {
                    btnGoogleSignIn.style.opacity = '1';
                    btnGoogleSignIn.style.pointerEvents = 'auto';
                    if (authErrorBanner) {
                        authErrorBanner.textContent = e.message || 'Login error';
                        authErrorBanner.classList.remove('hidden');
                    }
                }
            });
        }

        // Email Form Submit
        if (authEmailForm) {
            authEmailForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const email = authEmailInput ? authEmailInput.value.trim() : '';
                const password = authPasswordInput ? authPasswordInput.value : '';
                const displayName = authDisplayName ? authDisplayName.value.trim() : '';

                if (!email || !password) {
                    if (authErrorBanner) {
                        authErrorBanner.textContent = 'Please enter both email and password.';
                        authErrorBanner.classList.remove('hidden');
                    }
                    return;
                }

                if (password.length < 6) {
                    if (authErrorBanner) {
                        authErrorBanner.textContent = 'Password must be at least 6 characters.';
                        authErrorBanner.classList.remove('hidden');
                    }
                    return;
                }

                // Show spinner
                if (authSubmitText) authSubmitText.textContent = isSignUpMode ? 'Creating...' : 'Logging in...';
                if (btnAuthSubmit) btnAuthSubmit.disabled = true;

                try {
                    let res;
                    if (isSignUpMode) {
                        res = await window.SoundWaveFirebase.signupWithEmail(email, password, displayName);
                    } else {
                        res = await window.SoundWaveFirebase.loginWithEmail(email, password);
                    }

                    if (authSubmitText) authSubmitText.textContent = isSignUpMode ? 'Create Free Account' : 'Log In';
                    if (btnAuthSubmit) btnAuthSubmit.disabled = false;

                    if (res && res.success) {
                        closeAuthModal();
                        showToast(isSignUpMode ? 'Account created! Welcome to SoundWave 🚀' : 'Logged in successfully! 🎵');
                        if (res.isDemoNotice) {
                            setTimeout(() => showToast(res.isDemoNotice), 2500);
                        }
                    } else {
                        if (authErrorBanner) {
                            authErrorBanner.textContent = (res && res.error) ? res.error : 'Authentication failed.';
                            authErrorBanner.classList.remove('hidden');
                        }
                    }
                } catch (err) {
                    if (authSubmitText) authSubmitText.textContent = isSignUpMode ? 'Create Free Account' : 'Log In';
                    if (btnAuthSubmit) btnAuthSubmit.disabled = false;
                    if (authErrorBanner) {
                        authErrorBanner.textContent = err.message || 'Error occurred';
                        authErrorBanner.classList.remove('hidden');
                    }
                }
            });
        }

        // Log out button
        if (btnLogoutUser) {
            btnLogoutUser.addEventListener('click', async () => {
                if (window.SoundWaveFirebase) {
                    await window.SoundWaveFirebase.logout();
                    closeProfileModal();
                    showToast('Logged out of SoundWave 👋');
                }
            });
        }

        // Manual Sync button
        if (btnManualSync) {
            btnManualSync.addEventListener('click', async () => {
                if (!window.SoundWaveFirebase) return;
                btnManualSync.textContent = 'Syncing... ⏳';
                const res = await window.SoundWaveFirebase.pushUserDataToCloud({
                    likedSongs: likedSongs,
                    subscription: getSubscription()
                });
                btnManualSync.textContent = '☁️ Sync All Data to Cloud Now';
                if (res && res.success) {
                    showToast(`Synced ${likedSongs.length} songs & VIP plan to Cloud! ☁️✨`);
                } else {
                    showToast('Sync updated locally. Connect Firebase for multi-device sync!');
                }
            });
        }

        // Update UI when Auth state changes
        if (window.SoundWaveFirebase) {
            window.SoundWaveFirebase.onAuthStateChanged((user) => {
                updateAuthStatusUI(user);
            });
        }

        function updateAuthStatusUI(user) {
            const isConfigured = window.SoundWaveFirebase ? window.SoundWaveFirebase.isConfigured : false;

            // Update Firebase status pill
            if (btnFirebasePill) {
                if (isConfigured) {
                    btnFirebasePill.classList.add('connected');
                    if (fbPillText) fbPillText.textContent = 'Cloud Live 🔥';
                } else {
                    btnFirebasePill.classList.remove('connected');
                    if (fbPillText) fbPillText.textContent = 'Firebase';
                }
            }

            if (user) {
                // User is logged in
                if (btnTopLogin) btnTopLogin.classList.add('hidden');
                if (btnUserProfile) btnUserProfile.classList.remove('hidden');

                const name = user.displayName || user.email?.split('@')[0] || 'User';
                const firstName = name.split(' ')[0];

                if (userAvatarLabel) userAvatarLabel.textContent = firstName;

                if (user.photoURL && userAvatarImg) {
                    userAvatarImg.src = user.photoURL;
                    userAvatarImg.classList.remove('hidden');
                    if (userAvatarIcon) userAvatarIcon.classList.add('hidden');
                } else {
                    if (userAvatarImg) userAvatarImg.classList.add('hidden');
                    if (userAvatarIcon) {
                        userAvatarIcon.classList.remove('hidden');
                        userAvatarIcon.textContent = '👤';
                    }
                }
            } else {
                // User is logged out
                if (btnTopLogin) btnTopLogin.classList.remove('hidden');
                if (btnUserProfile) btnUserProfile.classList.add('hidden');
            }

            updateProfileModalDetails();
        }

        function updateProfileModalDetails() {
            const user = window.SoundWaveFirebase ? window.SoundWaveFirebase.currentUser : null;
            const sub = getSubscription();
            const isConfigured = window.SoundWaveFirebase ? window.SoundWaveFirebase.isConfigured : false;

            if (profileNameDisplay) {
                profileNameDisplay.textContent = user ? (user.displayName || user.email?.split('@')[0] || 'Member') : 'Guest Listener';
            }

            if (profileEmailDisplay) {
                profileEmailDisplay.textContent = user ? (user.email || 'Signed in via Google') : 'Log in to sync across devices';
            }

            if (profileBigPhoto && profileBigEmoji) {
                if (user && user.photoURL) {
                    profileBigPhoto.src = user.photoURL;
                    profileBigPhoto.classList.remove('hidden');
                    profileBigEmoji.classList.add('hidden');
                } else {
                    profileBigPhoto.classList.add('hidden');
                    profileBigEmoji.classList.remove('hidden');
                    profileBigEmoji.textContent = sub.active ? '👑' : '🎧';
                }
            }

            if (profileMembershipPill) {
                profileMembershipPill.textContent = sub.active ? `👑 ${sub.planName || 'VIP Member'}` : '🎵 Free Plan';
            }

            if (profileSyncModePill) {
                profileSyncModePill.textContent = isConfigured ? 'Firestore Live 🟢' : 'Demo Mode 🟠';
            }

            if (syncLikedCount) {
                syncLikedCount.textContent = likedSongs.length;
            }
        }

        // Firebase Settings Modal Tabs & Save
        if (fbTabPaste && fbTabManual && fbPanePaste && fbPaneManual) {
            fbTabPaste.addEventListener('click', () => {
                fbTabPaste.classList.add('active');
                fbTabManual.classList.remove('active');
                fbPanePaste.classList.remove('hidden');
                fbPaneManual.classList.add('hidden');
            });

            fbTabManual.addEventListener('click', () => {
                fbTabManual.classList.add('active');
                fbTabPaste.classList.remove('active');
                fbPaneManual.classList.remove('hidden');
                fbPanePaste.classList.add('hidden');
            });
        }

        function populateFbSettingsUI() {
            if (!window.SoundWaveFirebase) return;
            const cfg = window.SoundWaveFirebase.getConfig();
            const isLive = window.SoundWaveFirebase.isConfigured;

            if (fbConnectionBanner) {
                fbConnectionBanner.classList.toggle('live', isLive);
            }
            if (bannerStatusTitle) {
                bannerStatusTitle.textContent = isLive ? 'Firebase Live Connected 🔥' : 'Firebase Ready to Connect';
            }
            if (bannerStatusDesc) {
                bannerStatusDesc.textContent = isLive ?
                    `Connected to project "${cfg.projectId}". All liked songs and subscriptions sync in realtime.` :
                    'Paste your Firebase project credentials below to enable live cloud sync.';
            }

            if (fbInputApiKey) fbInputApiKey.value = cfg.apiKey && !cfg.apiKey.includes('YOUR_API') ? cfg.apiKey : '';
            if (fbInputProjectId) fbInputProjectId.value = cfg.projectId && !cfg.projectId.includes('YOUR_PROJECT') ? cfg.projectId : '';
            if (fbInputAuthDomain) fbInputAuthDomain.value = cfg.authDomain || '';
            if (fbInputAppId) fbInputAppId.value = cfg.appId && !cfg.appId.includes('1234') ? cfg.appId : '';

            if (fbSnippetTextarea && !fbSnippetTextarea.value) {
                fbSnippetTextarea.value = JSON.stringify(cfg, null, 2);
            }
        }

        // Save Firebase Config
        if (btnSaveFbConfig) {
            btnSaveFbConfig.addEventListener('click', () => {
                if (!window.SoundWaveFirebase) return;

                let configObj = {};
                const isPasteTab = fbTabPaste && fbTabPaste.classList.contains('active');

                if (isPasteTab && fbSnippetTextarea) {
                    const text = fbSnippetTextarea.value.trim();
                    try {
                        // Extract JSON or regex from snippet
                        const apiKeyMatch = text.match(/apiKey["']?\s*:\s*["']([^"']+)["']/i);
                        const projIdMatch = text.match(/projectId["']?\s*:\s*["']([^"']+)["']/i);
                        const authDomainMatch = text.match(/authDomain["']?\s*:\s*["']([^"']+)["']/i);
                        const storageMatch = text.match(/storageBucket["']?\s*:\s*["']([^"']+)["']/i);
                        const senderIdMatch = text.match(/messagingSenderId["']?\s*:\s*["']([^"']+)["']/i);
                        const appIdMatch = text.match(/appId["']?\s*:\s*["']([^"']+)["']/i);

                        if (apiKeyMatch && projIdMatch) {
                            configObj = {
                                apiKey: apiKeyMatch[1],
                                projectId: projIdMatch[1],
                                authDomain: authDomainMatch ? authDomainMatch[1] : `${projIdMatch[1]}.firebaseapp.com`,
                                storageBucket: storageMatch ? storageMatch[1] : `${projIdMatch[1]}.appspot.com`,
                                messagingSenderId: senderIdMatch ? senderIdMatch[1] : '',
                                appId: appIdMatch ? appIdMatch[1] : ''
                            };
                        } else {
                            // Try direct JSON.parse
                            configObj = JSON.parse(text);
                        }
                    } catch (e) {
                        showToast('Please check your Firebase configuration snippet syntax!');
                        return;
                    }
                } else {
                    configObj = {
                        apiKey: fbInputApiKey ? fbInputApiKey.value.trim() : '',
                        projectId: fbInputProjectId ? fbInputProjectId.value.trim() : '',
                        authDomain: fbInputAuthDomain ? fbInputAuthDomain.value.trim() : '',
                        appId: fbInputAppId ? fbInputAppId.value.trim() : ''
                    };
                }

                if (!configObj.apiKey || !configObj.projectId) {
                    showToast('API Key and Project ID are required!');
                    return;
                }

                window.SoundWaveFirebase.saveConfig(configObj);
                closeFbSettingsModal();
                updateAuthStatusUI(window.SoundWaveFirebase.currentUser);
                showToast('Firebase configuration saved & connected! 🔥🎉');
            });
        }

        // Reset Firebase Config
        if (btnResetFbConfig) {
            btnResetFbConfig.addEventListener('click', () => {
                if (window.SoundWaveFirebase) {
                    window.SoundWaveFirebase.resetConfig();
                    populateFbSettingsUI();
                    showToast('Reset to demo configuration');
                }
            });
        }

        // Listen for Realtime Cloud Sync Events from Firestore
        window.addEventListener('soundwave:remote-data-sync', (e) => {
            if (!e.detail) return;
            let changesCount = 0;

            // Merge liked songs
            if (Array.isArray(e.detail.likedSongs)) {
                e.detail.likedSongs.forEach(remoteTrack => {
                    if (remoteTrack && remoteTrack.id && !likedSongs.some(t => t.id === remoteTrack.id)) {
                        likedSongs.unshift(remoteTrack);
                        changesCount++;
                    }
                });

                if (changesCount > 0) {
                    try {
                        localStorage.setItem(STORAGE_KEY_LIKED, JSON.stringify(likedSongs));
                    } catch (err) {}
                    updateLikedUI();
                    showToast(`☁️ Cloud Synced: ${changesCount} new liked ${changesCount === 1 ? 'song' : 'songs'} added!`);
                }
            }

            // Sync subscription
            if (e.detail.subscription && e.detail.subscription.active) {
                const currentSub = getSubscription();
                if (!currentSub.active || currentSub.expiresAt !== e.detail.subscription.expiresAt) {
                    try {
                        localStorage.setItem(STORAGE_KEY_SUB, JSON.stringify(e.detail.subscription));
                    } catch (err) {}
                    updateSubscriptionUI();
                }
            }
        });

        // Initial push if newly registered user has local liked songs
        window.addEventListener('soundwave:request-initial-push', () => {
            if (window.SoundWaveFirebase && likedSongs.length > 0) {
                window.SoundWaveFirebase.pushUserDataToCloud({
                    likedSongs: likedSongs,
                    subscription: getSubscription()
                });
            }
        });
    }

    // ==========================================================================
    // --- 24. MOVIES SECTION & VEGAMOVIES ENGINE ---
    // ==========================================================================
    let currentMovieGenre = 'action';
    let currentMovieLanguage = '';
    let currentMoviePage = 1;
    let isMoviesLoading = false;
    let spotlightMovieData = null;
    let movieSearchDebounceTimer = null;

    const movieSpotlightBanner = document.getElementById('movieSpotlightBanner');
    const spotlightTitle = document.getElementById('spotlightTitle');
    const spotlightRating = document.getElementById('spotlightRating');
    const spotlightYear = document.getElementById('spotlightYear');
    const spotlightGenre = document.getElementById('spotlightGenre');
    const spotlightDesc = document.getElementById('spotlightDesc');
    const spotlightPosterImg = document.getElementById('spotlightPosterImg');
    const btnSpotlightTrailer = document.getElementById('btnSpotlightTrailer');
    const btnSpotlightDetail = document.getElementById('btnSpotlightDetail');

    const movieSearchInput = document.getElementById('movieSearchInput');
    const movieSearchClear = document.getElementById('movieSearchClear');
    const movieChipsRow = document.getElementById('movieChipsRow');

    const moviesGridTitle = document.getElementById('moviesGridTitle');
    const moviesCountBadge = document.getElementById('moviesCountBadge');
    const moviesLoadingSpinner = document.getElementById('moviesLoadingSpinner');
    const moviesGrid = document.getElementById('moviesGrid');
    const moviesLoadMoreWrap = document.getElementById('moviesLoadMoreWrap');
    const btnMoviesLoadMore = document.getElementById('btnMoviesLoadMore');

    const movieDetailModal = document.getElementById('movieDetailModal');
    const movieDetailBackdrop = document.getElementById('movieDetailBackdrop');
    const btnMovieDetailClose = document.getElementById('btnMovieDetailClose');
    const movieDetailBody = document.getElementById('movieDetailBody');

    // Load Movies from Backend Scraper API
    async function loadMovies(genre, language, page = 1, append = false) {
        if (isMoviesLoading) return;
        isMoviesLoading = true;

        if (moviesLoadingSpinner) moviesLoadingSpinner.classList.remove('hidden');

        try {
            let url = `${API_BASE}/api/movies?page=${page}`;
            if (language) url += `&language=${encodeURIComponent(language)}`;
            else if (genre) url += `&genre=${encodeURIComponent(genre)}`;

            const res = await fetch(url);
            const data = await res.json();

            const movies = data.movies || [];

            if (!append && movies.length > 0) {
                // Update Spotlight with first high-rated movie
                updateSpotlightMovie(movies[0]);
            }

            renderMovieCards(movies, append);

            // Toggle Load More button
            if (moviesLoadMoreWrap) {
                if (data.has_next) {
                    moviesLoadMoreWrap.classList.remove('hidden');
                } else {
                    moviesLoadMoreWrap.classList.add('hidden');
                }
            }

            if (moviesCountBadge) {
                const totalRendered = moviesGrid ? moviesGrid.children.length : movies.length;
                moviesCountBadge.textContent = `${totalRendered} Movies available`;
            }

        } catch (err) {
            console.error('Failed to load movies:', err);
            showToast('Unable to load movies. Retrying...');
        } finally {
            isMoviesLoading = false;
            if (moviesLoadingSpinner) moviesLoadingSpinner.classList.add('hidden');
        }
    }

    // Update the Cinematic Spotlight Banner
    function updateSpotlightMovie(movie) {
        if (!movie) return;
        spotlightMovieData = movie;

        if (spotlightTitle) spotlightTitle.textContent = movie.title || 'Featured Movie';
        if (spotlightRating) spotlightRating.textContent = movie.rating ? `⭐ ${movie.rating} / 10` : '⭐ 8.0 / 10';
        if (spotlightYear) spotlightYear.textContent = movie.release || '2026';
        if (spotlightGenre) spotlightGenre.textContent = (currentMovieGenre || 'Action, Thriller').toUpperCase();
        if (spotlightPosterImg && movie.poster) spotlightPosterImg.src = movie.poster;

        // Fetch detail in background to enrich synopsis & trailer for spotlight
        if (movie.slug) {
            fetch(`${API_BASE}/api/movies/detail?slug=${encodeURIComponent(movie.slug)}`)
                .then(r => r.json())
                .then(det => {
                    if (det && !det.error) {
                        spotlightMovieData = det;
                        if (spotlightDesc && det.overview) {
                            spotlightDesc.textContent = det.overview;
                        }
                        if (spotlightGenre && det.genres) {
                            spotlightGenre.textContent = det.genres;
                        }
                    }
                })
                .catch(() => {});
        }
    }

    // Render Movie Poster Cards
    function renderMovieCards(movies, append = false) {
        if (!moviesGrid) return;
        if (!append) moviesGrid.innerHTML = '';

        if (!movies || movies.length === 0) {
            if (!append) {
                moviesGrid.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; padding: 3rem 1rem; color: #888;">
                        <p style="font-size: 1.1rem; margin-bottom: 8px;">No movies found in this category.</p>
                        <span style="font-size: 0.85rem;">Try another genre or search query above!</span>
                    </div>
                `;
            }
            return;
        }

        movies.forEach(movie => {
            const card = document.createElement('div');
            card.className = 'movie-card';
            card.setAttribute('data-slug', movie.slug || '');

            const posterUrl = movie.poster || movie.image || 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400';
            const ratingText = movie.rating && movie.rating !== 'N/A' ? `⭐ ${movie.rating}` : '⭐ HD';

            card.innerHTML = `
                <div class="movie-card-thumb-wrap">
                    <img src="${posterUrl}" alt="${escapeHtml(movie.title)}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400'">
                    <span class="movie-card-rating">${ratingText}</span>
                    <span class="movie-hd-badge">1080p Full HD</span>
                    <div class="movie-card-hover-actions">
                        <button class="btn-quick-trailer" title="Watch in 1080p Full HD">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="white">
                                <polygon points="6 3 20 12 6 21 6 3"></polygon>
                            </svg>
                            <span>Play 1080p</span>
                        </button>
                        <button class="btn-quick-info">
                            <span>More Info</span>
                        </button>
                    </div>
                </div>
                <div class="movie-card-info">
                    <h4 class="movie-card-title" title="${escapeHtml(movie.title)}">${escapeHtml(movie.title)}</h4>
                    <div class="movie-card-meta">
                        <span>${movie.release || 'Movie'}</span>
                        <span style="color: #e50914; font-weight: 700;">Cinema HD (1080p)</span>
                    </div>
                </div>
            `;

            // Hover trailer button
            const btnTrailer = card.querySelector('.btn-quick-trailer');
            if (btnTrailer) {
                btnTrailer.addEventListener('click', (e) => {
                    e.stopPropagation();
                    quickPlayMovieTrailer(movie.slug, movie.title);
                });
            }

            // Click entire card to open detail
            card.addEventListener('click', () => {
                openMovieDetailModal(movie.slug);
            });

            moviesGrid.appendChild(card);
        });
    }

    // Load Vegamovies shelf on Home Tab
    async function loadVegamoviesHomeShelf() {
        const homeGrid = document.getElementById('vegamoviesHomeGrid');
        if (!homeGrid) return;

        try {
            const res = await fetch(`${API_BASE}/api/movies?genre=action&page=1`);
            const data = await res.json();
            const movies = (data.movies || []).slice(0, 6);

            homeGrid.innerHTML = '';
            movies.forEach(movie => {
                const card = document.createElement('div');
                card.className = 'sp-card';
                card.style.cursor = 'pointer';

                const poster = movie.poster || 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400';
                card.innerHTML = `
                    <div class="card-art-box" style="position: relative;">
                        <img src="${poster}" alt="${escapeHtml(movie.title)}" loading="lazy">
                        <span class="movie-hd-badge">1080p</span>
                        <div class="card-play-hover">
                            <button class="card-green-play" title="Play in 1080p Full HD">
                                <svg viewBox="0 0 24 24" width="22" height="22" fill="white">
                                    <polygon points="6 3 20 12 6 21 6 3"></polygon>
                                </svg>
                            </button>
                        </div>
                    </div>
                    <div class="card-title-text" title="${escapeHtml(movie.title)}">${escapeHtml(movie.title)}</div>
                    <div class="card-artist-text">⭐ ${movie.rating || '8.0'} • Cinema HD (1080p)</div>
                `;

                const playBtn = card.querySelector('.card-green-play');
                if (playBtn) {
                    playBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        quickPlayMovieTrailer(movie.slug, movie.title);
                    });
                }

                card.addEventListener('click', () => {
                    openMovieDetailModal(movie.slug);
                });

                homeGrid.appendChild(card);
            });
        } catch (e) {
            console.log('Failed to load home vegamovies shelf:', e);
        }
    }

    // Play Movie Trailer directly
    async function quickPlayMovieTrailer(slug, title) {
        if (!slug) return;
        showToast(`Loading 1080p Full HD stream: ${title || 'Movie'}...`);

        currentVideoQuality = '1080p';
        localStorage.setItem('soundwave_video_quality', '1080p');
        const ytQualitySelect = document.getElementById('ytQualitySelect');
        const ytQualityBadge = document.getElementById('ytQualityBadge');
        if (ytQualitySelect) ytQualitySelect.value = '1080p';
        if (ytQualityBadge) ytQualityBadge.textContent = '1080p';

        try {
            const res = await fetch(`${API_BASE}/api/movies/detail?slug=${encodeURIComponent(slug)}`);
            const detail = await res.json();

            if (detail && detail.trailer_id) {
                switchTab('video');
                playYouTubeVideo(detail.trailer_id, `${detail.title} (1080p Full HD)`, 'Cinema Vault 1080p');
            } else {
                switchTab('video');
                const ytQuery = `${title} Official Movie 1080p`;
                loadYouTubeVideos(ytQuery);
                showToast(`Searching 1080p Video: ${title}`);
            }
        } catch (err) {
            console.error('Trailer error:', err);
            switchTab('video');
            loadYouTubeVideos(`${title} 1080p`);
        }
    }

    // Open Full Movie Detail Modal
    async function openMovieDetailModal(slug) {
        if (!slug || !movieDetailModal || !movieDetailBody) return;

        // Show modal with loading spinner
        movieDetailBody.innerHTML = `
            <div style="text-align: center; padding: 4rem 2rem;">
                <div class="sp-spinner" style="margin: 0 auto 16px;"></div>
                <p style="color: #fff; font-weight: 700;">Fetching 1080p movie details from Cinema Vault...</p>
            </div>
        `;
        movieDetailModal.classList.remove('hidden');

        try {
            const res = await fetch(`${API_BASE}/api/movies/detail?slug=${encodeURIComponent(slug)}`);
            const detail = await res.json();

            if (detail.error) throw new Error(detail.error);

            const posterUrl = detail.poster || 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400';
            const ratingPill = detail.rating && detail.rating !== 'N/A' ? `<span class="movie-pill movie-pill-rating">⭐ ${detail.rating}</span>` : '';
            const hdPill = `<span class="movie-pill" style="background: rgba(229,9,20,0.2); color: #ff4d4d; border-color: rgba(229,9,20,0.4); font-weight:800;">⚡ 1080p Full HD</span>`;
            const releasePill = detail.release ? `<span class="movie-pill">📅 ${escapeHtml(detail.release)}</span>` : '';
            const runtimePill = detail.runtime ? `<span class="movie-pill">⏱️ ${escapeHtml(detail.runtime)}</span>` : '';
            const genrePill = detail.genres ? `<span class="movie-pill">🎭 ${escapeHtml(detail.genres)}</span>` : '';

            // Cast HTML
            let castHtml = '';
            if (detail.cast && detail.cast.length > 0) {
                castHtml = `
                    <h4 class="movie-modal-section-title">Top Cast</h4>
                    <div class="movie-cast-carousel">
                        ${detail.cast.map(c => `
                            <div class="cast-card-item">
                                <div class="cast-avatar-box">
                                    <img src="${c.image || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120'}" alt="${escapeHtml(c.name)}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120'">
                                </div>
                                <span class="cast-actor-name" title="${escapeHtml(c.name)}">${escapeHtml(c.name)}</span>
                                <span class="cast-char-name" title="${escapeHtml(c.character)}">${escapeHtml(c.character)}</span>
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            movieDetailBody.innerHTML = `
                <div class="movie-modal-hero">
                    <div class="movie-modal-poster">
                        <img src="${posterUrl}" alt="${escapeHtml(detail.title)}" onerror="this.src='https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400'">
                    </div>
                    <div class="movie-modal-info">
                        <h2 class="movie-modal-title">${escapeHtml(detail.title)}</h2>
                        ${detail.tagline ? `<p class="movie-modal-tagline">"${escapeHtml(detail.tagline)}"</p>` : ''}
                        <div class="movie-pills-row">
                            ${hdPill}
                            ${ratingPill}
                            ${releasePill}
                            ${runtimePill}
                            ${genrePill}
                        </div>
                        <div class="movie-modal-actions">
                            <button class="btn-modal-trailer" id="btnModalPlayTrailer">
                                <svg viewBox="0 0 24 24" width="18" height="18" fill="white">
                                    <polygon points="6 3 20 12 6 21 6 3"></polygon>
                                </svg>
                                <span>Watch in 1080p Full HD</span>
                            </button>
                            <button class="btn-modal-full-movie" id="btnModalSearchFullMovie">
                                <svg viewBox="0 0 24 24" width="18" height="18" fill="#e50914">
                                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/>
                                </svg>
                                <span>Watch Full Movie (1080p)</span>
                            </button>
                            <a href="${detail.vegamovies_url || `https://vegamovie.website/movie/${slug}/`}" target="_blank" rel="noopener" class="btn-modal-vegamovies">
                                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                    <polyline points="15 3 21 3 21 9"></polyline>
                                    <line x1="10" y1="14" x2="21" y2="3"></line>
                                </svg>
                                <span>View Source Page</span>
                            </a>
                        </div>
                    </div>
                </div>

                <h4 class="movie-modal-section-title">Storyline & Synopsis</h4>
                <p class="movie-overview-text">${escapeHtml(detail.overview || 'Synopsis not available for this movie.')}</p>

                ${detail.director ? `
                    <div class="movie-director-row">
                        <strong>Director:</strong> ${escapeHtml(detail.director)}
                    </div>
                ` : ''}

                ${castHtml}
            `;

            // Wire Trailer Play Button
            const btnPlay = document.getElementById('btnModalPlayTrailer');
            if (btnPlay) {
                btnPlay.addEventListener('click', () => {
                    movieDetailModal.classList.add('hidden');
                    currentVideoQuality = '1080p';
                    localStorage.setItem('soundwave_video_quality', '1080p');
                    if (detail.trailer_id) {
                        switchTab('video');
                        playYouTubeVideo(detail.trailer_id, `${detail.title} (1080p Full HD)`, 'Cinema Vault 1080p');
                    } else {
                        switchTab('video');
                        loadYouTubeVideos(`${detail.title} Official Trailer 1080p`);
                    }
                });
            }

            // Wire Full Movie Watch Button
            const btnFullMovie = document.getElementById('btnModalSearchFullMovie');
            if (btnFullMovie) {
                btnFullMovie.addEventListener('click', () => {
                    movieDetailModal.classList.add('hidden');
                    currentVideoQuality = '1080p';
                    localStorage.setItem('soundwave_video_quality', '1080p');
                    switchTab('video');
                    const query = `${detail.title} Full Movie Hindi 1080p`;
                    loadYouTubeVideos(query);
                    showToast(`Searching 1080p full movie: ${detail.title}`);
                });
            }

        } catch (err) {
            console.error('Modal error:', err);
            movieDetailBody.innerHTML = `
                <div style="text-align: center; padding: 3rem 1.5rem; color: #ff6b6b;">
                    <p style="font-size: 1.1rem; margin-bottom: 10px;">Failed to load movie details.</p>
                    <button class="btn-prem-view-plans" onclick="document.getElementById('movieDetailModal').classList.add('hidden')">Close</button>
                </div>
            `;
        }
    }

    // Live Search on Vegamovies
    async function searchVegamovies(query) {
        if (!query || !query.trim()) {
            if (moviesGridTitle) moviesGridTitle.textContent = `${(currentMovieGenre || 'Action').toUpperCase()} Movies`;
            loadMovies(currentMovieGenre, currentMovieLanguage, 1);
            return;
        }

        if (moviesLoadingSpinner) moviesLoadingSpinner.classList.remove('hidden');
        if (moviesGridTitle) moviesGridTitle.textContent = `Search results for "${query}"`;
        if (moviesLoadMoreWrap) moviesLoadMoreWrap.classList.add('hidden');

        try {
            const res = await fetch(`${API_BASE}/api/movies/search?q=${encodeURIComponent(query)}`);
            const data = await res.json();
            renderMovieCards(data.results || [], false);

            if (moviesCountBadge) {
                const count = (data.results || []).length;
                moviesCountBadge.textContent = `${count} Movies found`;
            }
        } catch (err) {
            console.error('Movie search error:', err);
            showToast('Search failed. Please try again.');
        } finally {
            if (moviesLoadingSpinner) moviesLoadingSpinner.classList.add('hidden');
        }
    }

    // Wire Movies Listeners
    if (btnSpotlightTrailer) {
        btnSpotlightTrailer.addEventListener('click', () => {
            if (spotlightMovieData) {
                quickPlayMovieTrailer(spotlightMovieData.slug, spotlightMovieData.title);
            }
        });
    }

    if (btnSpotlightDetail) {
        btnSpotlightDetail.addEventListener('click', () => {
            if (spotlightMovieData && spotlightMovieData.slug) {
                openMovieDetailModal(spotlightMovieData.slug);
            }
        });
    }

    // Category / Genre chips
    if (movieChipsRow) {
        const chips = movieChipsRow.querySelectorAll('.movie-chip');
        chips.forEach(chip => {
            chip.addEventListener('click', () => {
                chips.forEach(c => c.classList.remove('active'));
                chip.classList.add('active');

                const type = chip.getAttribute('data-type');
                const val = chip.getAttribute('data-val');

                currentMoviePage = 1;
                if (movieSearchInput) movieSearchInput.value = '';
                if (movieSearchClear) movieSearchClear.classList.add('hidden');

                if (type === 'language') {
                    currentMovieLanguage = val;
                    currentMovieGenre = '';
                    if (moviesGridTitle) moviesGridTitle.textContent = `${chip.textContent.trim()} (Vegamovies)`;
                } else {
                    currentMovieGenre = val;
                    currentMovieLanguage = '';
                    if (moviesGridTitle) moviesGridTitle.textContent = `${chip.textContent.trim()} Movies (Vegamovies)`;
                }

                loadMovies(currentMovieGenre, currentMovieLanguage, 1);
            });
        });
    }

    // Search input
    if (movieSearchInput) {
        movieSearchInput.addEventListener('input', (e) => {
            const val = e.target.value.trim();
            if (movieSearchClear) {
                movieSearchClear.classList.toggle('hidden', val.length === 0);
            }

            if (movieSearchDebounceTimer) clearTimeout(movieSearchDebounceTimer);
            movieSearchDebounceTimer = setTimeout(() => {
                searchVegamovies(val);
            }, 350);
        });
    }

    if (movieSearchClear) {
        movieSearchClear.addEventListener('click', () => {
            if (movieSearchInput) movieSearchInput.value = '';
            movieSearchClear.classList.add('hidden');
            searchVegamovies('');
        });
    }

    // Load More Button
    if (btnMoviesLoadMore) {
        btnMoviesLoadMore.addEventListener('click', () => {
            currentMoviePage++;
            loadMovies(currentMovieGenre, currentMovieLanguage, currentMoviePage, true);
        });
    }

    // Modal close events
    if (btnMovieDetailClose) {
        btnMovieDetailClose.addEventListener('click', () => {
            if (movieDetailModal) movieDetailModal.classList.add('hidden');
        });
    }

    if (movieDetailBackdrop) {
        movieDetailBackdrop.addEventListener('click', () => {
            if (movieDetailModal) movieDetailModal.classList.add('hidden');
        });
    }
});





    // DMCA Legal Modal Listeners
    const btnOpenDmca = document.getElementById('btnOpenDmcaModal');
    const dmcaModal = document.getElementById('dmcaModal');
    const btnCloseDmca = document.getElementById('btnCloseDmcaModal');
    const btnAckDmca = document.getElementById('btnAcknowledgeDmca');

    if (btnOpenDmca && dmcaModal) {
        btnOpenDmca.addEventListener('click', () => dmcaModal.classList.remove('hidden'));
    }
    if (btnCloseDmca && dmcaModal) {
        btnCloseDmca.addEventListener('click', () => dmcaModal.classList.add('hidden'));
    }
    if (btnAckDmca && dmcaModal) {
        btnAckDmca.addEventListener('click', () => dmcaModal.classList.add('hidden'));
    }
    

    // Side Nav Sports Button Listener
    const sideNavSports = document.getElementById('sideNavSports');
    if (sideNavSports) {
        sideNavSports.addEventListener('click', () => {
            switchTab('video');
            loadYouTubeVideos('Live Sports Cricket Football Highlights 4K');
            const ytIn = document.getElementById('ytSearchInput');
            if (ytIn) ytIn.value = 'Live Sports Highlights 4K';
            document.querySelectorAll('.yt-chip').forEach(c => {
                c.classList.toggle('active', (c.getAttribute('data-q') || '').includes('Sports'));
            });
            showToast('Loading Live Sports & Highlights...');
        });
    }


    // =========================================================================
    // TOP 4 FEATURES IMPLEMENTATION:
    // 1. Ambient Glow Mode
    // 2. Infinite Autoplay Queue
    // 3. Picture-in-Picture (PiP / Floating Mini-Player)
    // 4. Playback Speed Controller (Audio & Video)
    // =========================================================================

    let isAmbientGlowEnabled = true;
    let isAutoplayEnabled = true;
    let currentPlaybackSpeed = 1.0;
    const SPEED_CYCLE = [0.75, 1.0, 1.25, 1.5, 2.0];

    // -------------------------------------------------------------
    // FEATURE 1: AMBIENT GLOW MODE
    // -------------------------------------------------------------
    const ambientGlowEl = document.getElementById('ambientGlow');
    const btnAmbientToggle = document.getElementById('btnAmbientToggle');

    function updateAmbientGlowColor(color1 = '#1db954', color2 = '#10b981') {
        if (!ambientGlowEl) return;
        ambientGlowEl.style.background = `radial-gradient(circle at center, ${color1} 0%, ${color2} 40%, transparent 70%)`;
    }

    if (btnAmbientToggle && ambientGlowEl) {
        btnAmbientToggle.addEventListener('click', () => {
            isAmbientGlowEnabled = !isAmbientGlowEnabled;
            ambientGlowEl.classList.toggle('disabled', !isAmbientGlowEnabled);
            btnAmbientToggle.classList.toggle('active-feature', isAmbientGlowEnabled);
            btnAmbientToggle.innerHTML = `<span>✨ Ambient Glow: ${isAmbientGlowEnabled ? 'ON' : 'OFF'}</span>`;
            showToast(`Ambient Glow: ${isAmbientGlowEnabled ? 'ON' : 'OFF'}`);
        });
    }

    // -------------------------------------------------------------
    // FEATURE 2: INFINITE AUTOPLAY QUEUE ("UP NEXT" ENGINE)
    // -------------------------------------------------------------
    const btnAutoplayToggle = document.getElementById('btnAutoplayToggle');
    let isFetchingAutoplay = false;

    if (btnAutoplayToggle) {
        btnAutoplayToggle.addEventListener('click', () => {
            isAutoplayEnabled = !isAutoplayEnabled;
            btnAutoplayToggle.classList.toggle('active-feature', isAutoplayEnabled);
            btnAutoplayToggle.innerHTML = `<span>♾️ Autoplay: ${isAutoplayEnabled ? 'ON' : 'OFF'}</span>`;
            showToast(`Autoplay: ${isAutoplayEnabled ? 'ON (Never Stops)' : 'OFF'}`);
        });
    }

    // Enhanced playNext with Infinite Autoplay recommendation
    const originalPlayNext = playNext;
    playNext = async function() {
        if (activeQueue.length === 0) return;
        
        let nextIndex = currentTrackIndex + 1;
        if (nextIndex < activeQueue.length) {
            playTrackByIndex(nextIndex);
            return;
        }

        // When queue reaches end, fetch new related tracks automatically!
        if (isAutoplayEnabled && !isFetchingAutoplay) {
            isFetchingAutoplay = true;
            const currentTrack = activeQueue[currentTrackIndex] || activeQueue[0];
            const seedQuery = currentTrack ? `${currentTrack.channel} top songs hits` : 'Trending Songs 2024';
            showToast('♾️ Autoplay: Loading related tracks...');

            try {
                const res = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(seedQuery)}`);
                const data = await res.json();
                if (data.results && data.results.length > 0) {
                    const newTracks = data.results.filter(r => !activeQueue.some(q => q.id === r.id));
                    if (newTracks.length > 0) {
                        activeQueue.push(...newTracks.slice(0, 8));
                        playTrackByIndex(nextIndex);
                        isFetchingAutoplay = false;
                        return;
                    }
                }
            } catch (err) {
                console.warn('Autoplay fetch failed:', err);
            }
            isFetchingAutoplay = false;
        }

        // Fallback loop if autoplay fails
        playTrackByIndex(0);
    };

    // Video Autoplay: When a video finishes, auto-play next video in grid
    const ytNativeVideoForAutoplay = document.getElementById('ytNativeVideo');
    if (ytNativeVideoForAutoplay) {
        ytNativeVideoForAutoplay.addEventListener('ended', () => {
            if (!isAutoplayEnabled) return;
            const videoCards = document.querySelectorAll('.yt-video-card');
            if (videoCards.length > 1) {
                const randomNext = videoCards[Math.floor(Math.random() * videoCards.length)];
                if (randomNext) {
                    showToast('♾️ Autoplay: Playing next video...');
                    randomNext.click();
                }
            }
        });
    }

    // -------------------------------------------------------------
    // FEATURE 3: PICTURE-IN-PICTURE (PiP) & FLOATING MINI-PLAYER
    // -------------------------------------------------------------
    const btnTogglePip = document.getElementById('btnTogglePip');
    const floatingMiniPlayer = document.getElementById('floatingMiniPlayer');
    const miniPlayerBody = document.getElementById('miniPlayerBody');
    const miniPlayerTitle = document.getElementById('miniPlayerTitle');
    const btnMiniClose = document.getElementById('btnMiniClose');
    const btnMiniExpand = document.getElementById('btnMiniExpand');
    const ytVideoWrapper = document.getElementById('ytVideoWrapper');

    async function togglePiPMode() {
        const vid = document.getElementById('ytNativeVideo');
        if (vid && !vid.classList.contains('hidden') && document.pictureInPictureEnabled) {
            try {
                if (document.pictureInPictureElement) {
                    await document.exitPictureInPicture();
                } else if (vid.readyState >= 1) {
                    await vid.requestPictureInPicture();
                    showToast('Picture-in-Picture Activated');
                    return;
                }
            } catch (err) {
                console.warn('Native PiP failed, using in-app floating player:', err);
            }
        }
        toggleFloatingMiniPlayer();
    }

    function toggleFloatingMiniPlayer(forceOpen = null) {
        if (!floatingMiniPlayer || !ytVideoWrapper) return;
        const shouldOpen = forceOpen !== null ? forceOpen : floatingMiniPlayer.classList.contains('hidden');

        if (shouldOpen) {
            if (miniPlayerTitle) miniPlayerTitle.textContent = currentActiveVideoTitle || 'SoundWave Video';
            if (miniPlayerBody && ytVideoWrapper) {
                miniPlayerBody.appendChild(ytVideoWrapper);
            }
            floatingMiniPlayer.classList.remove('hidden');
            showToast('Mini Player Floating');
        } else {
            const theaterStage = document.getElementById('ytPlayerTheater');
            if (theaterStage && ytVideoWrapper) {
                theaterStage.insertBefore(ytVideoWrapper, theaterStage.querySelector('.yt-video-meta-bar'));
            }
            floatingMiniPlayer.classList.add('hidden');
        }
    }

    if (btnTogglePip) {
        btnTogglePip.addEventListener('click', togglePiPMode);
    }
    if (btnMiniClose) {
        btnMiniClose.addEventListener('click', () => toggleFloatingMiniPlayer(false));
    }
    if (btnMiniExpand) {
        btnMiniExpand.addEventListener('click', () => {
            toggleFloatingMiniPlayer(false);
            switchTab('video');
        });
    }

    // Auto-float mini-player when user navigates away from video tab while video is playing!
    const originalSwitchTab = switchTab;
    switchTab = function(tabName, addToHistory = true) {
        const vid = document.getElementById('ytNativeVideo');
        const isVideoPlaying = vid && !vid.paused && !vid.classList.contains('hidden');

        if (tabName !== 'video' && isVideoPlaying) {
            toggleFloatingMiniPlayer(true);
        } else if (tabName === 'video' && floatingMiniPlayer && !floatingMiniPlayer.classList.contains('hidden')) {
            toggleFloatingMiniPlayer(false);
        }

        originalSwitchTab(tabName, addToHistory);
    };

    // -------------------------------------------------------------
    // FEATURE 4: PLAYBACK SPEED CONTROLLER (AUDIO & VIDEO)
    // -------------------------------------------------------------
    const btnVideoSpeed = document.getElementById('btnVideoSpeed');
    const btnAudioSpeed = document.getElementById('btnAudioSpeed');

    function applyPlaybackSpeed(newSpeed) {
        currentPlaybackSpeed = newSpeed;
        if (audio) audio.playbackRate = newSpeed;
        const vid = document.getElementById('ytNativeVideo');
        if (vid) vid.playbackRate = newSpeed;

        if (btnVideoSpeed) btnVideoSpeed.innerHTML = `<span>⚡ ${newSpeed}x</span>`;
        if (btnAudioSpeed) btnAudioSpeed.textContent = `${newSpeed}x`;
        showToast(`Speed: ${newSpeed}x`);
    }

    function cycleSpeed() {
        const currIdx = SPEED_CYCLE.indexOf(currentPlaybackSpeed);
        const nextIdx = (currIdx + 1) % SPEED_CYCLE.length;
        applyPlaybackSpeed(SPEED_CYCLE[nextIdx]);
    }

    if (btnVideoSpeed) {
        btnVideoSpeed.addEventListener('click', cycleSpeed);
    }
    if (btnAudioSpeed) {
        btnAudioSpeed.addEventListener('click', cycleSpeed);
    }

    // Apply speed automatically whenever a new audio or video starts
    if (audio) {
        audio.addEventListener('play', () => {
            audio.playbackRate = currentPlaybackSpeed;
        });
    }
    const nativeVidForSpeed = document.getElementById('ytNativeVideo');
    if (nativeVidForSpeed) {
        nativeVidForSpeed.addEventListener('play', () => {
            nativeVidForSpeed.playbackRate = currentPlaybackSpeed;
        });
    }


    // --- 25. BROWSE MORE TRENDING SONGS SYSTEM ---
    const TRENDING_QUERIES = [
        'Trending Hindi Punjabi Songs 2024 Hits',
        'Top Bollywood Most Viewed Songs All Time',
        'Arijit Singh Best Songs Hits',
        'Top Global Viral Songs Billion Views',
        'Latest Punjabi Video Songs 4K',
        'Best Romantic Bollywood Songs 1080p',
        'Top Lo-Fi Aesthetic Music Videos',
        'Bhangra & Dance Party Hits Video'
    ];
    let currentTrendingQueryIndex = 0;

    const btnBrowseMore = document.getElementById('btnBrowseMoreVideos');
    if (btnBrowseMore) {
        btnBrowseMore.addEventListener('click', async () => {
            currentTrendingQueryIndex = (currentTrendingQueryIndex + 1) % TRENDING_QUERIES.length;
            const nextQuery = TRENDING_QUERIES[currentTrendingQueryIndex];
            const originalText = 'Browse More Trending Songs ▾';
            btnBrowseMore.innerHTML = `
                <div class="sp-spinner" style="width:16px;height:16px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:8px;"></div>
                <span>Loading more viral hits...</span>
            `;
            showToast(`Loading: ${nextQuery}`);

            try {
                const res = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(nextQuery)}`);
                const data = await res.json();
                const grid = document.getElementById('ytVideosGrid');
                if (data.results && data.results.length > 0 && grid) {
                    const firstNewIdx = grid.children.length;
                    renderYtVideoCards(data.results, grid, true);
                    btnBrowseMore.innerHTML = `<span>${originalText}</span>`;
                    showToast(`Added ${data.results.length} more trending hits!`);
                    if (grid.children[firstNewIdx]) {
                        grid.children[firstNewIdx].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                } else {
                    btnBrowseMore.innerHTML = `<span>${originalText}</span>`;
                    showToast('No additional hits found.');
                }
            } catch (err) {
                console.warn('Browse more error:', err);
                btnBrowseMore.innerHTML = `<span>${originalText}</span>`;
                showToast('Unable to load more. Retrying...');
            }
        });
    }

    // -------------------------------------------------------------
    // FEATURE: HOME BROWSE MORE TRENDING HITS (Endless Shelves)
    // -------------------------------------------------------------
    const HOME_BROWSE_QUERIES = [
        { title: '🔥 Punjabi Viral Banger Hits', query: 'Top Punjabi Viral Songs 2024 Hits' },
        { title: '⚡ Bollywood Dance Party Hits', query: 'Bollywood High Energy Dance Songs Party' },
        { title: '👑 Global Viral Top 50', query: 'Global Viral Top 50 Songs 2024' },
        { title: '🌸 90s Evergreen Bollywood Hits', query: 'Best of 90s Bollywood Evergreen Songs' },
        { title: '🎧 Desi Hip-Hop & Rap Anthems', query: 'Top Indian Hip Hop Rap Songs Hits' },
        { title: '🌙 Late Night Acoustic & Chill', query: 'Late Night Acoustic Hindi Songs Relax' }
    ];
    let homeBrowseIndex = 0;

    const btnHomeBrowseMore = document.getElementById('btnHomeBrowseMore');
    const homeDynamicShelves = document.getElementById('homeDynamicShelves');

    if (btnHomeBrowseMore && homeDynamicShelves) {
        btnHomeBrowseMore.addEventListener('click', async () => {
            const currentItem = HOME_BROWSE_QUERIES[homeBrowseIndex % HOME_BROWSE_QUERIES.length];
            homeBrowseIndex++;

            const originalBtnContent = btnHomeBrowseMore.innerHTML;
            btnHomeBrowseMore.innerHTML = `
                <div class="sp-spinner" style="width:16px;height:16px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:8px;"></div>
                <span>Loading ${currentItem.title}...</span>
            `;
            showToast(`Loading: ${currentItem.title}`);

            try {
                const shelfDiv = document.createElement('div');
                shelfDiv.className = 'music-shelf';
                shelfDiv.style.marginTop = '2rem';
                shelfDiv.innerHTML = `
                    <div class="shelf-head">
                        <h2>${currentItem.title}</h2>
                        <button class="shelf-more-btn" data-query="${escapeHtml(currentItem.query)}">Show all</button>
                    </div>
                    <div class="shelf-cards-grid">
                        <div style="grid-column: 1/-1; padding: 2rem 0; text-align: center; color: var(--sp-text-mute);">
                            <div class="sp-spinner" style="margin: 0 auto 10px;"></div>
                            <span style="font-size: 0.85rem;">Loading tracks...</span>
                        </div>
                    </div>
                `;
                homeDynamicShelves.appendChild(shelfDiv);

                const moreBtn = shelfDiv.querySelector('.shelf-more-btn');
                if (moreBtn) {
                    moreBtn.addEventListener('click', () => {
                        switchTab('search');
                        if (searchPageViewInput) searchPageViewInput.value = currentItem.query;
                        triggerSearch(currentItem.query);
                    });
                }

                const shelfGrid = shelfDiv.querySelector('.shelf-cards-grid');
                const res = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(currentItem.query)}`);
                const data = await res.json();

                if (data.results && data.results.length > 0) {
                    renderCardGrid(data.results.slice(0, 8), shelfGrid);
                    showToast(`Added: ${currentItem.title}`);
                    shelfDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                } else {
                    shelfGrid.innerHTML = `<p style="color: var(--sp-text-mute); font-size: 0.85rem;">No tracks found.</p>`;
                }
            } catch (err) {
                console.error('Home browse more error:', err);
                showToast('Failed to load shelf. Please retry.');
            } finally {
                btnHomeBrowseMore.innerHTML = `<span>Browse More Trending Hits ▾</span>`;
            }
        });
    }

    // Auto-load trending videos when page boots or when video tab is shown
    document.addEventListener('DOMContentLoaded', () => {
        loadYouTubeVideos('Trending Music Videos 2024');
    });
    // Call immediately if DOM already loaded
    setTimeout(() => {
        const grid = document.getElementById('ytVideosGrid');
        if (grid && grid.children.length === 0) {
            loadYouTubeVideos('Trending Music Videos 2024');
        }
    }, 500);
