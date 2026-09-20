// IF Hub Theme System
// Themes modeled after platforms Infocom shipped Z-machine games on

// Canonical retro font URL (shared by all theme callers)
var RETRO_FONTS_URL = 'https://fonts.googleapis.com/css2?family=DotGothic16&family=Pixelify+Sans&family=Press+Start+2P&family=Silkscreen&family=Sixtyfour&family=Tiny5&family=VT323&family=Workbench&display=swap';

// Load retro platform fonts into a document (defaults to current document)
function ensureRetroFonts(doc) {
    doc = doc || document;
    try {
        if (doc.getElementById('retro-platform-fonts')) return;
        var link = doc.createElement('link');
        link.id = 'retro-platform-fonts';
        link.rel = 'stylesheet';
        link.href = RETRO_FONTS_URL;
        doc.head.appendChild(link);
    } catch(e) {}
}

// Load fonts eagerly for current page
ensureRetroFonts();

var THEMES = [
    {
        id: 'classic', name: 'Classic',
        chrome: {
            pageBg: '#0a0a0a', pageFg: '#d4c5a9', headingFg: '#e8d8b0',
            accentFg: '#e8d090', mutedFg: '#aa9966', dimFg: '#9a8a6a',
            cardBg: '#111', cardBorder: '#1e1a14', toolbarBg: '#0e0a08',
            border: '#2a2418', borderHover: '#3a2a18', surfaceBg: '#1a1410',
            btnBg: '#e8d090', btnFg: '#0a0a0a', btnHoverBg: '#f0d890',
            inputBg: '#110a08', inputFg: '#e8d090',
            activeTabBg: '#e8d090', activeTabFg: '#0a0a0a',
            badgeBg: '#1a1814', badgeFg: '#938059',
            codeBg: '#1a1410', codeFg: '#e8d090',
            footerFg: '#887856', linkFg: '#aa9966',
            fontFamily: 'Georgia, "Times New Roman", serif'
        },
        game: {
            bodyBg: '#111', bufferBg: '#111', bufferFg: '#d4c5a9',
            gridBg: '#1c1810', gridFg: '#aa9966',
            inputFg: '#e8d090', emphFg: '#e8d8b0', headerFg: '#e8d8b0',
            bufferSize: '16px', bufferLineHeight: '1.6',
            gridSize: '14px', gridLineHeight: '20px',
            monoFamily: '"SF Mono", "Fira Code", "Cascadia Code", Consolas, "Courier New", monospace',
            propFamily: '"Iowan Old Style", Palatino, Georgia, "Times New Roman", serif'
        },
        // the hub’s own source colors, which this background was built for
        syntax: {
            kw: '#c08050', str: '#8bab6e', cmt: '#6d6248', sub: '#7ea8b0',
            head: '#e0c8a0', rule: '#b89860', num: '#b08a70', tbl: '#9090b0'
        },
        scrollbar: { thumb: '#3a3020', track: '#111', thumbHover: '#5a4a30' }
    },
    {
        id: 'dos', name: 'MS-DOS',
        chrome: {
            pageBg: '#000000', pageFg: '#aaaaaa', headingFg: '#ffffff',
            accentFg: '#55ffff', mutedFg: '#9a9a9a', dimFg: '#767676',
            cardBg: '#0000aa', cardBorder: '#aaaaaa', toolbarBg: '#0000aa',
            border: '#555555', borderHover: '#aaaaaa', surfaceBg: '#0000aa',
            btnBg: '#aaaaaa', btnFg: '#000000', btnHoverBg: '#ffffff',
            inputBg: '#000000', inputFg: '#aaaaaa',
            activeTabBg: '#aaaaaa', activeTabFg: '#000000',
            badgeBg: '#0000aa', badgeFg: '#ffff55',
            codeBg: '#0000aa', codeFg: '#ffff55',
            footerFg: '#767676', linkFg: '#55ffff',
            fontFamily: '"VT323", "Consolas", "Courier New", monospace'
        },
        game: {
            bodyBg: '#000', bufferBg: '#000', bufferFg: '#aaa',
            gridBg: '#aaa', gridFg: '#000',
            inputFg: '#ffffff', emphFg: '#ffff55', headerFg: '#ffffff',
            bufferSize: '20px', bufferLineHeight: '1.25',
            gridSize: '20px', gridLineHeight: '24px',
            monoFamily: '"VT323", "Consolas", "Courier New", monospace',
            propFamily: '"VT323", "Consolas", "Courier New", monospace'
        },
        // CGA on Norton blue
        syntax: {
            kw: '#ffff55', str: '#55ff55', cmt: '#8c8cd0', sub: '#ff55ff',
            head: '#ffffff', rule: '#ff9a9a', num: '#55ffff', tbl: '#c8c8c8'
        },
        scrollbar: { thumb: '#555555', track: '#000000', thumbHover: '#aaaaaa' }
    },
    {
        id: 'apple2', name: 'Apple II',
        chrome: {
            pageBg: '#000', pageFg: '#33ff00', headingFg: '#66ff33',
            accentFg: '#33ff00', mutedFg: '#22aa00', dimFg: '#1a8800',
            cardBg: '#0a0a0a', cardBorder: '#1a3a00', toolbarBg: '#050505',
            border: '#1a3a00', borderHover: '#2a5a00', surfaceBg: '#0a1a00',
            btnBg: '#33ff00', btnFg: '#000', btnHoverBg: '#66ff33',
            inputBg: '#0a0a0a', inputFg: '#33ff00',
            activeTabBg: '#33ff00', activeTabFg: '#000',
            badgeBg: '#0a1a00', badgeFg: '#22aa00',
            codeBg: '#0a1a00', codeFg: '#33ff00',
            footerFg: '#1a8800', linkFg: '#33ff00',
            fontFamily: '"DotGothic16", "Courier New", monospace'
        },
        game: {
            bodyBg: '#000', bufferBg: '#000', bufferFg: '#33ff00',
            gridBg: '#33ff00', gridFg: '#000',
            inputFg: '#66ff33', emphFg: '#66ff33', headerFg: '#88ff66',
            bufferSize: '16px', bufferLineHeight: '1.4',
            gridSize: '16px', gridLineHeight: '22px',
            monoFamily: '"DotGothic16", "Courier New", monospace',
            propFamily: '"DotGothic16", "Courier New", monospace'
        },
        // green phosphor: brightness, not hue
        syntax: {
            kw: '#66ff33', str: '#33ff00', cmt: '#1e7a00', sub: '#8cff66',
            head: '#ccffbb', rule: '#2bcc00', num: '#55e02b', tbl: '#3fa82b'
        },
        scrollbar: { thumb: '#1a5500', track: '#000', thumbHover: '#2a7700' }
    },
    {
        id: 'c64', name: 'Commodore 64',
        chrome: {
            pageBg: '#000000', pageFg: '#ffffff', headingFg: '#ffffff',
            accentFg: '#b8c76f', mutedFg: '#9ad284', dimFg: '#959595',
            cardBg: '#352879', cardBorder: '#6c5eb5', toolbarBg: '#352879',
            border: '#6c5eb5', borderHover: '#9ad284', surfaceBg: '#352879',
            btnBg: '#9ad284', btnFg: '#000000', btnHoverBg: '#b8c76f',
            inputBg: '#000000', inputFg: '#ffffff',
            activeTabBg: '#9ad284', activeTabFg: '#000000',
            badgeBg: '#352879', badgeFg: '#ffffff',
            codeBg: '#000000', codeFg: '#70a4b2',
            footerFg: '#959595', linkFg: '#9ad284',
            fontFamily: '"Sixtyfour", "Courier New", monospace'
        },
        game: {
            bodyBg: '#352879', bufferBg: '#352879', bufferFg: '#ffffff',
            gridBg: '#6c5eb5', gridFg: '#ffffff',
            inputFg: '#9ad284', emphFg: '#b8c76f', headerFg: '#ffffff',
            bufferSize: '16px', bufferLineHeight: '1.4',
            gridSize: '16px', gridLineHeight: '22px',
            monoFamily: '"Sixtyfour", "Courier New", monospace',
            propFamily: '"Sixtyfour", "Courier New", monospace'
        },
        // every value is an exact Pepto-palette C64 color
        syntax: {
            kw: '#b8c76f', str: '#9ad284', cmt: '#6c6c6c', sub: '#70a4b2',
            head: '#ffffff', rule: '#959595', num: '#70a4b2', tbl: '#9ad284'
        },
        scrollbar: { thumb: '#6c5eb5', track: '#000000', thumbHover: '#9ad284' }
    },
    {
        id: 'amiga', name: 'Amiga',
        chrome: {
            pageBg: '#000000', pageFg: '#ffffff', headingFg: '#ffffff',
            accentFg: '#ffcc88', mutedFg: '#cce0f4', dimFg: '#aaccee',
            cardBg: '#0055aa', cardBorder: '#77aadd', toolbarBg: '#0055aa',
            border: '#77aadd', borderHover: '#ffcc88', surfaceBg: '#0055aa',
            btnBg: '#ff8800', btnFg: '#000000', btnHoverBg: '#ffcc88',
            inputBg: '#000000', inputFg: '#ffffff',
            activeTabBg: '#ff8800', activeTabFg: '#000000',
            badgeBg: '#0055aa', badgeFg: '#ffffff',
            codeBg: '#000000', codeFg: '#ff8800',
            footerFg: '#cce0f4', linkFg: '#ffcc88',
            fontFamily: '"Workbench", "Trebuchet MS", Tahoma, sans-serif'
        },
        game: {
            bodyBg: '#0055aa', bufferBg: '#0055aa', bufferFg: '#ffffff',
            gridBg: '#ff8800', gridFg: '#000000',
            inputFg: '#ffffff', emphFg: '#ffcc88', headerFg: '#ffffff',
            bufferSize: '16px', bufferLineHeight: '1.4',
            gridSize: '16px', gridLineHeight: '22px',
            monoFamily: '"Workbench", "Courier New", monospace',
            propFamily: '"Workbench", "Trebuchet MS", Tahoma, sans-serif'
        },
        // Workbench 1.3 had four colors — blue, white, black, orange. Four cannot
        // furnish eight classes, so the rest are tints of those hues, never a new one.
        syntax: {
            kw: '#ff8800', str: '#ffcc88', cmt: '#5588bb', sub: '#ffddaa',
            head: '#ffffff', rule: '#aaccee', num: '#77aadd', tbl: '#88bbdd'
        },
        scrollbar: { thumb: '#0055aa', track: '#000000', thumbHover: '#ff8800' }
    },
    {
        id: 'mac', name: 'Macintosh',
        chrome: {
            pageBg: '#fff', pageFg: '#000', headingFg: '#000',
            accentFg: '#000', mutedFg: '#555', dimFg: '#707070',
            cardBg: '#f0f0f0', cardBorder: '#ccc', toolbarBg: '#e8e8e8',
            border: '#ccc', borderHover: '#999', surfaceBg: '#e8e8e8',
            btnBg: '#000', btnFg: '#fff', btnHoverBg: '#333',
            inputBg: '#fff', inputFg: '#000',
            activeTabBg: '#000', activeTabFg: '#fff',
            badgeBg: '#e8e8e8', badgeFg: '#555',
            codeBg: '#e8e8e8', codeFg: '#000',
            footerFg: '#707070', linkFg: '#333',
            fontFamily: '"Geneva", "Lucida Grande", Helvetica, sans-serif'
        },
        game: {
            bodyBg: '#fff', bufferBg: '#fff', bufferFg: '#000',
            gridBg: '#000', gridFg: '#fff',
            inputFg: '#000', emphFg: '#333', headerFg: '#000',
            bufferSize: '16px', bufferLineHeight: '1.5',
            gridSize: '16px', gridLineHeight: '22px',
            monoFamily: 'Monaco, "Courier New", monospace',
            propFamily: '"Geneva", "Lucida Grande", Helvetica, sans-serif'
        },
        // black on white: brightness, not hue
        syntax: {
            kw: '#000000', str: '#3a3a3a', cmt: '#7a7a7a', sub: '#4a4a4a',
            head: '#000000', rule: '#5a5a5a', num: '#2a2a2a', tbl: '#636363'
        },
        scrollbar: { thumb: '#999', track: '#e8e8e8', thumbHover: '#777' }
    },
    {
        id: 'atarist', name: 'Atari ST',
        chrome: {
            pageBg: '#fff', pageFg: '#000', headingFg: '#000',
            accentFg: '#008800', mutedFg: '#555', dimFg: '#707070',
            cardBg: '#f0f0f0', cardBorder: '#ccc', toolbarBg: '#e8e8e8',
            border: '#ccc', borderHover: '#999', surfaceBg: '#e8e8e8',
            btnBg: '#008800', btnFg: '#fff', btnHoverBg: '#006600',
            inputBg: '#fff', inputFg: '#000',
            activeTabBg: '#008800', activeTabFg: '#fff',
            badgeBg: '#e8e8e8', badgeFg: '#555',
            codeBg: '#e8e8e8', codeFg: '#006600',
            footerFg: '#707070', linkFg: '#006600',
            fontFamily: '"Silkscreen", Tahoma, Helvetica, Arial, sans-serif'
        },
        game: {
            bodyBg: '#fff', bufferBg: '#fff', bufferFg: '#000',
            gridBg: '#008800', gridFg: '#fff',
            inputFg: '#000', emphFg: '#333', headerFg: '#000',
            bufferSize: '15px', bufferLineHeight: '1.35',
            gridSize: '15px', gridLineHeight: '19px',
            monoFamily: '"Silkscreen", "Courier New", Consolas, monospace',
            propFamily: '"Silkscreen", Tahoma, Helvetica, Arial, sans-serif'
        },
        // black on white with the ST’s green
        syntax: {
            kw: '#006600', str: '#3a3a3a', cmt: '#7a7a7a', sub: '#004d00',
            head: '#000000', rule: '#5a5a5a', num: '#2a2a2a', tbl: '#636363'
        },
        scrollbar: { thumb: '#999', track: '#e8e8e8', thumbHover: '#777' }
    },
    {
        id: 'cpm', name: 'CP/M (Kaypro)',
        chrome: {
            pageBg: '#000000', pageFg: '#5cff8f', headingFg: '#8affb0',
            accentFg: '#5cff8f', mutedFg: '#3fbf68', dimFg: '#35a058',
            cardBg: '#0a1a0f', cardBorder: '#1e4a2c', toolbarBg: '#0a1a0f',
            border: '#1e4a2c', borderHover: '#3fbf68', surfaceBg: '#0a1a0f',
            btnBg: '#5cff8f', btnFg: '#000000', btnHoverBg: '#8affb0',
            inputBg: '#0a1a0f', inputFg: '#5cff8f',
            activeTabBg: '#5cff8f', activeTabFg: '#000000',
            badgeBg: '#0a1a0f', badgeFg: '#3fbf68',
            codeBg: '#0a1a0f', codeFg: '#5cff8f',
            footerFg: '#35a058', linkFg: '#5cff8f',
            fontFamily: '"VT323", "Courier New", monospace'
        },
        game: {
            bodyBg: '#000000', bufferBg: '#000000', bufferFg: '#5cff8f',
            gridBg: '#5cff8f', gridFg: '#000000',
            inputFg: '#8affb0', emphFg: '#8affb0', headerFg: '#b0ffc8',
            bufferSize: '20px', bufferLineHeight: '1.25',
            gridSize: '20px', gridLineHeight: '24px',
            monoFamily: '"VT323", "Courier New", monospace',
            propFamily: '"VT323", "Courier New", monospace'
        },
        // Kaypro green phosphor: brightness, not hue
        syntax: {
            kw: '#8affb0', str: '#5cff8f', cmt: '#2d7a49', sub: '#a8ffc6',
            head: '#d6ffe4', rule: '#43c46e', num: '#6ee89c', tbl: '#4fae72'
        },
        scrollbar: { thumb: '#1e4a2c', track: '#000000', thumbHover: '#3fbf68' }
    },
    {
        id: 'atari8', name: 'Atari 800',
        chrome: {
            pageBg: '#2a3c86', pageFg: '#a8c8ff', headingFg: '#e0ecff',
            accentFg: '#a8c8ff', mutedFg: '#94b4ec', dimFg: '#92b2ee',
            cardBg: '#233270', cardBorder: '#3a5090', toolbarBg: '#26377a',
            border: '#3a5090', borderHover: '#4a60a0', surfaceBg: '#26377a',
            btnBg: '#a8c8ff', btnFg: '#1a2860', btnHoverBg: '#e0ecff',
            inputBg: '#233270', inputFg: '#a8c8ff',
            activeTabBg: '#a8c8ff', activeTabFg: '#1a2860',
            badgeBg: '#233270', badgeFg: '#94b4ec',
            codeBg: '#233270', codeFg: '#a8c8ff',
            footerFg: '#92b2ee', linkFg: '#e0ecff',
            fontFamily: '"Press Start 2P", "Courier New", monospace'
        },
        game: {
            bodyBg: '#2a3c86', bufferBg: '#2a3c86', bufferFg: '#a8c8ff',
            gridBg: '#a8c8ff', gridFg: '#1a2860',
            inputFg: '#e0ecff', emphFg: '#ffffff', headerFg: '#ffffff',
            bufferSize: '16px', bufferLineHeight: '1.6',
            gridSize: '16px', gridLineHeight: '22px',
            monoFamily: '"Press Start 2P", "Courier New", monospace',
            propFamily: '"Press Start 2P", "Courier New", monospace'
        },
        // GRAPHICS 0 blue
        syntax: {
            kw: '#e0ecff', str: '#a8ffd8', cmt: '#7f96d8', sub: '#ffc8e8',
            head: '#ffffff', rule: '#ffd8a8', num: '#a8c8ff', tbl: '#d8c0ff'
        },
        scrollbar: { thumb: '#3a5090', track: '#2a3c86', thumbHover: '#4a60a0' }
    },
    {
        id: 'trs80', name: 'TRS-80',
        chrome: {
            pageBg: '#000000', pageFg: '#d8d8d8', headingFg: '#ffffff',
            accentFg: '#ffffff', mutedFg: '#a0a0a0', dimFg: '#8a8a8a',
            cardBg: '#101010', cardBorder: '#333333', toolbarBg: '#101010',
            border: '#333333', borderHover: '#666666', surfaceBg: '#101010',
            btnBg: '#d8d8d8', btnFg: '#000000', btnHoverBg: '#ffffff',
            inputBg: '#101010', inputFg: '#d8d8d8',
            activeTabBg: '#d8d8d8', activeTabFg: '#000000',
            badgeBg: '#181818', badgeFg: '#a0a0a0',
            codeBg: '#181818', codeFg: '#d8d8d8',
            footerFg: '#8a8a8a', linkFg: '#ffffff',
            fontFamily: '"Tiny5", "Courier New", monospace'
        },
        game: {
            bodyBg: '#000000', bufferBg: '#000000', bufferFg: '#d8d8d8',
            gridBg: '#d8d8d8', gridFg: '#000000',
            inputFg: '#ffffff', emphFg: '#ffffff', headerFg: '#ffffff',
            bufferSize: '20px', bufferLineHeight: '1.4',
            gridSize: '20px', gridLineHeight: '24px',
            monoFamily: '"Tiny5", "Courier New", monospace',
            propFamily: '"Tiny5", "Courier New", monospace'
        },
        // Model III white phosphor: brightness, not hue
        syntax: {
            kw: '#ffffff', str: '#d8d8d8', cmt: '#7a7a7a', sub: '#e8e8e8',
            head: '#ffffff', rule: '#b0b0b0', num: '#c4c4c4', tbl: '#989898'
        },
        scrollbar: { thumb: '#555555', track: '#000000', thumbHover: '#888888' }
    },

    // ── Reading Themes (non-OS) ──

    {
        id: 'sepia', name: 'Sepia',
        chrome: {
            pageBg: '#f4ecd8', pageFg: '#5b4636', headingFg: '#3e2c1c',
            accentFg: '#8b5e3c', mutedFg: '#72614f', dimFg: '#776854',
            cardBg: '#ede0c8', cardBorder: '#d4c4a8', toolbarBg: '#e8d8be',
            border: '#d4c4a8', borderHover: '#baa888', surfaceBg: '#ede0c8',
            btnBg: '#8b5e3c', btnFg: '#f4ecd8', btnHoverBg: '#6b4426',
            inputBg: '#ede0c8', inputFg: '#5b4636',
            activeTabBg: '#8b5e3c', activeTabFg: '#f4ecd8',
            badgeBg: '#e8d8be', badgeFg: '#6c5b4b',
            codeBg: '#ede0c8', codeFg: '#6b4426',
            footerFg: '#776854', linkFg: '#8b5e3c',
            fontFamily: '"Iowan Old Style", Palatino, Georgia, "Times New Roman", serif'
        },
        game: {
            bodyBg: '#f4ecd8', bufferBg: '#f4ecd8', bufferFg: '#433020',
            gridBg: '#5b4636', gridFg: '#f4ecd8',
            inputFg: '#8b5e3c', emphFg: '#6b4426', headerFg: '#3e2c1c',
            bufferSize: '17px', bufferLineHeight: '1.7',
            gridSize: '15px', gridLineHeight: '20px',
            monoFamily: '"Iowan Old Style", Palatino, Georgia, "Times New Roman", serif',
            propFamily: '"Iowan Old Style", Palatino, Georgia, "Times New Roman", serif'
        },
        // ink on a warm page
        syntax: {
            kw: '#8b3e1e', str: '#4a6b2e', cmt: '#7f7058', sub: '#2f6b72',
            head: '#3e2c1c', rule: '#6b4426', num: '#7a3f5a', tbl: '#4a4a7a'
        },
        scrollbar: { thumb: '#c4a878', track: '#ede0c8', thumbHover: '#b09060' }
    },
    {
        id: 'midnight', name: 'Midnight',
        chrome: {
            pageBg: '#0d1b2a', pageFg: '#c8d6e5', headingFg: '#e2ecf5',
            accentFg: '#e0a050', mutedFg: '#7a8fa3', dimFg: '#6886a0',
            cardBg: '#132638', cardBorder: '#1e3a52', toolbarBg: '#0f2233',
            border: '#1e3a52', borderHover: '#2a5070', surfaceBg: '#132638',
            btnBg: '#e0a050', btnFg: '#0d1b2a', btnHoverBg: '#f0b868',
            inputBg: '#132638', inputFg: '#c8d6e5',
            activeTabBg: '#e0a050', activeTabFg: '#0d1b2a',
            badgeBg: '#132638', badgeFg: '#7a8fa3',
            codeBg: '#132638', codeFg: '#e0a050',
            footerFg: '#6886a0', linkFg: '#e0a050',
            fontFamily: 'Georgia, "Times New Roman", serif'
        },
        game: {
            bodyBg: '#0d1b2a', bufferBg: '#0d1b2a', bufferFg: '#c8d6e5',
            gridBg: '#1a3248', gridFg: '#e0a050',
            inputFg: '#e0a050', emphFg: '#f0c878', headerFg: '#e2ecf5',
            bufferSize: '17px', bufferLineHeight: '1.7',
            gridSize: '15px', gridLineHeight: '20px',
            monoFamily: '"SF Mono", "Fira Code", Consolas, "Courier New", monospace',
            propFamily: 'Georgia, "Times New Roman", serif'
        },
        syntax: {
            kw: '#e0a050', str: '#7fc99a', cmt: '#5b7186', sub: '#7fcfe8',
            head: '#e2ecf5', rule: '#d0b070', num: '#c89ad8', tbl: '#9aa8c0'
        },
        scrollbar: { thumb: '#1e3a52', track: '#0d1b2a', thumbHover: '#2a5070' }
    },
    {
        id: 'forest', name: 'Forest',
        chrome: {
            pageBg: '#0f1a12', pageFg: '#b8c9a8', headingFg: '#d0e0c0',
            accentFg: '#d4a050', mutedFg: '#7a8c69', dimFg: '#738868',
            cardBg: '#142218', cardBorder: '#1e3422', toolbarBg: '#0c1610',
            border: '#1e3422', borderHover: '#2e4a32', surfaceBg: '#142218',
            btnBg: '#d4a050', btnFg: '#0f1a12', btnHoverBg: '#e4b868',
            inputBg: '#142218', inputFg: '#b8c9a8',
            activeTabBg: '#d4a050', activeTabFg: '#0f1a12',
            badgeBg: '#142218', badgeFg: '#7a8c69',
            codeBg: '#142218', codeFg: '#d4a050',
            footerFg: '#738868', linkFg: '#d4a050',
            fontFamily: 'Georgia, "Times New Roman", serif'
        },
        game: {
            bodyBg: '#0f1a12', bufferBg: '#0f1a12', bufferFg: '#b8c9a8',
            gridBg: '#1a2e1e', gridFg: '#d4a050',
            inputFg: '#d4a050', emphFg: '#e4c878', headerFg: '#d0e0c0',
            bufferSize: '17px', bufferLineHeight: '1.7',
            gridSize: '15px', gridLineHeight: '20px',
            monoFamily: '"SF Mono", "Fira Code", Consolas, "Courier New", monospace',
            propFamily: 'Georgia, "Times New Roman", serif'
        },
        syntax: {
            kw: '#d4a050', str: '#9ac47a', cmt: '#5f7458', sub: '#8fbfa8',
            head: '#d0e0c0', rule: '#c0a868', num: '#c89a7a', tbl: '#8aa8a0'
        },
        scrollbar: { thumb: '#1e3422', track: '#0f1a12', thumbHover: '#2e4a32' }
    },
    {
        id: 'lavender', name: 'Lavender',
        chrome: {
            pageBg: '#1a1625', pageFg: '#d0c4e8', headingFg: '#e4daf4',
            accentFg: '#c898d0', mutedFg: '#8e7faa', dimFg: '#897aa9',
            cardBg: '#201a30', cardBorder: '#2e2644', toolbarBg: '#161220',
            border: '#2e2644', borderHover: '#443860', surfaceBg: '#201a30',
            btnBg: '#c898d0', btnFg: '#1a1625', btnHoverBg: '#d8ade0',
            inputBg: '#201a30', inputFg: '#d0c4e8',
            activeTabBg: '#c898d0', activeTabFg: '#1a1625',
            badgeBg: '#201a30', badgeFg: '#8e7faa',
            codeBg: '#201a30', codeFg: '#c898d0',
            footerFg: '#897aa9', linkFg: '#c898d0',
            fontFamily: 'Georgia, "Times New Roman", serif'
        },
        game: {
            bodyBg: '#1a1625', bufferBg: '#1a1625', bufferFg: '#d0c4e8',
            gridBg: '#2a2240', gridFg: '#c898d0',
            inputFg: '#c898d0', emphFg: '#d8ade0', headerFg: '#e4daf4',
            bufferSize: '17px', bufferLineHeight: '1.7',
            gridSize: '15px', gridLineHeight: '20px',
            monoFamily: '"SF Mono", "Fira Code", Consolas, "Courier New", monospace',
            propFamily: 'Georgia, "Times New Roman", serif'
        },
        syntax: {
            kw: '#c898d0', str: '#9ad0b0', cmt: '#6f6390', sub: '#8fb8e0',
            head: '#e4daf4', rule: '#d8b0a0', num: '#e0c080', tbl: '#a0a0d8'
        },
        scrollbar: { thumb: '#2e2644', track: '#1a1625', thumbHover: '#443860' }
    },
    {
        id: 'solarized', name: 'Solarized',
        chrome: {
            pageBg: '#002b36', pageFg: '#93a1a1', headingFg: '#93a1a1',
            accentFg: '#b58900', mutedFg: '#839496', dimFg: '#839496',
            cardBg: '#073642', cardBorder: '#094555', toolbarBg: '#01313d',
            border: '#094555', borderHover: '#0b5a6e', surfaceBg: '#073642',
            btnBg: '#b58900', btnFg: '#002b36', btnHoverBg: '#cb9a00',
            inputBg: '#073642', inputFg: '#93a1a1',
            activeTabBg: '#b58900', activeTabFg: '#002b36',
            badgeBg: '#073642', badgeFg: '#93a1a1',
            codeBg: '#002b36', codeFg: '#93a1a1',
            footerFg: '#839496', linkFg: '#2aa198',
            fontFamily: '"Menlo", "SF Mono", "Fira Code", Consolas, monospace'
        },
        game: {
            bodyBg: '#002b36', bufferBg: '#002b36', bufferFg: '#93a1a1',
            gridBg: '#073642', gridFg: '#93a1a1',
            inputFg: '#b58900', emphFg: '#93a1a1', headerFg: '#93a1a1',
            bufferSize: '16px', bufferLineHeight: '1.5',
            gridSize: '15px', gridLineHeight: '20px',
            monoFamily: '"Menlo", "SF Mono", "Fira Code", Consolas, "Courier New", monospace',
            propFamily: '"Menlo", "SF Mono", "Fira Code", Consolas, "Courier New", monospace'
        },
        // the Solarized accent ring
        syntax: {
            kw: '#b58900', str: '#2aa198', cmt: '#586e75', sub: '#6c71c4',
            head: '#93a1a1', rule: '#859900', num: '#268bd2', tbl: '#d33682'
        },
        scrollbar: { thumb: '#094555', track: '#002b36', thumbHover: '#0b5a6e' }
    }
];

/* The stored choice, or null when the reader has never made one. getThemeId() folds that
   null into 'classic', which is right for rendering but loses the distinction the player
   needs: a game with an overlay defaults to its overlay, so "never chose" and "chose
   classic" have to be told apart (#120). */
function storedThemeId() {
    try { return localStorage.getItem('ifhub-theme'); }
    catch (e) { return null; }
}

function getThemeId() {
    return storedThemeId() || 'classic';
}

function setThemeId(id) {
    try { localStorage.setItem('ifhub-theme', id); }
    catch (e) { /* localStorage unavailable */ }
}

function getTheme(id) {
    for (var i = 0; i < THEMES.length; i++) {
        if (THEMES[i].id === id) return THEMES[i];
    }
    return THEMES[0];
}

var CHROME_VAR_MAP = {
    pageBg: '--page-bg', pageFg: '--page-fg', headingFg: '--heading-fg',
    accentFg: '--accent', mutedFg: '--muted', dimFg: '--dim',
    cardBg: '--card-bg', cardBorder: '--card-border', toolbarBg: '--toolbar-bg',
    border: '--border', borderHover: '--border-hover', surfaceBg: '--surface-bg',
    btnBg: '--btn-bg', btnFg: '--btn-fg', btnHoverBg: '--btn-hover-bg',
    inputBg: '--input-bg', inputFg: '--input-fg',
    activeTabBg: '--active-tab-bg', activeTabFg: '--active-tab-fg',
    badgeBg: '--badge-bg', badgeFg: '--badge-fg',
    codeBg: '--code-bg', codeFg: '--code-fg',
    footerFg: '--footer-fg', linkFg: '--link-fg', fontFamily: '--font-family'
};

/* The source pane's own colors. Each theme carries its own eight, because deriving them
   from the chrome collapses on the narrow palettes: a phosphor terminal or a black-on-white
   Mac has no eight hues to give, and a naive mapping puts several classes on one value and
   stops distinguishing anything (#121). */
var SYNTAX_VAR_MAP = {
    kw: '--syn-kw', str: '--syn-str', cmt: '--syn-cmt', sub: '--syn-sub',
    head: '--syn-head', rule: '--syn-rule', num: '--syn-num', tbl: '--syn-tbl'
};

/* The variables a page needs for code and for search hits, as `--name: value;` text.
   Returned as a string so the same set can be set on this document or injected into an
   iframe the hub themes (the walkthrough viewer highlights search hits too). */
function syntaxVarText(theme) {
    var out = '--code-bg: ' + theme.chrome.codeBg + ';';
    var syn = theme.syntax || {};
    for (var k in SYNTAX_VAR_MAP) {
        if (syn[k]) out += SYNTAX_VAR_MAP[k] + ': ' + syn[k] + ';';
    }
    return out;
}

function applyChrome(theme) {
    var s = document.documentElement.style;
    var c = theme.chrome;
    for (var k in CHROME_VAR_MAP) s.setProperty(CHROME_VAR_MAP[k], c[k]);
    var syn = theme.syntax || {};
    for (var j in SYNTAX_VAR_MAP) {
        if (syn[j]) s.setProperty(SYNTAX_VAR_MAP[j], syn[j]);
    }
    s.setProperty('--scroll-thumb', theme.scrollbar.thumb);
    s.setProperty('--scroll-track', theme.scrollbar.track);
    s.setProperty('--scroll-thumb-hover', theme.scrollbar.thumbHover);
}

function initTheme(context) {
    // context is kept for callers ('app', 'library'); every page gets the chrome theme.
    applyChrome(getTheme(getThemeId()));
}

// Shared style for theme select elements (used by createThemeDropdown and app.html buildStyleDropdown)
var THEME_SELECT_STYLE = 'background:var(--input-bg);border:1px solid var(--border);color:var(--accent);border-radius:4px;padding:3px 8px;font-family:inherit;font-size:0.85em;cursor:pointer;';

/* The one id that is not a theme. "Native" means: inject nothing into pages the hub did
   not write — a game's own player, a workspace's tests report — so they can be seen as
   their author built them. Hub surfaces still need colors and fall back to classic,
   which getTheme() already does for any unknown id.

   Only the player offers it; the landing page has no foreign pages to leave alone. */
var NATIVE_ID = 'native';
var NATIVE_NAME = 'Native (game’s own look)';

// Populate a <select> with theme options, returning the element
function populateThemeOptions(select, includeNative) {
    for (var i = 0; i < THEMES.length; i++) {
        var opt = document.createElement('option');
        opt.value = THEMES[i].id;
        opt.textContent = THEMES[i].name;
        select.appendChild(opt);
    }
    if (includeNative) {
        var sep = document.createElement('option');
        sep.disabled = true;
        sep.textContent = '────────';
        select.appendChild(sep);
        var nat = document.createElement('option');
        nat.value = NATIVE_ID;
        nat.textContent = NATIVE_NAME;
        select.appendChild(nat);
    }
    return select;
}

// Resolve hub from URL params: returns { activeHub, hubParam }

// Filter a data entry by hub filter criteria

/* Fill a <select> with the platform themes, select the saved one, and apply the chrome on
   change. Used by createThemeDropdown() and by the landing page's own select. The player's
   style dropdown adds a per-game overlay option on top of populateThemeOptions(). */
function wireThemeSelect(select) {
    populateThemeOptions(select);
    select.value = getThemeId();
    // The stored id may not be offered here — Native is player-only — and an unmatched
    // value would leave the select blank. Classic is what those ids fall back to anyway.
    if (!select.value) select.value = 'classic';
    select.addEventListener('change', function() {
        setThemeId(this.value);
        applyChrome(getTheme(this.value));
    });
    return select;
}

function createThemeDropdown(containerId) {
    var container = document.getElementById(containerId);
    if (!container) return;

    var label = document.createElement('label');
    label.textContent = 'Theme: ';
    label.htmlFor = 'theme-select';
    label.style.cssText = 'color:var(--muted);font-size:0.85em;white-space:nowrap;cursor:pointer;';

    var select = document.createElement('select');
    select.id = 'theme-select';
    select.style.cssText = THEME_SELECT_STYLE;
    wireThemeSelect(select);

    container.appendChild(label);
    container.appendChild(select);
}

/* ==================================================================
   CSS BUILDERS — engine-specific theme CSS generation
   Used by app.html (iframe injection) and theme-listener.js (postMessage)
   ================================================================== */

function buildScrollbarCSS(sb) {
  return '* { scrollbar-color: ' + sb.thumb + ' ' + sb.track + ' !important; }\n' +
    '::-webkit-scrollbar { width: 10px; background: ' + sb.track + ' !important; }\n' +
    '::-webkit-scrollbar-thumb { background: ' + sb.thumb + ' !important; border-radius: 4px; }\n' +
    '::-webkit-scrollbar-thumb:hover { background: ' + sb.thumbHover + ' !important; }\n';
}

function buildChromeCSS(c, sb, varText) {
  return (varText ? ':root {' + varText + '}\n' : '') +
    'html, body { background: ' + c.pageBg + ' !important; color: ' + c.pageFg + ' !important; }\n' +
    'h1, h2, h3, h4, strong { color: ' + c.headingFg + ' !important; }\n' +
    'a { color: ' + c.accentFg + ' !important; }\n' +
    'a:hover { color: ' + c.btnHoverBg + ' !important; }\n' +
    'input, select, textarea { background: ' + c.inputBg + ' !important; color: ' + c.inputFg + ' !important; border-color: ' + c.border + ' !important; }\n' +
    'button { background: ' + c.btnBg + ' !important; color: ' + c.btnFg + ' !important; border-color: ' + c.border + ' !important; }\n' +
    'button:hover { background: ' + c.btnHoverBg + ' !important; }\n' +
    'button.active, .tab-btn.active, .mode-btn.active { background: ' + c.activeTabBg + ' !important; color: ' + c.activeTabFg + ' !important; }\n' +
    'pre, code { background: ' + c.codeBg + ' !important; color: ' + c.codeFg + ' !important; border-color: ' + c.border + ' !important; }\n' +
    'table, th, td, tr { border-color: ' + c.border + ' !important; }\n' +
    'th { color: ' + c.headingFg + ' !important; }\n' +
    'td { color: ' + c.pageFg + ' !important; }\n' +
    '.toolbar, .source-toolbar, .wt-toolbar, header, nav { background: ' + c.toolbarBg + ' !important; border-color: ' + c.border + ' !important; color: ' + c.mutedFg + ' !important; }\n' +
    '.sidebar, .nav, .wt-sidebar { background: ' + c.toolbarBg + ' !important; border-color: ' + c.cardBorder + ' !important; }\n' +
    '.nav-item, .wt-nav-item, .sidebar a { color: ' + c.mutedFg + ' !important; }\n' +
    '.nav-item.active, .wt-nav-item.active, .sidebar a.active { color: ' + c.headingFg + ' !important; border-left-color: ' + c.accentFg + ' !important; background: ' + c.surfaceBg + ' !important; }\n' +
    'footer { color: ' + c.footerFg + ' !important; border-color: ' + c.cardBorder + ' !important; }\n' +
    buildScrollbarCSS(sb);
}

function buildTestReportCSS(c, sb) {
  // ifplayer report uses CSS custom properties + hardcoded colors designed
  // for a light theme.  Map IF Hub chrome properties → ifplayer variables
  // and override hardcoded colors for dark/retro themes.
  var hex = c.pageBg.replace('#', '');
  var rv = parseInt(hex.slice(0,2), 16);
  var gv = parseInt(hex.slice(2,4), 16);
  var bv = parseInt(hex.slice(4,6), 16);
  var isLight = (rv * 299 + gv * 587 + bv * 114) / 1000 > 128;

  // Adaptive pass/fail/warn — brighter on dark backgrounds
  var pass     = isLight ? '#1a7f37' : '#3fb950';
  var passBg   = isLight ? '#dcffe4' : 'rgba(63, 185, 80, 0.15)';
  var fail     = isLight ? '#b81a3e' : '#f85149';
  var failBg   = isLight ? '#ffd9e0' : 'rgba(248, 81, 73, 0.15)';
  var warn     = isLight ? '#b87800' : '#d29922';
  var cardBg   = isLight ? '#ffffff' : c.cardBg;
  var roomClr  = isLight ? '#6b3a8a' : '#c49ee0';
  var gameFg   = isLight ? '#2a2620' : c.pageFg;
  var headerBg = isLight ? '#2b231a' : c.toolbarBg;
  var headerFg = isLight ? '#fafafa' : c.headingFg;
  var failHeaderBg  = isLight ? '#4a1626' : 'rgba(248, 81, 73, 0.2)';
  var turnRowBg     = isLight ? '#f1ebdb' : c.surfaceBg;
  var setupBg       = isLight ? '#f7f3ea' : c.surfaceBg;
  var setupListBg   = isLight ? '#fdfbf6' : c.cardBg;
  var failHoverBg   = isLight ? '#ffc6d3' : 'rgba(248, 81, 73, 0.2)';
  var failRowBorder = isLight ? '#f0aab8' : 'rgba(248, 81, 73, 0.3)';
  var hlBg     = isLight ? '#ffe88a' : 'rgba(255, 232, 138, 0.3)';
  var hlFg     = isLight ? '#5a4400' : '#ffe88a';
  var hlBorder = isLight ? '#d9b840' : '#b89a30';
  var metaFg   = isLight ? 'rgba(255,255,255,0.78)' : c.mutedFg;
  var arrowFg  = isLight ? 'rgba(255,255,255,0.55)' : c.mutedFg;

  return (
    /* ── CSS custom properties ─────────────────────────────────── */
    ':root {\n' +
    '  --bg: '      + c.pageBg    + ' !important;\n' +
    '  --fg: '      + c.pageFg    + ' !important;\n' +
    '  --muted: '   + c.mutedFg   + ' !important;\n' +
    '  --pass: '    + pass        + ' !important;\n' +
    '  --pass-bg: ' + passBg      + ' !important;\n' +
    '  --fail: '    + fail        + ' !important;\n' +
    '  --fail-bg: ' + failBg      + ' !important;\n' +
    '  --warn: '    + warn        + ' !important;\n' +
    '  --code-bg: ' + c.codeBg    + ' !important;\n' +
    '  --line: '    + c.border    + ' !important;\n' +
    '  --accent: '  + c.accentFg  + ' !important;\n' +
    '  --hover: '   + c.surfaceBg + ' !important;\n' +
    '  --ui-font: ' + c.fontFamily + ' !important;\n' +
    '}\n' +

    /* ── Page ──────────────────────────────────────────────────── */
    'html, body { background: ' + c.pageBg + ' !important; color: ' + c.pageFg + ' !important; }\n' +
    'h1 { color: ' + c.headingFg + ' !important; }\n' +

    /* ── Cards — override hardcoded "white" ────────────────────── */
    '.summary, .games, details.test, .test-body, .transcript, ' +
    'pre.turn-response, pre.opening-text, .turn-body, ' +
    '.drift-diff { background: ' + cardBg + ' !important; }\n' +
    '.summary, .games, details.test { border-color: ' + c.border + ' !important; }\n' +
    'details.test { box-shadow: none !important; }\n' +

    /* ── Test card header ──────────────────────────────────────── */
    'summary.test-summary { background: ' + headerBg + ' !important; color: ' + headerFg + ' !important; }\n' +
    'details.test[data-status="fail"] summary.test-summary { background: ' + failHeaderBg + ' !important; }\n' +
    'summary.test-summary .glyph.pass { color: ' + pass + ' !important; }\n' +
    'summary.test-summary .glyph.fail { color: ' + fail + ' !important; }\n' +
    'summary.test-summary::before { color: ' + arrowFg + ' !important; }\n' +
    '.test-summary-meta { color: ' + metaFg + ' !important; }\n' +
    '.test-summary-meta .outcome-walkthrough { color: ' + pass + ' !important; }\n' +
    '.test-summary-meta .outcome-scenario { color: ' + metaFg + ' !important; }\n' +
    '.test-summary-meta .outcome-error { color: ' + fail + ' !important; }\n' +

    /* ── Turn rows ─────────────────────────────────────────────── */
    'summary.turn-row { background: ' + turnRowBg + ' !important; border-top-color: ' + c.border + ' !important; }\n' +
    'details.turn-detail[data-status="fail"] summary.turn-row { border-top-color: ' + failRowBorder + ' !important; }\n' +
    'details.turn-detail[data-status="fail"] summary.turn-row:hover { background: ' + failHoverBg + ' !important; }\n' +

    /* ── Game text & rooms ─────────────────────────────────────── */
    'pre.turn-response, pre.opening-text { color: ' + gameFg + ' !important; }\n' +
    '.turn-room, .setup-end-room, li.setup-step .setup-room { color: ' + roomClr + ' !important; }\n' +

    /* ── Match highlights ──────────────────────────────────────── */
    '.hl.hl-active { background: ' + hlBg + ' !important; color: ' + hlFg + ' !important; box-shadow: 0 0 0 1px ' + hlBorder + ' !important; }\n' +
    'button.match-toggle { background: ' + cardBg + ' !important; }\n' +
    'button.match-toggle.active { background: ' + hlBg + ' !important; color: ' + hlFg + ' !important; border-color: ' + hlBorder + ' !important; }\n' +
    'li.fail button.match-toggle.active { background: ' + failBg + ' !important; color: ' + fail + ' !important; border-color: ' + fail + ' !important; }\n' +
    'li.fail.matches-active ~ pre.turn-response .hl.hl-active, ' +
    '.turn-detail[data-status="fail"] .hl.hl-active.hl-fail { background: ' + failBg + ' !important; color: ' + fail + ' !important; box-shadow: 0 0 0 1px ' + fail + ' !important; }\n' +

    /* ── Setup section ─────────────────────────────────────────── */
    'details.setup { background: ' + setupBg + ' !important; }\n' +
    'ul.setup-list { background: ' + setupListBg + ' !important; }\n' +
    'li.setup-step { border-bottom-color: ' + c.border + ' !important; }\n' +

    /* ── Scrollbar ─────────────────────────────────────────────── */
    buildScrollbarCSS(sb)
  );
}

function buildParchmentCSS(g, sb) {
  return 'body, html { background: ' + g.bodyBg + ' !important; }\n' +
    '.BufferWindow { color: ' + g.bufferFg + ' !important; background-color: ' + g.bufferBg + ' !important; font-family: ' + g.monoFamily + ' !important; font-size: ' + g.bufferSize + ' !important; line-height: ' + g.bufferLineHeight + ' !important; }\n' +
    '.BufferWindow span { color: ' + g.bufferFg + ' !important; }\n' +
    '.BufferWindow span.reverse { color: ' + g.bufferBg + ' !important; background-color: ' + g.bufferFg + ' !important; }\n' +
    '.BufferWindow .Style_input { color: ' + g.inputFg + ' !important; }\n' +
    '.BufferWindow .Style_emphasized { color: ' + g.emphFg + ' !important; }\n' +
    '.BufferWindow .Style_header { color: ' + g.headerFg + ' !important; }\n' +
    '.BufferWindow .Style_subheader,\n' +
    '.BufferWindow .Style_alert { color: ' + g.headerFg + ' !important; }\n' +
    '.BufferWindow .Input,\n' +
    '.BufferWindow textarea.Input { color: ' + g.inputFg + ' !important; caret-color: ' + g.inputFg + '; font-family: ' + g.monoFamily + ' !important; }\n' +
    '.GridWindow { color: ' + g.gridFg + ' !important; background-color: ' + g.gridBg + ' !important; padding: 4px 12px !important; border: none !important; border-radius: 0 !important; box-shadow: none !important; margin: 0 !important; width: 100% !important; box-sizing: border-box !important; }\n' +
    '.GridWindow span { color: ' + g.gridFg + ' !important; background-color: ' + g.gridBg + ' !important; }\n' +
    '.GridWindow span.reverse { color: ' + g.gridFg + ' !important; background-color: ' + g.gridBg + ' !important; }\n' +
    '#loadingpane { color: ' + g.bufferFg + '; background: ' + g.bodyBg + '; font-family: ' + g.monoFamily + '; }\n' +
    '.WindowFrame { background: transparent !important; }\n' +
    'div#gameport { background: linear-gradient(to bottom, ' + g.gridBg + ' 0px, ' + g.gridBg + ' ' + ((parseInt(g.gridLineHeight) || 20) + 10) + 'px, ' + g.bufferBg + ' ' + ((parseInt(g.gridLineHeight) || 20) + 10) + 'px) !important; }\n' +
    buildScrollbarCSS(sb);
}

function buildInkCSS(g, sb) {
  return 'body { background: ' + g.bodyBg + ' !important; color: ' + g.bufferFg + ' !important; font-family: ' + g.propFamily + ' !important; }\n' +
    'h1 { color: ' + g.headerFg + ' !important; border-bottom-color: ' + g.gridBg + ' !important; }\n' +
    '#story p { color: ' + g.bufferFg + ' !important; }\n' +
    '.choice-echo { color: ' + g.gridFg + ' !important; }\n' +
    '#choices { border-top-color: ' + g.gridBg + ' !important; }\n' +
    '.choice { color: ' + g.inputFg + ' !important; font-family: ' + g.propFamily + ' !important; }\n' +
    '.choice:hover { color: ' + g.headerFg + ' !important; }\n' +
    '#end { color: ' + g.emphFg + ' !important; }\n' +
    buildScrollbarCSS(sb);
}

function buildBasicCSS(g, sb) {
  return 'body, html { background: ' + g.bodyBg + ' !important; color: ' + g.bufferFg + ' !important; font-family: ' + g.monoFamily + ' !important; }\n' +
    'pre, .output, .terminal, #screen { color: ' + g.bufferFg + ' !important; background: ' + g.bufferBg + ' !important; font-family: ' + g.monoFamily + ' !important; }\n' +
    'input, .input-line { color: ' + g.inputFg + ' !important; background: ' + g.bufferBg + ' !important; font-family: ' + g.monoFamily + ' !important; caret-color: ' + g.inputFg + '; }\n' +
    buildScrollbarCSS(sb);
}

/* Sharpee (Chord) pages style their chrome through --theme-* variables (engine.css), and the
   page's own theme listener maps a hub theme onto the same variables when it gets the
   ifhub:applyTheme message. These rules win on specificity (html:root) and add explicit
   element rules so the chrome stays legible whatever the game's own theme set: the buffer
   pair for the bars, dropdowns, input line and dialogs; the grid pair (inverse video) for
   the status bar, hovers and buttons. */
function buildSharpeeCSS(g, sb) {
  return 'html:root {' +
    ' --theme-bg: ' + g.bodyBg + ' !important;' +
    ' --theme-bg-alt: ' + g.bufferBg + ' !important;' +
    ' --theme-desktop-bg: ' + g.bodyBg + ' !important;' +
    ' --theme-text: ' + g.bufferFg + ' !important;' +
    ' --theme-text-muted: ' + g.bufferFg + ' !important;' +
    ' --theme-accent: ' + g.gridBg + ' !important;' +
    ' --theme-accent-text: ' + g.gridFg + ' !important;' +
    ' --theme-border: ' + g.gridBg + ' !important;' +
    ' --theme-input-bg: ' + g.bufferBg + ' !important;' +
    ' --theme-menu-bg: ' + g.bufferBg + ' !important;' +
    ' --theme-menu-hover: ' + g.gridBg + ' !important;' +
    ' --theme-font: ' + g.monoFamily + ' !important;' +
    ' --theme-font-body: ' + g.propFamily + ' !important;' +
    ' --theme-font-chrome: ' + g.monoFamily + ' !important;' +
    ' --theme-font-size: ' + g.bufferSize + ' !important;' +
    ' --theme-line-height: ' + g.bufferLineHeight + ' !important; }\n' +
    'body, html { background: ' + g.bodyBg + ' !important; color: ' + g.bufferFg + ' !important; }\n' +
    '.sharpee-window-title-bar, .sharpee-menu-bar, .sharpee-menu-dropdown, .sharpee-input-bar, .sharpee-dialog { background: ' + g.bufferBg + ' !important; color: ' + g.bufferFg + ' !important; border-color: ' + g.gridBg + ' !important; }\n' +
    '.sharpee-window-title, .sharpee-menu-bar-trigger, .sharpee-menu-option, .sharpee-input-prompt { color: ' + g.bufferFg + ' !important; }\n' +
    '.sharpee-menu-bar-trigger:hover, .sharpee-menu-bar-item--open > .sharpee-menu-bar-trigger, .sharpee-menu-option:hover, .sharpee-status-bar, .sharpee-dialog-title, .sharpee-dialog-button { background: ' + g.gridBg + ' !important; color: ' + g.gridFg + ' !important; }\n' +
    '.sharpee-input-field { background: ' + g.bufferBg + ' !important; color: ' + g.inputFg + ' !important; caret-color: ' + g.inputFg + '; }\n' +
    '.sharpee-prose-pane .command-echo { color: ' + g.inputFg + ' !important; }\n' +
    '.sharpee-prose-pane .system-message { color: ' + g.emphFg + ' !important; }\n' +
    buildScrollbarCSS(sb);
}

function buildRezCSS(g, sb) {
  return 'body, html { background: ' + g.bodyBg + ' !important; color: ' + g.bufferFg + ' !important; font-family: ' + g.propFamily + ' !important; }\n' +
    '#game-container, .box, .card, .content, .section { background: ' + g.bufferBg + ' !important; color: ' + g.bufferFg + ' !important; }\n' +
    '.title, .subtitle, h1, h2, h3, strong { color: ' + g.headerFg + ' !important; }\n' +
    'a, a.choice { color: ' + g.inputFg + ' !important; }\n' +
    'a:hover, a.choice:hover { color: ' + g.headerFg + ' !important; }\n' +
    '.button, button { background: ' + g.gridBg + ' !important; color: ' + g.gridFg + ' !important; border-color: ' + g.gridBg + ' !important; }\n' +
    '.button:hover, button:hover { background: ' + g.emphFg + ' !important; }\n' +
    'blockquote { border-left-color: ' + g.inputFg + ' !important; color: ' + g.emphFg + ' !important; }\n' +
    '.navbar, .hero { background: ' + g.gridBg + ' !important; }\n' +
    buildScrollbarCSS(sb);
}
