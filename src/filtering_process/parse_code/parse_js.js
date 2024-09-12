const parser = require('@babel/parser');
const fs = require('fs');

// Read JavaScript code from command-line arguments
const jsCode = process.argv[2];

// Function to parse JavaScript code and get AST
function parseJS(code) {
    return parser.parse(code, {
        sourceType: 'module',
        plugins: [
            'jsx',       // Enable JSX parsing
            'typescript' // Enable TypeScript parsing
        ]
    });
}

// Parse the JavaScript code and log the AST
const ast = parseJS(jsCode);
console.log(JSON.stringify(ast, null, 2));
