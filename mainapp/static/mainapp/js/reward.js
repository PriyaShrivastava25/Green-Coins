function redeemReward(cost, rewardName) {
    fetch('/redeem/', {  
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify({
            reward: rewardName,
            cost: cost
        })
    })
    .then(response => response.json())
    .then(data => {
        const messageDiv = document.getElementById("message");

        if (data.success) {
            alert("Reward Redeemed!");

            if (messageDiv) {
                messageDiv.style.color = 'green';
                messageDiv.innerHTML = `Successfully redeemed: ${rewardName}<br>`;

            
             }
        } else {
            alert("Failed to redeem: " + data.message);
            if (messageDiv) {
                messageDiv.style.color = 'red';
                messageDiv.innerText = "Failed: " + data.message;
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("Something went wrong. Error: " + error);
        const messageDiv = document.getElementById("message");
        if (messageDiv) {
            messageDiv.style.color = 'red';
            messageDiv.innerText = "Something went wrong. Try again later.";
        }
    });
}

function getCSRFToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const trimmed = cookie.trim();
        if (trimmed.startsWith(name + '=')) {
            return trimmed.substring(name.length + 1);
        }
    }
    return '';
}






     