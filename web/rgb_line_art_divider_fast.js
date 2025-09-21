/**
 * RGBLineArtDividerFast Web Extension
 * Adds a download button to the node for PSD file download
 */

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "ComfyUI-fixableflow.RGBLineArtDividerFast",
    
    async nodeCreated(node) {
        // Only apply to RGBLineArtDividerFast nodes
        if (node.comfyClass !== "RGBLineArtDividerFast") {
            return;
        }
        
        // Store the PSD path when the node executes
        node.psdPath = null;
        
        // Add custom widget for download button
        const downloadWidget = node.addWidget(
            "button",
            "Download PSD",
            null,
            () => {
                if (node.psdPath) {
                    // Create download URL
                    const filename = node.psdPath.split('/').pop();
                    const downloadUrl = `/view?filename=${filename}&subfolder=&type=output&folder_type=ComfyUI-LayerDivider/output`;
                    
                    // Create a temporary link and click it
                    const link = document.createElement('a');
                    link.href = downloadUrl;
                    link.download = filename;
                    link.style.display = 'none';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    // Show success message
                    app.ui.dialog.show(`Downloading: ${filename}`);
                } else {
                    app.ui.dialog.show("No PSD file available. Please run the workflow first.");
                }
            },
            { 
                serialize: false 
            }
        );
        
        // Style the button
        downloadWidget.disabled = true;
        downloadWidget.bgColor = "#444444";
        
        // Override the onExecuted method to capture the PSD path
        const originalOnExecuted = node.onExecuted;
        node.onExecuted = function(output) {
            // Call original handler if it exists
            if (originalOnExecuted) {
                originalOnExecuted.call(this, output);
            }
            
            // Extract PSD path from output (4th element in the output array)
            if (output && output.psd_path && output.psd_path[0]) {
                node.psdPath = output.psd_path[0];
                downloadWidget.disabled = false;
                downloadWidget.bgColor = "#4CAF50";
                downloadWidget.name = `Download PSD (${node.psdPath.split('/').pop()})`;
            }
        };
        
        // Reset button when node is cleared
        const originalOnClear = node.onClear;
        node.onClear = function() {
            if (originalOnClear) {
                originalOnClear.call(this);
            }
            node.psdPath = null;
            downloadWidget.disabled = true;
            downloadWidget.bgColor = "#444444";
            downloadWidget.name = "Download PSD";
        };
    },
});
