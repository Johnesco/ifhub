// IF Hub Theme System
// Themes modeled after platforms Infocom shipped Z-machine games on

// Load retro platform fonts from Google Fonts
(function() {
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://fonts.googleapis.com/css2?family=DotGothic16&family=Press+Start+2P&family=Silkscreen&family=Sixtyfour&family=Tiny5&family=VT323&family=Workbench&display=swap';
    document.head.appendChild(link);
})();

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
            badgeBg: '#1a1814', badgeFg: '#7a6a4a',
            codeBg: '#1a1410', codeFg: '#e8d090',
            footerFg: '#665a40', linkFg: '#aa9966',
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
        scrollbar: { thumb: '#3a3020', track: '#111', thumbHover: '#5a4a30' }
    },
    {
        id: 'dos', name: 'MS-DOS',
        chrome: {
            pageBg: '#0a0a0a', pageFg: '#d4c5a9', headingFg: '#e8d8b0',
            accentFg: '#e8d090', mutedFg: '#aa9966', dimFg: '#9a8a6a',
            cardBg: '#111', cardBorder: '#1e1a14', toolbarBg: '#0e0a08',
            border: '#2a2418', borderHover: '#3a2a18', surfaceBg: '#1a1410',
            btnBg: '#e8d090', btnFg: '#0a0a0a', btnHoverBg: '#f0d890',
            inputBg: '#110a08', inputFg: '#e8d090',
            activeTabBg: '#e8d090', activeTabFg: '#0a0a0a',
            badgeBg: '#1a1814', badgeFg: '#7a6a4a',
            codeBg: '#1a1410', codeFg: '#e8d090',
            footerFg: '#665a40', linkFg: '#aa9966',
            fontFamily: '"VT323", "Consolas", "Courier New", monospace'
        },
        game: {
            bodyBg: '#000', bufferBg: '#000', bufferFg: '#aaa',
            gridBg: '#aaa', gridFg: '#000',
            inputFg: '#ccc', emphFg: '#ccc', headerFg: '#fff',
            bufferSize: '20px', bufferLineHeight: '1.25',
            gridSize: '20px', gridLineHeight: '24px',
            monoFamily: '"VT323", "Consolas", "Courier New", monospace',
            propFamily: '"VT323", "Consolas", "Courier New", monospace'
        },
        scrollbar: { thumb: '#333', track: '#000', thumbHover: '#444' }
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
        scrollbar: { thumb: '#1a5500', track: '#000', thumbHover: '#2a7700' }
    },
    {
        id: 'c64', name: 'Commodore 64',
        chrome: {
            pageBg: '#40318d', pageFg: '#70a4b2', headingFg: '#87bfcc',
            accentFg: '#70a4b2', mutedFg: '#6080a0', dimFg: '#506888',
            cardBg: '#352878', cardBorder: '#504090', toolbarBg: '#382b80',
            border: '#504090', borderHover: '#6050a0', surfaceBg: '#382b80',
            btnBg: '#70a4b2', btnFg: '#40318d', btnHoverBg: '#87bfcc',
            inputBg: '#352878', inputFg: '#70a4b2',
            activeTabBg: '#70a4b2', activeTabFg: '#40318d',
            badgeBg: '#352878', badgeFg: '#6080a0',
            codeBg: '#352878', codeFg: '#70a4b2',
            footerFg: '#506888', linkFg: '#87bfcc',
            fontFamily: '"Sixtyfour", "Courier New", monospace'
        },
        game: {
            bodyBg: '#40318d', bufferBg: '#40318d', bufferFg: '#70a4b2',
            gridBg: '#70a4b2', gridFg: '#40318d',
            inputFg: '#87bfcc', emphFg: '#87bfcc', headerFg: '#a0d4e0',
            bufferSize: '16px', bufferLineHeight: '1.4',
            gridSize: '16px', gridLineHeight: '22px',
            monoFamily: '"Sixtyfour", "Courier New", monospace',
            propFamily: '"Sixtyfour", "Courier New", monospace'
        },
        scrollbar: { thumb: '#6050a0', track: '#40318d', thumbHover: '#7060b0' }
    },
    {
        id: 'amiga', name: 'Amiga',
        chrome: {
            pageBg: '#0055aa', pageFg: '#fff', headingFg: '#fff',
            accentFg: '#ff8800', mutedFg: '#aaccee', dimFg: '#88aacc',
            cardBg: '#004488', cardBorder: '#3377bb', toolbarBg: '#003d7a',
            border: '#3377bb', borderHover: '#4488cc', surfaceBg: '#004488',
            btnBg: '#ff8800', btnFg: '#000', btnHoverBg: '#ffaa33',
            inputBg: '#004488', inputFg: '#fff',
            activeTabBg: '#ff8800', activeTabFg: '#000',
            badgeBg: '#004488', badgeFg: '#aaccee',
            codeBg: '#004488', codeFg: '#ff8800',
            footerFg: '#88aacc', linkFg: '#ffaa33',
            fontFamily: '"Workbench", "Trebuchet MS", Tahoma, sans-serif'
        },
        game: {
            bodyBg: '#0055aa', bufferBg: '#0055aa', bufferFg: '#fff',
            gridBg: '#ff8800', gridFg: '#000',
            inputFg: '#fff', emphFg: '#ffcc88', headerFg: '#fff',
            bufferSize: '16px', bufferLineHeight: '1.4',
            gridSize: '16px', gridLineHeight: '22px',
            monoFamily: '"Workbench", "Courier New", monospace',
            propFamily: '"Workbench", "Trebuchet MS", Tahoma, sans-serif'
        },
        scrollbar: { thumb: '#3377bb', track: '#0055aa', thumbHover: '#4488cc' }
    },
    {
        id: 'mac', name: 'Macintosh',
        chrome: {
            pageBg: '#fff', pageFg: '#000', headingFg: '#000',
            accentFg: '#000', mutedFg: '#555', dimFg: '#777',
            cardBg: '#f0f0f0', cardBorder: '#ccc', toolbarBg: '#e8e8e8',
            border: '#ccc', borderHover: '#999', surfaceBg: '#e8e8e8',
            btnBg: '#000', btnFg: '#fff', btnHoverBg: '#333',
            inputBg: '#fff', inputFg: '#000',
            activeTabBg: '#000', activeTabFg: '#fff',
            badgeBg: '#e8e8e8', badgeFg: '#555',
            codeBg: '#e8e8e8', codeFg: '#000',
            footerFg: '#777', linkFg: '#333',
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
        scrollbar: { thumb: '#999', track: '#e8e8e8', thumbHover: '#777' }
    },
    {
        id: 'atarist', name: 'Atari ST',
        chrome: {
            pageBg: '#fff', pageFg: '#000', headingFg: '#000',
            accentFg: '#008800', mutedFg: '#555', dimFg: '#777',
            cardBg: '#f0f0f0', cardBorder: '#ccc', toolbarBg: '#e8e8e8',
            border: '#ccc', borderHover: '#999', surfaceBg: '#e8e8e8',
            btnBg: '#008800', btnFg: '#fff', btnHoverBg: '#00aa00',
            inputBg: '#fff', inputFg: '#000',
            activeTabBg: '#008800', activeTabFg: '#fff',
            badgeBg: '#e8e8e8', badgeFg: '#555',
            codeBg: '#e8e8e8', codeFg: '#008800',
            footerFg: '#777', linkFg: '#006600',
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
        scrollbar: { thumb: '#999', track: '#e8e8e8', thumbHover: '#777' }
    },
    {
        id: 'cpm', name: 'CP/M (Kaypro)',
        chrome: {
            pageBg: '#000', pageFg: '#ffb000', headingFg: '#ffc033',
            accentFg: '#ffb000', mutedFg: '#aa7700', dimFg: '#886600',
            cardBg: '#0a0a00', cardBorder: '#332200', toolbarBg: '#050500',
            border: '#332200', borderHover: '#554400', surfaceBg: '#1a1100',
            btnBg: '#ffb000', btnFg: '#000', btnHoverBg: '#ffc033',
            inputBg: '#0a0a00', inputFg: '#ffb000',
            activeTabBg: '#ffb000', activeTabFg: '#000',
            badgeBg: '#1a1100', badgeFg: '#aa7700',
            codeBg: '#1a1100', codeFg: '#ffb000',
            footerFg: '#886600', linkFg: '#ffb000',
            fontFamily: '"VT323", "Courier New", monospace'
        },
        game: {
            bodyBg: '#000', bufferBg: '#000', bufferFg: '#ffb000',
            gridBg: '#ffb000', gridFg: '#000',
            inputFg: '#ffc033', emphFg: '#ffc033', headerFg: '#ffd066',
            bufferSize: '20px', bufferLineHeight: '1.25',
            gridSize: '20px', gridLineHeight: '24px',
            monoFamily: '"VT323", "Courier New", monospace',
            propFamily: '"VT323", "Courier New", monospace'
        },
        scrollbar: { thumb: '#554400', track: '#000', thumbHover: '#776600' }
    },
    {
        id: 'atari8', name: 'Atari 800',
        chrome: {
            pageBg: '#2a3c86', pageFg: '#5494d4', headingFg: '#6aade8',
            accentFg: '#5494d4', mutedFg: '#4070a0', dimFg: '#365e8a',
            cardBg: '#233270', cardBorder: '#3a5090', toolbarBg: '#26377a',
            border: '#3a5090', borderHover: '#4a60a0', surfaceBg: '#26377a',
            btnBg: '#5494d4', btnFg: '#2a3c86', btnHoverBg: '#6aade8',
            inputBg: '#233270', inputFg: '#5494d4',
            activeTabBg: '#5494d4', activeTabFg: '#2a3c86',
            badgeBg: '#233270', badgeFg: '#4070a0',
            codeBg: '#233270', codeFg: '#5494d4',
            footerFg: '#365e8a', linkFg: '#6aade8',
            fontFamily: '"Press Start 2P", "Courier New", monospace'
        },
        game: {
            bodyBg: '#2a3c86', bufferBg: '#2a3c86', bufferFg: '#5494d4',
            gridBg: '#5494d4', gridFg: '#2a3c86',
            inputFg: '#6aade8', emphFg: '#6aade8', headerFg: '#88c8f0',
            bufferSize: '16px', bufferLineHeight: '1.6',
            gridSize: '16px', gridLineHeight: '22px',
            monoFamily: '"Press Start 2P", "Courier New", monospace',
            propFamily: '"Press Start 2P", "Courier New", monospace'
        },
        scrollbar: { thumb: '#3a5090', track: '#2a3c86', thumbHover: '#4a60a0' }
    },
    {
        id: 'trs80', name: 'TRS-80',
        chrome: {
            pageBg: '#003000', pageFg: '#b0ffb0', headingFg: '#c0ffc0',
            accentFg: '#b0ffb0', mutedFg: '#60aa60', dimFg: '#408840',
            cardBg: '#002800', cardBorder: '#1a5a1a', toolbarBg: '#002400',
            border: '#1a5a1a', borderHover: '#2a7a2a', surfaceBg: '#003800',
            btnBg: '#b0ffb0', btnFg: '#003000', btnHoverBg: '#c0ffc0',
            inputBg: '#002800', inputFg: '#b0ffb0',
            activeTabBg: '#b0ffb0', activeTabFg: '#003000',
            badgeBg: '#003800', badgeFg: '#60aa60',
            codeBg: '#003800', codeFg: '#b0ffb0',
            footerFg: '#408840', linkFg: '#b0ffb0',
            fontFamily: '"Tiny5", "Courier New", monospace'
        },
        game: {
            bodyBg: '#003000', bufferBg: '#003000', bufferFg: '#b0ffb0',
            gridBg: '#b0ffb0', gridFg: '#003000',
            inputFg: '#c0ffc0', emphFg: '#c0ffc0', headerFg: '#d0ffd0',
            bufferSize: '20px', bufferLineHeight: '1.4',
            gridSize: '20px', gridLineHeight: '24px',
            monoFamily: '"Tiny5", "Courier New", monospace',
            propFamily: '"Tiny5", "Courier New", monospace'
        },
        scrollbar: { thumb: '#1a5a1a', track: '#003000', thumbHover: '#2a7a2a' }
    },

    // ── Reading Themes (non-OS) ──

    {
        id: 'sepia', name: 'Sepia',
        chrome: {
            pageBg: '#f4ecd8', pageFg: '#5b4636', headingFg: '#3e2c1c',
            accentFg: '#8b5e3c', mutedFg: '#8a7560', dimFg: '#a08e78',
            cardBg: '#ede0c8', cardBorder: '#d4c4a8', toolbarBg: '#e8d8be',
            border: '#d4c4a8', borderHover: '#baa888', surfaceBg: '#ede0c8',
            btnBg: '#8b5e3c', btnFg: '#f4ecd8', btnHoverBg: '#a0714a',
            inputBg: '#ede0c8', inputFg: '#5b4636',
            activeTabBg: '#8b5e3c', activeTabFg: '#f4ecd8',
            badgeBg: '#e8d8be', badgeFg: '#8a7560',
            codeBg: '#ede0c8', codeFg: '#8b5e3c',
            footerFg: '#a08e78', linkFg: '#8b5e3c',
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
        scrollbar: { thumb: '#c4a878', track: '#ede0c8', thumbHover: '#b09060' }
    },
    {
        id: 'midnight', name: 'Midnight',
        chrome: {
            pageBg: '#0d1b2a', pageFg: '#c8d6e5', headingFg: '#e2ecf5',
            accentFg: '#e0a050', mutedFg: '#6b8299', dimFg: '#506a80',
            cardBg: '#132638', cardBorder: '#1e3a52', toolbarBg: '#0f2233',
            border: '#1e3a52', borderHover: '#2a5070', surfaceBg: '#132638',
            btnBg: '#e0a050', btnFg: '#0d1b2a', btnHoverBg: '#f0b868',
            inputBg: '#132638', inputFg: '#c8d6e5',
            activeTabBg: '#e0a050', activeTabFg: '#0d1b2a',
            badgeBg: '#132638', badgeFg: '#6b8299',
            codeBg: '#132638', codeFg: '#e0a050',
            footerFg: '#506a80', linkFg: '#e0a050',
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
        scrollbar: { thumb: '#1e3a52', track: '#0d1b2a', thumbHover: '#2a5070' }
    },
    {
        id: 'forest', name: 'Forest',
        chrome: {
            pageBg: '#0f1a12', pageFg: '#b8c9a8', headingFg: '#d0e0c0',
            accentFg: '#d4a050', mutedFg: '#708060', dimFg: '#586850',
            cardBg: '#142218', cardBorder: '#1e3422', toolbarBg: '#0c1610',
            border: '#1e3422', borderHover: '#2e4a32', surfaceBg: '#142218',
            btnBg: '#d4a050', btnFg: '#0f1a12', btnHoverBg: '#e4b868',
            inputBg: '#142218', inputFg: '#b8c9a8',
            activeTabBg: '#d4a050', activeTabFg: '#0f1a12',
            badgeBg: '#142218', badgeFg: '#708060',
            codeBg: '#142218', codeFg: '#d4a050',
            footerFg: '#586850', linkFg: '#d4a050',
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
        scrollbar: { thumb: '#1e3422', track: '#0f1a12', thumbHover: '#2e4a32' }
    },
    {
        id: 'lavender', name: 'Lavender',
        chrome: {
            pageBg: '#1a1625', pageFg: '#d0c4e8', headingFg: '#e4daf4',
            accentFg: '#c898d0', mutedFg: '#8070a0', dimFg: '#685888',
            cardBg: '#201a30', cardBorder: '#2e2644', toolbarBg: '#161220',
            border: '#2e2644', borderHover: '#443860', surfaceBg: '#201a30',
            btnBg: '#c898d0', btnFg: '#1a1625', btnHoverBg: '#d8ade0',
            inputBg: '#201a30', inputFg: '#d0c4e8',
            activeTabBg: '#c898d0', activeTabFg: '#1a1625',
            badgeBg: '#201a30', badgeFg: '#8070a0',
            codeBg: '#201a30', codeFg: '#c898d0',
            footerFg: '#685888', linkFg: '#c898d0',
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
        scrollbar: { thumb: '#2e2644', track: '#1a1625', thumbHover: '#443860' }
    },
    {
        id: 'sharpee', name: 'Sharpee',
        chrome: {
            pageBg: '#0000aa', pageFg: '#ffffff', headingFg: '#ffffff',
            accentFg: '#00aaaa', mutedFg: '#aaaaaa', dimFg: '#888888',
            cardBg: '#000088', cardBorder: '#00aaaa', toolbarBg: '#000077',
            border: '#00aaaa', borderHover: '#55dddd', surfaceBg: '#000088',
            btnBg: '#00aaaa', btnFg: '#000000', btnHoverBg: '#55dddd',
            inputBg: '#000088', inputFg: '#00aaaa',
            activeTabBg: '#00aaaa', activeTabFg: '#000000',
            badgeBg: '#000088', badgeFg: '#aaaaaa',
            codeBg: '#000088', codeFg: '#00aaaa',
            footerFg: '#888888', linkFg: '#00aaaa',
            fontFamily: '"Perfect DOS VGA 437", "Consolas", "Courier New", monospace'
        },
        game: {
            bodyBg: '#0000aa', bufferBg: '#0000aa', bufferFg: '#ffffff',
            gridBg: '#00aaaa', gridFg: '#000000',
            inputFg: '#00aaaa', emphFg: '#aaaaaa', headerFg: '#ffffff',
            bufferSize: '16px', bufferLineHeight: '1.4',
            gridSize: '16px', gridLineHeight: '22px',
            monoFamily: '"Perfect DOS VGA 437", "Consolas", "Courier New", monospace',
            propFamily: '"Perfect DOS VGA 437", "Consolas", "Courier New", monospace'
        },
        scrollbar: { thumb: '#00aaaa', track: '#000088', thumbHover: '#55dddd' }
    },
    {
        id: 'solarized', name: 'Solarized',
        chrome: {
            pageBg: '#002b36', pageFg: '#839496', headingFg: '#93a1a1',
            accentFg: '#b58900', mutedFg: '#657b83', dimFg: '#586e75',
            cardBg: '#073642', cardBorder: '#094555', toolbarBg: '#01313d',
            border: '#094555', borderHover: '#0b5a6e', surfaceBg: '#073642',
            btnBg: '#b58900', btnFg: '#002b36', btnHoverBg: '#cb9a00',
            inputBg: '#073642', inputFg: '#839496',
            activeTabBg: '#b58900', activeTabFg: '#002b36',
            badgeBg: '#073642', badgeFg: '#657b83',
            codeBg: '#073642', codeFg: '#b58900',
            footerFg: '#586e75', linkFg: '#2aa198',
            fontFamily: '"Menlo", "SF Mono", "Fira Code", Consolas, monospace'
        },
        game: {
            bodyBg: '#002b36', bufferBg: '#002b36', bufferFg: '#839496',
            gridBg: '#073642', gridFg: '#b58900',
            inputFg: '#b58900', emphFg: '#cb4b16', headerFg: '#93a1a1',
            bufferSize: '16px', bufferLineHeight: '1.5',
            gridSize: '15px', gridLineHeight: '20px',
            monoFamily: '"Menlo", "SF Mono", "Fira Code", Consolas, "Courier New", monospace',
            propFamily: '"Menlo", "SF Mono", "Fira Code", Consolas, "Courier New", monospace'
        },
        scrollbar: { thumb: '#094555', track: '#002b36', thumbHover: '#0b5a6e' }
    }
];

var _themeContext = null;

function getThemeId() {
    try { return localStorage.getItem('ifhub-theme') || 'classic'; }
    catch (e) { return 'classic'; }
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

function applyChrome(theme) {
    var s = document.documentElement.style;
    var c = theme.chrome;
    s.setProperty('--page-bg', c.pageBg);
    s.setProperty('--page-fg', c.pageFg);
    s.setProperty('--heading-fg', c.headingFg);
    s.setProperty('--accent', c.accentFg);
    s.setProperty('--muted', c.mutedFg);
    s.setProperty('--dim', c.dimFg);
    s.setProperty('--card-bg', c.cardBg);
    s.setProperty('--card-border', c.cardBorder);
    s.setProperty('--toolbar-bg', c.toolbarBg);
    s.setProperty('--border', c.border);
    s.setProperty('--border-hover', c.borderHover);
    s.setProperty('--surface-bg', c.surfaceBg);
    s.setProperty('--btn-bg', c.btnBg);
    s.setProperty('--btn-fg', c.btnFg);
    s.setProperty('--btn-hover-bg', c.btnHoverBg);
    s.setProperty('--input-bg', c.inputBg);
    s.setProperty('--input-fg', c.inputFg);
    s.setProperty('--active-tab-bg', c.activeTabBg);
    s.setProperty('--active-tab-fg', c.activeTabFg);
    s.setProperty('--badge-bg', c.badgeBg);
    s.setProperty('--badge-fg', c.badgeFg);
    s.setProperty('--code-bg', c.codeBg);
    s.setProperty('--code-fg', c.codeFg);
    s.setProperty('--footer-fg', c.footerFg);
    s.setProperty('--link-fg', c.linkFg);
    s.setProperty('--font-family', c.fontFamily);
    s.setProperty('--scroll-thumb', theme.scrollbar.thumb);
    s.setProperty('--scroll-track', theme.scrollbar.track);
    s.setProperty('--scroll-thumb-hover', theme.scrollbar.thumbHover);
}

function applyGame(theme) {
    var g = theme.game;
    var s = document.documentElement.style;
    s.setProperty('--glkote-buffer-bg', g.bufferBg);
    s.setProperty('--glkote-buffer-fg', g.bufferFg);
    s.setProperty('--glkote-buffer-reverse-bg', g.bufferFg);
    s.setProperty('--glkote-buffer-reverse-fg', g.bufferBg);
    s.setProperty('--glkote-buffer-size', g.bufferSize);
    s.setProperty('--glkote-buffer-line-height', g.bufferLineHeight);
    s.setProperty('--glkote-grid-bg', g.gridBg);
    s.setProperty('--glkote-grid-fg', g.gridFg);
    s.setProperty('--glkote-grid-reverse-bg', g.gridFg);
    s.setProperty('--glkote-grid-reverse-fg', g.gridBg);
    s.setProperty('--glkote-grid-size', g.gridSize);
    s.setProperty('--glkote-grid-line-height', g.gridLineHeight);
    s.setProperty('--glkote-input-fg', g.inputFg);
    s.setProperty('--glkote-mono-family', g.monoFamily);
    s.setProperty('--glkote-prop-family', g.propFamily);

    var el = document.getElementById('theme-game-overrides');
    if (el) el.remove();

    // Classic theme: just set CSS vars, don't inject override style
    // (the game's own CSS already has the right look)
    if (theme.id === 'classic') {
        setTimeout(function() { window.dispatchEvent(new Event('resize')); }, 50);
        return;
    }

    var style = document.createElement('style');
    style.id = 'theme-game-overrides';
    style.textContent =
        'body, html { background: ' + g.bodyBg + ' !important; }\n' +
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
        '* { scrollbar-color: ' + theme.scrollbar.thumb + ' ' + theme.scrollbar.track + '; }\n' +
        '::-webkit-scrollbar { width: 10px; background: ' + theme.scrollbar.track + '; }\n' +
        '::-webkit-scrollbar-thumb { background: ' + theme.scrollbar.thumb + '; border-radius: 4px; }\n' +
        '::-webkit-scrollbar-thumb:hover { background: ' + theme.scrollbar.thumbHover + '; }\n';
    document.head.appendChild(style);

    setTimeout(function() {
        window.dispatchEvent(new Event('resize'));
    }, 50);
}

function initTheme(context) {
    _themeContext = context;
    var theme = getTheme(getThemeId());
    if (context === 'game') {
        applyGame(theme);
        window.addEventListener('message', function(e) {
            if (e.data && e.data.type === 'ifhub:themeChange') {
                var t = getTheme(e.data.themeId);
                if (t) {
                    setThemeId(e.data.themeId);
                    applyGame(t);
                }
            }
        });
    } else {
        applyChrome(theme);
    }
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
    select.style.cssText = 'background:var(--input-bg);border:1px solid var(--border);color:var(--accent);border-radius:4px;padding:3px 8px;font-family:inherit;font-size:0.85em;cursor:pointer;';

    for (var i = 0; i < THEMES.length; i++) {
        var opt = document.createElement('option');
        opt.value = THEMES[i].id;
        opt.textContent = THEMES[i].name;
        if (THEMES[i].id === getThemeId()) opt.selected = true;
        select.appendChild(opt);
    }

    select.addEventListener('change', function() {
        var id = this.value;
        setThemeId(id);
        var theme = getTheme(id);
        if (_themeContext === 'game') {
            applyGame(theme);
        } else {
            applyChrome(theme);
        }
        var frame = document.getElementById('game-frame');
        if (frame && frame.contentWindow) {
            frame.contentWindow.postMessage({ type: 'ifhub:themeChange', themeId: id }, '*');
        }
    });

    container.appendChild(label);
    container.appendChild(select);
}
