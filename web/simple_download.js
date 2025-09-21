/**
 * RGBLineArtDividerFast Web Extension
 * Simple manual input with memory for PSD download
 */

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "ComfyUI-fixableflow.RGBLineArtDividerFast",
    
    async nodeCreated(node) {
        // Only apply to RGBLineArtDividerFast nodes  
        if (node.comfyClass === "RGBLineArtDividerFast") {
            console.log("RGBLineArtDividerFast: Adding download button");
            
            // Store the last known filename
            let lastFilename = localStorage.getItem('rgbDividerLastPSD') || null;
            
            // Add download button
            const downloadButton = node.addWidget(
                "button",
                "Download PSD",
                lastFilename ? `⬇ Download: ${lastFilename}` : "⬇ Download PSD",
                () => {
                    // Prompt with the last known filename as default
                    const filename = prompt(
                        "Enter the PSD filename from server console:\n" +
                        "(Example: output_rgb_fast_normal_G7kZ3I7mV9.psd)",
                        lastFilename || ""
                    );
                    
                    if (filename && filename.includes('.psd')) {
                        // Extract just the filename from full path if needed
                        const cleanFilename = filename.split('/').pop() || filename.split('\\').pop() || filename;
                        
                        console.log("Downloading:", cleanFilename);
                        
                        // Save for next time
                        lastFilename = cleanFilename;
                        localStorage.setItem('rgbDividerLastPSD', cleanFilename);
                        
                        // Update button text
                        downloadButton.name = `⬇ Download: ${cleanFilename}`;
                        
                        // Create download URL
                        const downloadUrl = `/view?filename=${encodeURIComponent(cleanFilename)}&type=output`;
                        
                        // Create and click download link
                        const link = document.createElement('a');
                        link.href = downloadUrl;
                        link.download = cleanFilename;
                        link.style.display = 'none';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        
                        console.log("Download initiated for:", cleanFilename);
                    }
                }
            );
            
            // Style the button
            downloadButton.color = "#4CAF50";
            downloadButton.bgcolor = "#2E7D32";
            
            // Listen for messages from websocket to capture PSD filename
            const originalOnExecuted = node.onExecuted;
            node.onExecuted = function(message) {
                console.log("Node executed, output:", message);
                
                if (originalOnExecuted) {
                    originalOnExecuted.apply(this, arguments);
                }
                
                // Try to find PSD filename in the output
                if (message) {
                    // Check if it's an array with 4 elements (our expected output)
                    if (Array.isArray(message) && message.length > 3) {
                        const lastItem = message[3];
                        if (lastItem && typeof lastItem === 'string' && lastItem.includes('.psd')) {
                            console.log("Found PSD filename in output:", lastItem);
                            lastFilename = lastItem;
                            localStorage.setItem('rgbDividerLastPSD', lastItem);
                            downloadButton.name = `⬇ Download: ${lastItem}`;
                        }
                    }
                    // Check for nested arrays (ComfyUI sometimes wraps outputs)
                    else if (Array.isArray(message)) {
                        message.forEach(item => {
                            if (Array.isArray(item) && item.length > 0) {
                                const str = item[0];
                                if (typeof str === 'string' && str.includes('.psd')) {
                                    console.log("Found PSD filename in nested array:", str);
                                    lastFilename = str;
                                    localStorage.setItem('rgbDividerLastPSD', str);
                                    downloadButton.name = `⬇ Download: ${str}`;
                                }
                            }
                        });
                    }
                }
            };
            
            // Also monitor WebSocket messages
            const ws = api.socket;
            if (ws) {
                const originalOnMessage = ws.onmessage;
                ws.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        
                        // Check for execution complete messages
                        if (data.type === 'executed' && data.data && data.data.node === String(node.id)) {
                            console.log("Execution complete for our node:", data.data);
                            
                            // Check if output contains our PSD path
                            if (data.data.output && Array.isArray(data.data.output.psd_path)) {
                                const psdPath = data.data.output.psd_path[0];
                                if (psdPath && psdPath.includes('.psd')) {
                                    const filename = psdPath.split('/').pop() || psdPath.split('\\').pop() || psdPath;
                                    console.log("Found PSD path in WebSocket message:", filename);
                                    lastFilename = filename;
                                    localStorage.setItem('rgbDividerLastPSD', filename);
                                    downloadButton.name = `⬇ Download: ${filename}`;
                                }
                            }
                        }
                        
                        // Check for console output messages
                        if (data.type === 'console' && data.data && typeof data.data === 'string') {
                            const consoleMsg = data.data;
                            if (consoleMsg.includes('PSD file saved:')) {
                                const match = consoleMsg.match(/([^/\\]+\.psd)/);
                                if (match) {
                                    const filename = match[1];
                                    console.log("Found PSD filename in console output:", filename);
                                    lastFilename = filename;
                                    localStorage.setItem('rgbDividerLastPSD', filename);
                                    downloadButton.name = `⬇ Download: ${filename}`;
                                }
                            }
                        }
                    } catch (e) {
                        // Ignore parse errors
                    }
                    
                    // Call original handler
                    if (originalOnMessage) {
                        originalOnMessage.apply(this, arguments);
                    }
                };
            }
            
            console.log("RGBLineArtDividerFast: Download button ready");
        }
    }
});
