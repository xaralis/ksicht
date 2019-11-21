// Import CSS bundle.
require('../sass/main.scss');

// BulmaJS - initialize JS handlers for the Bulma CSS framework.
// Only the plugins you need
import Navbar from '@vizuaalog/bulmajs/src/plugins/navbar';
import Notification from '@vizuaalog/bulmajs/src/plugins/notification';
import Tabs from '@vizuaalog/bulmajs/src/plugins/tabs';

// Upload fields
window.onload = function() {
    // Apply this to all upload fields
    const uploadFields = document.querySelectorAll(".file");

    for (let i = 0; i < uploadFields.length; i++) {
        let uploadField = uploadFields[i];
        let input = uploadField.querySelector(".file-input");
        let filename = uploadField.querySelector(".file-name");

        input.onchange = function() {
            if (input.files.length) {
                filename.textContent = input.files[0].name;
                uploadField.classList.add("has-name");
                filename.classList.remove("is-hidden");
            }
        }

        input.onchange();
    }
};
