var root = './lib/'; // filled in by jekyll
var protocol = (document.location.protocol !== 'file:') ? document.location.protocol : 'http:';
head.js(
    // External libraries
    root + 'ext/jquery.min.js',
    root + 'ext/jquery.svg.min.js',
    root + 'ext/jquery.svgdom.min.js',
    root + 'ext/jquery-ui.min.js',
    root + 'ext/waypoints.min.js',
    root + 'ext/jquery.address.min.js',

    // brat helper modules
    root + 'brat/configuration.js',
    root + 'brat/util.js',
    root + 'brat/annotation_log.js',
    root + 'ext/webfont.js',

    // brat modules
    root + 'brat/dispatcher.js',
    root + 'brat/url_monitor.js',
    root + 'brat/visualizer.js',
    // embedding configuration
    root + 'local/config.js',
    // project-specific collection data
    root + 'local/collections.js',

    // NOTE: non-local libraries
    protocol + '//spyysalo.github.io/annodoc/lib/local/annodoc.js',
    protocol + '//spyysalo.github.io/conllu.js/conllu.js',
    //JNW stuff
    root + 'visualise.js'
);
var webFontURLs = [
    root + 'static/fonts/PT_Sans-Caption-Web-Regular.ttf',
    root + 'static/fonts/Liberation_Sans-Regular.ttf'
];
var setupTabs = function() {
    // standard jQuery UI "tabs" element initialization
    $(".jquery-ui-tabs").tabs({
        heightStyle: "auto"
    });
    // use jQuery address to preserve tab state
    // (see https://github.com/UniversalDependencies/docs/issues/65,
    // http://stackoverflow.com/a/3330919)
    if ($(".jquery-ui-tabs").length > 0) {
        $.address.change(function(event) {
            $(".jquery-ui-tabs").tabs("select", window.location.hash)
        });
        $(".jquery-ui-tabs").bind("tabsselect", function(event, ui) {
            window.location.hash = ui.tab.hash;
        });
    }
};

head.ready(function() {
    // set up UI tabs on page
    setupTabs();
    // mark current collection (filled in by Jekyll)
    Collections.listing['_current'] = 'u-overview';

    //check if the URL contains a sentence
    var url = decodeURI(window.location.href);
    var qindex = url.indexOf("?");
    if (qindex != -1){
        var uri = url.substring(qindex + 1, url.length);
        var arguments = uri.split("&");
        var variables = [];
        for (var i = 0; i < arguments.length; i++) {
            variables[i] = arguments[i].split("=")[1].replace(/\+/g, " ");
            // do this as many times as there are variables
            // add vars for all the next variables you want
        };
        // variables is now an array populated with the values of the variables you want, in order
            // variables[0] is the text for the textbox
            // variables[1] could be the format to be forced

        $("#indata").val(variables[0]);

        keyUpFunc(); // activate it in the display
    }

    // perform all embedding and support functions
    Annodoc.activate(Config.bratCollData, Collections.listing);
    $("#cgin").keyup(
        cgParse
    );
    $("#conlluin").keyup(
        function() {
            var content = $("#conlluin").val();
            $("#dest").removeClass("language-sdparse").addClass("language-conllu");
            $("#dest").html(content); // $("#source");
            Annodoc.activate(Config.bratCollData, Collections.listing);
        }
    )
    $('#indata').on('input', keyUpFunc);
    $('#glossInput').on('input', updateGlossTable);

    (function($) {
        function pasteIntoInput(el, text) {
            el.focus();
            if (typeof el.selectionStart == "number") {
                var val = el.value;
                var selStart = el.selectionStart;
                el.value = val.slice(0, selStart) + text + val.slice(el.selectionEnd);
                el.selectionEnd = el.selectionStart = selStart + text.length;
            } else if (typeof document.selection != "undefined") {
                var textRange = document.selection.createRange();
                textRange.text = text;
                textRange.collapse(false);
                textRange.select();
            }
        }
    
        function allowTabChar(el) {
            $(el).keydown(function(e) {
                if (e.which == 9) {
                    pasteIntoInput(this, "\t");
                    return false;
                }
            });
    
            // For Opera, which only allows suppression of keypress events, not keydown
            $(el).keypress(function(e) {
                if (e.which == 9) {
                    return false;
                }
            });
        }
    
        $.fn.allowTabChar = function() {
            if (this.jquery) {
                this.each(function() {
                    if (this.nodeType == 1) {
                        var nodeName = this.nodeName.toLowerCase();
                        if (nodeName == "textarea" || (nodeName == "input" && this.type == "text")) {
                            allowTabChar(this);
                        }
                    }
                })
            }
            return this;
        }
    })(jQuery);
    $(function() {
        $("#indata").allowTabChar();
    });


    $("#annoMode").change(function(){
        if ($('#indata').is(':visible')) {
            updateIndataTable();
        } else {
            updateIndata();
        }
        $('.annoField').hide();
        $('#' + $('#annoMode').val()).show();
    })
    $('#highlight').on('input', function() {
        $('#onlyHighlighted').attr('disabled', $(this).val().length <= 0);
        updateIndataTable();
        keyUpFunc();
    });
    $('#basicDep').change(keyUpFunc)
    $('#enhancedDep').change(function(){ 
        $('#onlyMultipleEnhanced').attr('disabled', !$(this).is(':checked'))
        keyUpFunc() 
    })
    $('#onlyHighlighted').change(keyUpFunc)
    $('#onlyMultipleEnhanced').change(keyUpFunc)

    $('#jumpGo').click(function(){
        var sentenceId = $('#jumpText').val().trim();
        if (sentenceId.length) {
            if (map_sent_id.hasOwnProperty(sentenceId)) {
                sentenceId = map_sent_id[sentenceId] + 1;
            }
            nextSenSent(sentenceId)
        }
    })

    $("#jumpText").keyup(function(event) {
        if (event.keyCode === 13) {
            $("#jumpGo").click();
        }
    });

    var urlParams = new URLSearchParams(window.location.search);
    var text = urlParams.get('text');
    var highlight = urlParams.get("highlight");
    if (highlight) {
        $('#highlight').val(highlight);
    }
    if (text) {
        $('#indata').val(text);
        var hasEnhancedDeps = text.split("\n").some(line => {
            var columns = line.split("\t");
            return columns[8] && columns[8] !== "_";
        });

        if (hasEnhancedDeps) {
            $('#basicDep').attr('checked', false).change();
            $('#enhancedDep').attr('checked', true).change();
        } else {
            $('#basicDep').attr('checked', true).change();
            $('#enhancedDep').attr('checked', false).change();
        }
        if (urlParams.get('focus') === 'true') {
            var embedding = $('.embedding').detach();
            $('body > *').hide();
            embedding.appendTo('body').show();
        }
        keyUpFunc();
    }
});

var format = "";

//Listener to Load file
document.getElementById('filename').addEventListener('change', loadFromFile, false);

document.addEventListener('keydown', (event) => {
    if (event.ctrlKey && event.key == "Enter") {
        $('#updateVisBtn').click();
        event.preventDefault();
        } else if (event.ctrlKey && event.altKey && event.key === "ArrowRight") {
        document.getElementById('nextSenBtn').click();
        event.preventDefault();
        } else if (event.ctrlKey && event.altKey && event.key === "ArrowLeft") {
        document.getElementById('prevSenBtn').click();
        event.preventDefault();
        }
});

//Load Corpora from file
var contents = "";
var map_sent_id = {};
function loadFromFile(e) {
    contents = "";
    var file = e.target.files[0];
    if (!file) {
        return;
    }
    if (!file.name.endsWith('.conllu')) {
        alert("Only .conllu files are allowed.");
        return;
    }
    var reader = new FileReader();
    reader.onload = function(e) {
        contents = e.target.result.trim();
        contents.split("\n\n").forEach((block, index) => {
            const sentIdLine = block.split("\n").find(line => line.startsWith("# sent_id = "));
            if (sentIdLine) {
                const sentId = sentIdLine.split("= ")[1].trim();
                map_sent_id[sentId] = index;
            }
        });
        contents.split("\n").some(line => {
            if (line.includes('\t')) {
                if (line.split("\t")[8] === "_") {
                    $('#enhancedDep').attr('checked', false).change();
                    $('#basicDep').attr('checked', true).change();
                } else {
                    $('#basicDep').attr('checked', false).change();
                    $('#enhancedDep').attr('checked', true).change();
                }
                return true; // Stop further iteration
            }
            return false; // Continue iteration
        });
        loadDataInIndex();
    };
    
    reader.readAsText(file);
    $('#exportBtn').prop("disabled", false);
    $('#updateVisBtn').prop("disabled", false);
    $('#jumpGo').prop("disabled", false);
    $('#jumpText').prop("disabled", false);
}

var availablesentences = 0;
var currentsentence = 0;
var results = new Array();
		
function loadDataInIndex() {
	results = [];
    availablesentences = 0;
    currentsentence = 0;
    var splitted = contents.split("\n\n");
    availablesentences = splitted.length;
			
    if (availablesentences == 1 || availablesentences == 0) {
        document.getElementById('nextSenBtn').disabled = true;
    } else {
		document.getElementById('nextSenBtn').disabled = false;
	}
			
    for (var i = 0; i < splitted.length; ++i) {
        var check = splitted[i];
        results.push(check);
    }
    showDataIndiv();
}

function showDataIndiv() {
	document.getElementById('indata').value = (results[currentsentence]);
    updateIndataTable();
	document.getElementById('currentsen').innerHTML = (currentsentence+1);
	document.getElementById('totalsen').innerHTML = availablesentences;
    keyUpFunc();
}

function updateIndataTable() {
    tableHtml = ""
    tokens = $('#indata').val().trim().split("\n")

    for (let i = 0; i < tokens.length; i++) {
        let highlight = "";
        if ($('#highlight').val().trim().length && /\t/.test(tokens[i])) {
            const highlights = $('#highlight').val().trim().split(",");
            for (let h of highlights) {
                if (h.trim().length === 0) {
                    continue;
                }
                if (tokens[i].toLowerCase().includes(h.trim().toLowerCase())) {
                    highlight = "style='background-color:lightyellow;'";
                    break;
                }
            }
        }
        tableHtml += `<tr class='annoRow' ${highlight}>`;
    
        if (!/\t/.test(tokens[i])) {
            tableHtml += `<td class='annoCell' colspan=42 spellcheck=false contenteditable=true>${tokens[i]}</td>`;
        } else {
            const cols = tokens[i].split("\t");
            for (let j = 0; j < cols.length; j++) {
                tableHtml += `<td class='annoCell' spellcheck=false contenteditable=true>${cols[j]}</td>`;
            }
        }
    
        tableHtml += "</tr>";
    }
    $('#indataTable').html(tableHtml);
    $('.annoCell').on('input', function() {
        updateIndata();
    });
    $('.annoCell').on('input', function() {
        $(this).css('background-color', '#90EE90');
    });
}

function updateIndata() {
    text = ""
    tokens = $(".annoRow")

    tokens.each(function() {
        let token = $(this).children(".annoCell");
    
        token.each(function() {
            text += $(this).text();
            text += "\t";
        });
    
        text = text.trim() + "\n";
    });

    text = text.trim();
    
    $('#indata').val(text);
    keyUpFunc();
}

function prevSenSent() {
	results[currentsentence] = document.getElementById("indata").value;
    currentsentence--;
    if (currentsentence < (availablesentences - 1)) {
        document.getElementById("nextSenBtn").disabled = false;
    }
    if (currentsentence == 0) {
        document.getElementById("prevSenBtn").disabled = true;
    }
    showDataIndiv();
}

//When Navigate to next item
function nextSenSent(goTo=false) {
	results[currentsentence] = document.getElementById("indata").value;
    if (!goTo) {
        currentsentence++;
    } else {
        try {
            goTo = parseInt(goTo);
            if (goTo > 0 && goTo <= availablesentences) {
                currentsentence = goTo-1;
            } else {
                window.alert("Invalid sentence number or sent_id: " + $('#jumpText').val());
            }
        } catch (error) {
            window.alert("Invalid sentence number or sent_id: " + $('#jumpText').val());
        }
    }
    if (currentsentence == (availablesentences - 1)) {
        document.getElementById("nextSenBtn").disabled = true;
    } else {
        document.getElementById("nextSenBtn").disabled = false;
    }
    if (currentsentence > 0) {
        document.getElementById("prevSenBtn").disabled = false;
    }
    showDataIndiv();
}

//Export Corpora to file
function exportCorpora() {
    var type = ".txt";
    if (format == "CoNLL-U") {
        type = ".conllu";
    }
			
	results[currentsentence] = document.getElementById("indata").value;
	var finalcontent = "";
	for(var x=0; x < results.length; x++){
		finalcontent = finalcontent + results[x];
		if(x != ((results.length)-1)){
			finalcontent = finalcontent + "\n\n";
		}
	}		
    finalcontent = finalcontent.trim() + "\n\n"
    
    var link = document.createElement('a');
    var mimeType = 'text/plain';
    link.setAttribute('download', 'corpus' + type);
    link.setAttribute('href', 'data:' + mimeType + ';charset=utf-8,' + encodeURIComponent(finalcontent));
    link.click();
}
		
//KeyUp function
function keyUpFunc() {
    var content = $("#indata").val();
    var firstWord = content.replace(/\n/g, " ").split(" ")[0];

    // dealing with # comments at the beginning
    if (firstWord[0] === '#'){
        var following = 1;
        while (firstWord[0] === '#' && following < content.length){
            firstWord = content.split("\n")[following];
            following ++;
        }
    }
    if (firstWord.match(/"<.*/)) {
        format = "CG3";
        var cssClass = "language-conllx";
        var printContent = cgParse(content);
    } else if (firstWord.match(/1/)) {
        format = "CoNLL-U";
        var cssClass = "language-conllu";
        var printContent = conlluParse(content);
    } else {
        format = "SD"
        var cssClass = "language-sdparse";
        var printContent = content.replace(/\n/g, " ");
    }
    $("#dest").removeClass("language-sdparse").removeClass("language-conllu").removeClass("language-conllx");
    $("#dest").addClass(cssClass);
    $("#dest").html(printContent); // $("#source");
    Annodoc.activate(Config.bratCollData, Collections.listing);
    $(".show-hide-div").hide();
    
    // Update gloss table when content changes (with delay for BRAT to finish)
    setTimeout(function() {
        console.log("Delayed updateGlossTable call from keyUpFunc");
        updateGlossTable();
    }, 200);

    // ELVIS: FOR SCROLLING

    let isDragging = false;
    let startX;
    let scrollLeft;

    // Reference to the .embedding container
    const embeddingElement = document.querySelector('.embedding');

    // When mouse is pressed down on the .embedding but not its .span children
    embeddingElement.addEventListener('mousedown', (e) => {
        if (e.target.closest('.span, .arcs')) return; // Ignore if a .span is a parent of the target
        isDragging = true;
        startX = e.pageX;
        scrollLeft = document.body.scrollLeft || document.documentElement.scrollLeft;
    });

    // When mouse is released
    document.addEventListener('mouseup', () => {
        isDragging = false;
    });

    // In case the user drags out of the page and releases mouse
    document.addEventListener('mouseleave', () => {
        isDragging = false;
    });

    // When mouse moves
    embeddingElement.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        e.preventDefault(); // Prevent text selection, etc.

        // Calculate how far the mouse has moved from the initial position
        const xDiff = e.pageX - startX;

        // Update the horizontal scroll position of the body
        document.documentElement.scrollLeft += -xDiff * 0.1; // Adjust the multiplier for smoothness
    });
}

// Global variables for glosses
var currentGlosses = [];

function updateGlossTable() {
    if (typeof addDebugMessage === 'function') {
        addDebugMessage("=== updateGlossTable called ===");
    }
    
    var glossInput = $('#glossInput').val().trim();
    var words = extractWordsFromConllu($('#indata').val());
    
    if (typeof addDebugMessage === 'function') {
        addDebugMessage("Gloss input value: " + glossInput);
        addDebugMessage("Extracted words: " + JSON.stringify(words));
    }
    
    // Parse glosses from input (tab-separated or newline-separated)
    var glosses = [];
    if (glossInput) {
        if (glossInput.includes('\t')) {
            glosses = glossInput.split('\t');
        } else {
            glosses = glossInput.split(/\s+/);
        }
    }
    
    console.log("Parsed glosses:", glosses);
    
    // Update global glosses array
    currentGlosses = glosses;
    
    // Populate the table
    var tableBody = $('#glossTableBody');
    tableBody.empty();
    
    for (var i = 0; i < words.length; i++) {
        var word = words[i] || '';
        var gloss = glosses[i] || '';
        
        var row = $('<tr>');
        var wordCell = $('<td>').css({
            'border': '1px solid #ccc',
            'padding': '8px',
            'background-color': '#f9f9f9'
        }).text(word);
        
        var glossCell = $('<td>').css({
            'border': '1px solid #ccc',
            'padding': '4px'
        });
        
        var glossInput = $('<input>').attr({
            'type': 'text',
            'value': gloss,
            'data-index': i,
            'style': 'width: 100%; border: none; padding: 4px;'
        }).on('input', function() {
            var index = $(this).data('index');
            var value = $(this).val();
            while (currentGlosses.length <= index) {
                currentGlosses.push('');
            }
            currentGlosses[index] = value;
            // Trigger gloss re-rendering without full re-parse
            addGlossesToVisualization();
        });
        
        glossCell.append(glossInput);
        row.append(wordCell).append(glossCell);
        tableBody.append(row);
    }
    
    console.log("Table populated with", words.length, "rows");
    
    // Add glosses to visualization after updating table
    setTimeout(function() {
        console.log("Triggering addGlossesToVisualization with delay...");
        addGlossesToVisualization();
    }, 100);
}

function extractWordsFromConllu(conlluText) {
    var words = [];
    var lines = conlluText.split('\n');
    
    for (var i = 0; i < lines.length; i++) {
        var line = lines[i].trim();
        if (line && !line.startsWith('#') && line.includes('\t')) {
            var columns = line.split('\t');
            if (columns.length >= 2 && !columns[0].includes('-') && !columns[0].includes('.')) {
                words.push(columns[1]); // FORM column
            }
        }
    }
    
    return words;
}

function conlluParse(text) {
    var tokens = text.split("\n").filter(function(x) {
        var splitTokens = x.split("\t");
        return (x.indexOf("\t") === -1) || (splitTokens[0].indexOf(".") === -1) || $('#enhancedDep').is(":checked");
    });
    
    // Track word index for glosses
    var wordIndex = 0;
    for (let i = 0; i < tokens.length; i++) {
        let line = tokens[i];

        if (line.includes('\t')) {
            let token = line.split("\t");
            
            // Track word index for glosses (only for actual words, not multi-word tokens or empty nodes)
            if (token[0] && !token[0].includes('-') && !token[0].includes('.')) {
                wordIndex++;
            }

            // Highlight do token independe das outras opções
            if ($('#highlight').val().trim().length) {
                const highlights = $('#highlight').val().trim().split(',');
                for (let highlight of highlights) {
                    if (highlight.trim().length === 0) {
                        continue;
                    }
                    if (line.toLowerCase().includes(highlight.trim().toLowerCase())) {
                        tokens[0] = '# visual-style ' + token[0] + ' bgColor:lightyellow' + "\n" + tokens[0];
                        break;
                    }
                }
            }
            // Se mostrar só múltiplas enhanced, precisa ser antes de colorir enhanced
            if ($('#enhancedDep').is(':checked') && $('#onlyMultipleEnhanced').is(':checked') && token[8].indexOf('|') == -1) {
                token[8] = "_";
            }
            // Se mostrar só highlighted, precisa ser antes de colorir enhanced
            if ($('#highlight').val().trim().length && $("#onlyHighlighted").is(":checked")) {
                const highlights = $('#highlight').val().trim().split(',');
                let isHighlighted = false;
                for (let highlight of highlights) {
                    if (line.includes(highlight.trim())) {
                        isHighlighted = true;
                        break;
                    }
                }
                if (!isHighlighted) {
                    token[6] = "_";
                    token[7] = "_";
                    token[8] = "_";
                }
            }
            // Só colorir basic se tiver enhanced mas não estiver marcada para visualizar, por isso preciso fazer isso antes de remover as enhanced
            if (token[8] !== "_"){
                if (token[8].split("|").map(x => x.split(":").slice(0, 2).join(":")).indexOf(`${token[6]}:${token[7].split(":")[0]}`) === -1){
                    head = token[6]
                    label = token[7]
                    tokens[0] = `# visual-style ${head} ${token[0]} ${label} color:red\n` + tokens[0];
                }
            }
            // Se não mostrar enhanced, precisa ser antes de colorir enhanced
            if (!$('#enhancedDep').is(":checked")) {
                token[8] = "_";
            }
            // Só colorir enhanced se tiver visualização de enhanced, e precisa ser antes de remover basic deps pra aproveitar lista de novas relações
            if (token[8] !== "_") {
                for (let dep of token[8].split("|")) {
                    if (dep.split(":").splice(0, 2).join(":") !== `${token[6]}:${token[7].split(":")[0]}`) {
                        deps = dep.split(/:(.*)/s);
                        head = deps[0]
                        label = deps[1]
                        tokens[0] = `# visual-style ${head} ${token[0]} ${label} color:red\n` + tokens[0];
                    }
                }
            }
            // Só posso tirar as basic depois de colorir as enhanced
            if (!$('#basicDep').is(":checked")) {
                token[6] = "_";
                token[7] = "_";
            }
            // Apagar basic que são iguais enhanced
            if ($('#enhancedDep').is(":checked") && $('#basicDep').is(':checked')) {
                if (token[8].split("|").indexOf(`${token[6]}:${token[7]}`) !== -1){
                    token[6] = "_";
                    token[7] = "_";
                }
            }
            tokens[i] = token.join("\t");
        }
    }
    var result = tokens.join("\n");
    
    // Add glosses as a second line after BRAT processing
    setTimeout(function() {
        addGlossesToVisualization();
    }, 100);
    
    return result;
}

function addGlossesToVisualization() {
    console.log("=== addGlossesToVisualization called ===");
    console.log("Dispatcher available:", typeof Dispatcher !== 'undefined');
    console.log("Dispatcher count:", typeof Dispatcher !== 'undefined' ? Dispatcher.dispatchers.length : 0);
    
    // Always use fallback timing since BRAT event might not fire reliably
    console.log("Using direct timing approach");
    setTimeout(function() {
        console.log("Timeout fired, calling addGlossesAfterRendering");
        addGlossesAfterRendering();
    }, 300);
    
    // Also try the dispatcher approach as backup
    if (typeof Dispatcher !== 'undefined' && Dispatcher.dispatchers.length > 0) {
        console.log("Also setting up BRAT dispatcher listener");
        try {
            Dispatcher.dispatchers[0].on('doneRendering', function() {
                console.log("BRAT doneRendering event fired");
                setTimeout(function() {
                    addGlossesAfterRendering();
                }, 50);
            });
        } catch (e) {
            console.warn("Could not set up dispatcher listener:", e);
        }
    }
}

function addGlossesAfterRendering() {
    console.log("=== addGlossesAfterRendering called ===");
    console.log("Current glosses:", currentGlosses);
    
    // Remove any existing glosses first
    var existingGlosses = $('.embedding svg .gloss-text');
    console.log("Removing", existingGlosses.length, "existing glosses");
    existingGlosses.remove();
    
    if (!currentGlosses || currentGlosses.length === 0) {
        console.log("No glosses to add");
        return;
    }
    
    console.log("SVG elements found:", $('.embedding svg').length);
    console.log("Text groups found:", $('.embedding svg g.text').length);
    console.log("Text elements found:", $('.embedding svg g.text text').length);
    
    // Remove the second text row (the unwanted sentence display)
    $('.embedding svg g.text text').each(function(index) {
        if (index > 0) { // Remove all text elements except the first
            $(this).remove();
        }
    });
    
    // Also remove the second background rectangle and adjust SVG height
    $('.embedding svg g.background rect').each(function(index) {
        if (index > 0) { // Remove background rectangles for extra rows
            $(this).remove();
        }
    });
    
    // Remove extra sentence groups/transforms
    $('.embedding svg g[transform*="translate(0, 82)"]').remove();
    
    // Find the first text row with word tokens and add glosses
    var wordIndex = 0;
    $('.embedding svg g.text text:first tspan').each(function() {
        var $tspan = $(this);
        var chunkId = $tspan.attr('data-chunk-id');
        
        if (chunkId !== undefined && wordIndex < currentGlosses.length) {
            var gloss = currentGlosses[wordIndex];
            if (gloss && gloss.trim()) {
                var wordText = $tspan.text().replace(/ˑ/g, '').trim(); // Remove word boundary markers
                var svg = $tspan.closest('svg')[0];
                
                if (svg) {
                    // Find the corresponding highlight rectangle for this word
                    var highlightRect = $(svg).find('g.highlight rect').eq(wordIndex);
                    
                    var x, y;
                    if (highlightRect.length > 0) {
                        // Use the center of the highlight rectangle
                        var rectX = parseFloat(highlightRect.attr('x'));
                        var rectWidth = parseFloat(highlightRect.attr('width'));
                        var rectY = parseFloat(highlightRect.attr('y'));
                        var rectHeight = parseFloat(highlightRect.attr('height'));
                        
                        x = rectX + (rectWidth / 2); // Center of the rectangle
                        y = rectY + rectHeight + 12; // Below the rectangle
                        
                        if (typeof addDebugMessage === 'function') {
                            addDebugMessage("Using rect center: x=" + x + " y=" + y + " for word '" + wordText + "'");
                        }
                    } else {
                        // Fallback to text position if no highlight rect found
                        x = parseFloat($tspan.attr('x'));
                        y = parseFloat($tspan.attr('y')) + 18;
                        
                        if (typeof addDebugMessage === 'function') {
                            addDebugMessage("Using text position: x=" + x + " y=" + y + " for word '" + wordText + "'");
                        }
                    }
                    
                    var glossElement = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                    glossElement.setAttribute('x', x);
                    glossElement.setAttribute('y', y);
                    glossElement.setAttribute('class', 'gloss-text');
                    glossElement.setAttribute('text-anchor', 'middle'); // Center the text
                    glossElement.setAttribute('style', 'font-size: 9px; fill: #666; font-style: italic; font-family: Arial, sans-serif;');
                    glossElement.textContent = gloss;
                    
                    // Find the text group to append to
                    var textGroup = svg.querySelector('g.text');
                    if (textGroup) {
                        textGroup.appendChild(glossElement);
                    } else {
                        svg.appendChild(glossElement);
                    }
                }
            }
            wordIndex++;
        }
    });
    
    console.log('Removed extra text rows and added', wordIndex, 'glosses to visualization');
}

// Debug function for testing SVG manipulation directly
function testSVGGloss() {
    console.log("=== Testing SVG Gloss Addition ===");
    var svg = $('.embedding svg')[0];
    if (!svg) {
        console.error("No SVG found");
        return;
    }
    
    var testText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    testText.setAttribute('x', '50');
    testText.setAttribute('y', '100');
    testText.setAttribute('class', 'test-gloss');
    testText.setAttribute('style', 'font-size: 12px; fill: red; font-weight: bold;');
    testText.textContent = 'TEST GLOSS';
    
    svg.appendChild(testText);
    console.log("Test gloss added to SVG");
    
    return testText;
}

function exportSVG() {
    var exportAction = function() {
        var svg = $('.embedding svg');
        if (svg.length === 0) {
            // Try alternative selectors
            svg = $('#dest svg');
            if (svg.length === 0) {
                svg = $('svg');
                if (svg.length === 0) {
                    alert("No SVG found to export. Please ensure a visualization is displayed first.");
                    return;
                }
            }
        }

        var serializer = new XMLSerializer();
        var svgString = serializer.serializeToString(svg[0]);
        
        // Ensure the SVG has a white background by adding/modifying the style attribute
        if (svgString.includes('style=')) {
            svgString = svgString.replace(/style="([^"]*)"/, 'style="background-color: white; $1"');
        } else {
            svgString = svgString.replace('<svg', '<svg style="background-color: white;"');
        }
        
        // The SVG already has background rectangles in the .background group
        // We'll style them with CSS instead of adding a new rectangle

        // Add the CSS styles to the SVG string
        var styles = '';
        
        // First, add inline styles from the HTML document
        var inlineStyles = '';
        $('style').each(function() {
            inlineStyles += $(this).text() + '\n';
        });
        
        // Then, extract relevant CSS rules from stylesheets
        var styleSheets = document.styleSheets;
        for (var i = 0; i < styleSheets.length; i++) {
            var rules;
            try {
                rules = styleSheets[i].cssRules || styleSheets[i].rules;
            } catch (e) {
                console.warn("Cannot access stylesheet: " + styleSheets[i].href, e);
                continue;
            }
            if (rules) {
                for (var j = 0; j < rules.length; j++) {
                    var rule = rules[j];
                    if (rule.cssText) {
                        // Include rules that are relevant to SVG elements or general styling
                        var ruleText = rule.cssText;
                        if (ruleText.includes('svg') || 
                            ruleText.includes('text') || 
                            ruleText.includes('rect') || 
                            ruleText.includes('path') || 
                            ruleText.includes('g.') || 
                            ruleText.includes('.background') ||
                            ruleText.includes('.highlight') ||
                            ruleText.includes('.span') ||
                            ruleText.includes('.arcs') ||
                            ruleText.includes('.sentnum') ||
                            ruleText.includes('font-') ||
                            ruleText.includes('fill') ||
                            ruleText.includes('stroke')) {
                            styles += ruleText + '\n';
                        }
                    }
                }
            }
        }
        
        // Add essential BRAT visualization styles from the actual CSS files
        var bratStyles = `
            /* Core SVG styles from style-vis.css */
            svg {
                width: 100%;
                height: 1px;
                border: none;
                font-size: 15px;
                background-color: white !important;
                background: white !important;
            }
            
            /* Background styles for BRAT visualization */
            .background rect {
                fill: white;
            }
            
            .background rect.background0 {
                fill: #ffffff;
            }
            
            .background rect.background1 {
                fill: #f8f8f8;
            }
            
            /* Text styles */
            text {
                font-size: 13px;
                font-family: 'Liberation Sans', Verdana, Arial, Helvetica, sans-serif;
            }
            
            /* Span text styles */
            .span text {
                font-size: 10px;
                text-anchor: middle;
                font-family: 'PT Sans Caption', sans-serif;
                pointer-events: none;
            }
            
            /* Span rectangle styles */
            .span rect {
                stroke-width: 0.75;
            }
            
            /* Arc styles */
            .arcs path {
                stroke: #989898;
                fill: none;
                stroke-width: 1;
            }
            
            .arcs .highlight path {
                stroke: red;
                stroke-width: 2;
            }
            
            /* Arc text styles */
            .arcs text {
                font-size: 9px;
                text-anchor: middle;
                font-family: 'PT Sans Caption', sans-serif;
            }
            
            /* Path styles */
            path {
                pointer-events: none;
            }
            
            /* Glyph styles */
            .glyph {
                fill: #444444;
                font-family: sans-serif;
                font-weight: bold;
            }
            
            /* Sentence number styles (hidden) */
            .sentnum text {
                display: none;
            }
            
            .sentnum path {
                display: none;
            }
            
            /* Span path styles */
            .span path {
                fill: none;
            }
            
            .span path.curly {
                stroke-width: 0.5;
            }
            
            .span path.boxcross {
                stroke: black;
                opacity: 0.5;
            }
            
            /* Gloss text styles */
            .gloss-text {
                font-size: 9px !important;
                fill: #666 !important;
                text-anchor: middle !important;
                font-style: italic !important;
                font-family: Arial, sans-serif !important;
            }
        `;
        
        // Combine all styles
        styles = inlineStyles + styles + bratStyles;

        // Skip font embedding when running from file:// protocol to avoid CORS issues
        var isFileProtocol = window.location.protocol === 'file:';
        
        if (isFileProtocol) {
            // For file:// protocol, just embed CSS without font data URLs
            var fontStyles = '';
            for (var i = 0; i < webFontURLs.length; i++) {
                var fontName = webFontURLs[i].split('/').pop().split('.')[0].split('-')[0];
                fontStyles += "@font-face { font-family: '" + fontName + "'; src: url('" + webFontURLs[i] + "'); }\n";
            }
            
            svgString = svgString.replace('</svg>', '<style>' + fontStyles + styles + '</style></svg>');
            
            var blob = new Blob([svgString], {type: "image/svg+xml;charset=utf-8"});
            var url = URL.createObjectURL(blob);

            var link = document.createElement('a');
            link.setAttribute('href', url);
            link.setAttribute('download', 'graph.svg');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else {
            // For http/https protocols, try to embed fonts as data URLs
            var fontPromises = webFontURLs.map(function(url) {
                return fetch(url)
                    .then(response => response.blob())
                    .then(blob => new Promise((resolve, reject) => {
                        var reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result);
                        reader.onerror = reject;
                        reader.readAsDataURL(blob);
                    }))
                    .catch(err => {
                        console.warn('Failed to load font:', url, err);
                        return null;
                    });
            });

            Promise.all(fontPromises).then(function(fontData) {
                var fontStyles = '';
                for (var i = 0; i < webFontURLs.length; i++) {
                    var fontName = webFontURLs[i].split('/').pop().split('.')[0].split('-')[0];
                    if (fontData[i]) {
                        fontStyles += "@font-face { font-family: '" + fontName + "'; src: url('" + fontData[i] + "'); }\n";
                    } else {
                        fontStyles += "@font-face { font-family: '" + fontName + "'; src: url('" + webFontURLs[i] + "'); }\n";
                    }
                }

                svgString = svgString.replace('</svg>', '<style>' + fontStyles + styles + '</style></svg>');

                var blob = new Blob([svgString], {type: "image/svg+xml;charset=utf-8"});
                var url = URL.createObjectURL(blob);

                var link = document.createElement('a');
                link.setAttribute('href', url);
                link.setAttribute('download', 'graph.svg');
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            });
        }
    };

    if (typeof Dispatcher === 'undefined' || Dispatcher.dispatchers.length === 0) {
        // If the dispatcher is not yet available, wait for it.
        setTimeout(function() {
            Dispatcher.dispatchers[0].on('doneRendering', function() {
                exportAction();
            });
        }, 100);
    } else {
        // If the dispatcher is available, use it directly.
        Dispatcher.dispatchers[0].on('doneRendering', function() {
                exportAction();
            });
    }

    // As a fallback, if the event is not caught, export after a timeout.
    setTimeout(function() {
        exportAction();
    }, 1000);
}