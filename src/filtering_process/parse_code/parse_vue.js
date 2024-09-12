const parser = require('@babel/parser');
const fs = require('fs');

// Read Vue SFC content from command-line arguments
const vueCode = process.argv[2];

// Function to parse Vue SFC code and get AST
function parseVueSFC(code) {
    // Replace <>...</> with <Fragment>...</Fragment> for compatibility with Babel parser
    const jsxFragmentCode = code.replace(/<>/g, '<Fragment>').replace(/<\/>/g, '</Fragment>');

    return parser.parse(jsxFragmentCode, {
        sourceType: 'module',
        plugins: [
            'jsx', // Enable JSX parsing
            'typescript', // Enable TypeScript parsing
            'classProperties', // Enable class properties syntax (optional)
            'decorators-legacy' // Enable decorators syntax (optional)
        ],
        // Use @vue/babel-preset-jsx to enable Vue.js JSX support
        presets: [
            '@vue/babel-preset-jsx'
        ]
    });
}

// Parse the Vue SFC code and log the AST
const ast = parseVueSFC(vueCode);
console.log(JSON.stringify(ast, null, 2));
