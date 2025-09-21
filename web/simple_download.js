/**
 * RGBLineArtDividerFast Web Extension
 * Auto-captures PSD filename and enables one-click download
 */

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "ComfyUI-fixableflow.RGBLineArtDividerFast",
    
    async nodeCreated(node) {
        // Only apply to RGBLineArtDividerFast nodes
        if (node.comfyClass === "RGBLineArtDividerFast") {
            console.log("RGBLineArtDividerFast: Adding auto-download button");
            
            // Store the last generated filename
            let currentFilename = null;
            
            // Add download button
            const downloadButton = node.addWidget(
                "button",
                "Download PSD",
                "⬇ Download PSD (Run workflow first)",
                () => {
                    if (currentFilename) {
                        console.log("Downloading:", currentFilename);
                        
                        // Create download URL
                        const downloadUrl = `/view?filename=${encodeURIComponent(currentFilename)}&type=output`;
                        
                        // Create and click download link
                        const link = document.createElement('a');
                        link.href = downloadUrl;
                        link.download = currentFilename;
                        link.style.display = 'none';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        
                        console.log("Download initiated for:", currentFilename);
                    } else {
                        alert("No PSD file available. Please run the workflow first.");
                    }
                }
            );
            
            // Style the button - initially disabled appearance
            downloadButton.color = "#888888";
            downloadButton.bgcolor = "#333333";
            
            // Override onExecuted to capture the filename automatically
            const originalOnExecuted = node.onExecuted;
            node.onExecuted = function(message) {
                console.log("Node executed, checking for PSD path...");
                
                if (originalOnExecuted) {
                    originalOnExecuted.apply(this, arguments);
                }
                
                // Try to extract filename from the 4th output (psd_path)
                if (node.outputs && node.outputs.length > 3) {
                    // Wait a bit for the value to be set
                    setTimeout(() => {
                        // Check if the node has a widgets_values array
                        if (node.widgets_values && node.widgets_values.length > 0) {
                            // The last widget value might be the filename
                            const lastValue = node.widgets_values[node.widgets_values.length - 1];
                            if (lastValue && typeof lastValue === 'string' && lastValue.includes('.psd')) {
                                updateFilename(lastValue);
                            }
                        }
                    }, 100);
                }
            };
            
            // Function to update filename and button state
            function updateFilename(path) {
                // Extract just the filename from the full path
                if (path && path.includes('.psd')) {
                    currentFilename = path.split('/').pop() || path.split('\\').pop() || path;
                    console.log("PSD filename captured:", currentFilename);
                    
                    // Update button appearance to show it's ready
                    downloadButton.name = `⬇ Download: ${currentFilename}`;
                    downloadButton.color = "#4CAF50";
                    downloadButton.bgcolor = "#2E7D32";
                }
            }
            
            // Listen for execution messages from the API
            api.addEventListener("executed", (evt) => {
                const nodeId = evt.detail.node;
                if (nodeId === node.id) {
                    console.log("Node execution completed:", evt.detail);
                    
                    // Check if output contains filename
                    if (evt.detail.output && evt.detail.output.psd_path) {
                        const paths = evt.detail.output.psd_path;
                        if (Array.isArray(paths) && paths.length > 0) {
                            updateFilename(paths[0]);
                        } else if (typeof paths === 'string') {
                            updateFilename(paths);
                        }
                    }
                }
            });
            
            // Also listen for execution updates
            api.addEventListener("execution", (evt) => {
                if (evt.detail && evt.detail.output && evt.detail.node === node.id) {
                    console.log("Execution update for node:", evt.detail);
                }
            });
            
            // Monitor for changes in connected nodes
            const originalOnConnectionsChange = node.onConnectionsChange;
            node.onConnectionsChange = function(type, index, connected, link_info) {
                if (originalOnConnectionsChange) {
                    originalOnConnectionsChange.apply(this, arguments);
                }
                
                // If it's an output connection for the psd_path (index 3)
                if (type === 2 && index === 3 && connected && link_info) {
                    console.log("PSD path output connected:", link_info);
                    
                    // Try to get the value after a short delay
                    setTimeout(() => {
                        const graph = app.graph;
                        if (graph && graph.links && link_info) {
                            const link = graph.links[link_info.id];
                            if (link && link.data) {
                                console.log("Link data:", link.data);
                                if (typeof link.data === 'string' && link.data.includes('.psd')) {
                                    updateFilename(link.data);
                                }
                            }
                        }
                    }, 100);
                }
            };
            
            // Store reference to button on the node
            node.psdDownloadButton = downloadButton;
            node.getCurrentFilename = () => currentFilename;
            
            console.log("RGBLineArtDividerFast: Auto-download button added");
        }
    }
});

// Also try to intercept console messages to capture the filename
(function() {
    const originalLog = console.log;
    console.log = function() {
        // Check if this is a PSD file saved message
        const message = Array.from(arguments).join(' ');
        if (message.includes('PSD file saved:') || message.includes('Returning PSD path:')) {
            const match = message.match(/([^/\\]+\.psd)/);
            if (match) {
                const filename = match[1];
                console.warn("Captured PSD filename from console:", filename);
                
                // Find all RGBLineArtDividerFast nodes and update their filenames
                if (app.graph && app.graph.nodes) {
                    app.graph.nodes.forEach(node => {
                        if (node.comfyClass === 'RGBLineArtDividerFast' && node.psdDownloadButton) {
                            if (node.getCurrentFilename && !node.getCurrentFilename()) {
                                // Only update if no filename is set yet
                                node.psdDownloadButton.name = `⬇ Download: ${filename}`;
                                node.psdDownloadButton.color = "#4CAF50";
                                node.psdDownloadButton.bgcolor = "#2E7D32";
                            }
                        }
                    });
                }
            }
        }
        
        // Call the original console.log
        originalLog.apply(console, arguments);
    };
})();
