const cheerio = require('cheerio');

// Function to parse HTML code and extract information from all tags
function parseHTML(html) {
    const $ = cheerio.load(html);

    // Initialize an object to store tag information
    const tags = {};

    // Iterate through all elements
    $('*').each(function() {
        const tagName = $(this).prop('tagName').toLowerCase();

        // Initialize array for tag if it doesn't exist
        if (!tags[tagName]) {
            tags[tagName] = [];
        }

        // Push inner text of the element to the array
        tags[tagName].push($(this).text().trim());
    });

    return tags;
}

// Read HTML code from stdin
let htmlCode = '';
process.stdin.setEncoding('utf-8');
process.stdin.on('data', function(data) {
    htmlCode += data;
});

// When stdin ends, parse the HTML code and print the result
process.stdin.on('end', function() {
    const result = parseHTML(htmlCode);
    console.log(JSON.stringify(result, null, 2));
});
