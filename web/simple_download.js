/**
 * RGBLineArtDividerFast Web Extension
 * Adds a manual download button for PSD files
 */

import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "ComfyUI-fixableflow.RGBLineArtDividerFast",
    
    async nodeCreated(node) {
        // Only apply to RGBLineArtDividerFast nodes
        if (node.comfyClass === "RGBLineArtDividerFast") {
            console.log("RGBLineArtDividerFast: Adding download button");
            
            // Store the last known filename
            let lastFilename = null;
            
            // Add download button
            const downloadButton = node.addWidget(
                "button",
                "Download PSD",
                "Download PSD",
                () => {
                    console.log("Download button clicked");
                    
                    // Use the last known filename or prompt for input
                    let filename = lastFilename || prompt(
                        "Enter the PSD filename:\n" + 
                        "(You can find it in the server console after running the workflow)\n" +
                        "Example: output_rgb_fast_normal_abc123def.psd"
                    );
                    
                    if (filename && typeof filename === 'string') {
                        // Clean up the filename (remove path if present)
                        if (filename.includes('/')) {
                            filename = filename.split('/').pop();
                        } else if (filename.includes('\\')) {
                            filename = filename.split('\\').pop();
                        }
                        
                        console.log("Downloading:", filename);
                        
                        // Create download URL
                        const downloadUrl = `/view?filename=${encodeURIComponent(filename)}&type=output`;
                        
                        // Create and click download link
                        const link = document.createElement('a');
                        link.href = downloadUrl;
                        link.download = filename;
                        link.style.display = 'none';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        
                        // Store the filename for next time
                        lastFilename = filename;
                        
                        // Update button label
                        downloadButton.name = `Download: ${filename}`;
                        
                        console.log("Download initiated for:", filename);
                    }
                }
            );
            
            // Style the button
            downloadButton.color = "#4CAF50";
            downloadButton.bgcolor = "#333333";
            
            console.log("RGBLineArtDividerFast: Button added");
        }
    }
});
