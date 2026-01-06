document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("proofForm");
    const fileInput = document.getElementById("file");
    const claimedLat = document.getElementById("claimed_latitude");
    const claimedLon = document.getElementById("claimed_longitude");
    const liveLat = document.getElementById("live_latitude");
    const liveLon = document.getElementById("live_longitude");

    let gpsReady = false;
    let gpsError = false;

    // Disable live GPS 
    claimedLat.addEventListener("input", disableLiveIfManual);
    claimedLon.addEventListener("input", disableLiveIfManual);

    function disableLiveIfManual() {
        if (claimedLat.value.trim() !== "" || claimedLon.value.trim() !== "") {
            liveLat.value = "";
            liveLon.value = "";
            console.log("Manual lat/lon entered — live GPS disabled");
        }
    }

    // Fetch live GPS and store in hidden fields
    function fetchLiveGPS(callback) {
        if (!navigator.geolocation) {
            console.warn("Geolocation not supported.");
            gpsError = true;
            gpsReady = true;
            if (callback) callback();
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (pos) => {
                liveLat.value = pos.coords.latitude.toFixed(6);
                liveLon.value = pos.coords.longitude.toFixed(6);
                gpsReady = true;
                console.log(" Live GPS captured:", liveLat.value, liveLon.value);

                if (callback) callback();
            },
            (err) => {
                console.warn(" GPS Error:", err.message);
                gpsError = true;
                gpsReady = true;
                if (callback) callback();
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
    }

    // Fetch live GPS immediately on page load
    fetchLiveGPS();


    window.checkSize = function (input) {
        const file = input.files[0];
        if (!file) return;
        const maxSize = 12 * 1024 * 1024; 
        const infoDiv = document.getElementById("file-info");
        infoDiv.textContent = "";

        if (file.size > maxSize) {
            alert("Max file size is 12MB.");
            input.value = "";
        } else {
            infoDiv.textContent = `Selected File: ${file.name}`;
            infoDiv.style.color = "green";
        }
    };

    
    form.addEventListener("submit", function (e) {
        if (!fileInput.files.length) {
            alert("Please upload an image.");
            e.preventDefault();
            return;
        }

        
        if (!claimedLat.value && !claimedLon.value) {
            if (!gpsReady) {
                e.preventDefault();
                console.log(" Waiting for live GPS...");
                fetchLiveGPS(() => {
                    console.log("Submitting after GPS fetch...");
                    form.submit();
                });
                return;
            }
        }

        console.log("Form submitting with →", {
            claimedLat: claimedLat.value,
            claimedLon: claimedLon.value,
            liveLat: liveLat.value,
            liveLon: liveLon.value,
        });
    });
});



