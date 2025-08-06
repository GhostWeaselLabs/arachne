// Meridian Halo Wrapper
// This script ensures the MeridianHalo object is properly exposed to the global scope

(function() {
    'use strict';
    
    // Wait for the main script to load and execute
    function waitForMeridianHalo() {
        // Check if the script has created the MeridianHalo object
        if (typeof window.MeridianHalo !== 'undefined') {
            console.log('[halo-wrapper] MeridianHalo found in global scope');
            return;
        }
        
        // Check if the script has been loaded and executed
        // Look for any global objects that might contain MeridianHalo
        var globalObjects = Object.keys(window);
        var foundHalo = false;
        
        for (var i = 0; i < globalObjects.length; i++) {
            var key = globalObjects[i];
            var obj = window[key];
            
            if (obj && typeof obj === 'object' && obj.MeridianHalo) {
                // Found MeridianHalo in a global object, expose it
                window.MeridianHalo = obj.MeridianHalo;
                console.log('[halo-wrapper] MeridianHalo exposed from', key);
                foundHalo = true;
                break;
            }
        }
        
        if (!foundHalo) {
            // Try to find it in the return value of the script
            // This is a fallback approach
            setTimeout(waitForMeridianHalo, 100);
        }
    }
    
    // Start checking after a short delay to allow the main script to load
    setTimeout(waitForMeridianHalo, 50);
})();
