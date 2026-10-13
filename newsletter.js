/* SUNOLICIOUS newsletter pop-up: submit to Mailchimp in the background and confirm on-brand, without sending visitors to a Mailchimp page.
   Uses Mailchimp's own JSONP endpoint (the form's action URL with /post -> /post-json). If anything fails, falls back to the normal form post in a new tab. */
(function () {
    var form = document.getElementById('mc-embedded-subscribe-form');
    if (!form) return;

    var css = document.createElement('style');
    css.textContent =
        '.nl-done{text-align:center;padding:1.2rem 0 .4rem}' +
        '.nl-done .nl-mark{font-size:1.75rem;font-weight:200;letter-spacing:4px;line-height:1.1;color:#fff;margin:0 0 .45rem}' +
        '.nl-done .nl-mark sup{font-size:.3em;letter-spacing:0}' +
        '.nl-done .nl-tag{font-size:.62rem;letter-spacing:2.5px;text-transform:uppercase;color:rgba(255,255,255,.6);margin:0 0 1.6rem}' +
        '.nl-done h3{font-size:1.15rem;font-weight:300;letter-spacing:3px;text-transform:uppercase;color:#fff;margin:0 0 1rem}' +
        '.nl-done p{font-size:.9rem;line-height:1.7;color:#fff;margin:0 0 1.6rem}' +
        '.nl-done button{padding:.7rem 1.8rem;background:transparent;color:#fff;border:1px solid rgba(255,255,255,.5);font-family:inherit;font-size:.7rem;letter-spacing:2px;text-transform:uppercase;font-weight:300;cursor:pointer;transition:all .3s ease}' +
        '.nl-done button:hover{background:rgba(255,255,255,.12);border-color:#fff}' +
        '.nl-error{margin:.9rem 0 0;font-size:.82rem;line-height:1.6;color:#ffd9a8;text-align:center}';
    document.head.appendChild(css);

    function serialize(f) {
        var out = [];
        Array.prototype.forEach.call(f.elements, function (el) {
            if (!el.name || el.disabled) return;
            if ((el.type === 'checkbox' || el.type === 'radio') && !el.checked) return;
            out.push(encodeURIComponent(el.name) + '=' + encodeURIComponent(el.value));
        });
        return out.join('&');
    }

    function plain(html) {
        var d = document.createElement('div');
        d.innerHTML = html || '';
        return (d.textContent || '').replace(/\s+/g, ' ').trim();
    }

    function showDone(box, title, message) {
        Array.prototype.forEach.call(box.children, function (c) {
            if (c.id !== 'closePopup' && !c.classList.contains('close-btn')) c.style.display = 'none';
        });
        var done = box.querySelector('.nl-done');
        if (!done) {
            done = document.createElement('div');
            done.className = 'nl-done';
            box.appendChild(done);
        }
        done.innerHTML =
            '<div class="nl-mark">SUNOLICIOUS<sup>™</sup></div>' +
            '<div class="nl-tag">Human. Machine. Manifest.</div>' +
            '<h3></h3><p></p><button type="button">Close</button>';
        done.querySelector('h3').textContent = title;
        done.querySelector('p').textContent = message;
        done.querySelector('button').addEventListener('click', function () {
            var x = document.getElementById('closePopup');
            if (x) x.click();
        });
    }

    function fallback() {
        form.removeEventListener('submit', onSubmit);
        form.target = '_blank';
        form.submit();
    }

    function onSubmit(e) {
        e.preventDefault();
        var btn = form.querySelector('.submit-btn');
        var box = form.closest('.popup-content');
        var old = form.parentNode.querySelector('.nl-error');
        if (old) old.remove();
        var label = btn ? btn.textContent : '';
        if (btn) { btn.disabled = true; btn.textContent = 'Subscribing…'; }

        var cb = '__nlCb' + Date.now();
        var script = document.createElement('script');
        var done = false;
        function cleanup() { done = true; delete window[cb]; if (script.parentNode) script.parentNode.removeChild(script); clearTimeout(timer); }
        var timer = setTimeout(function () { if (!done) { cleanup(); fallback(); } }, 10000);

        window[cb] = function (res) {
            cleanup();
            if (btn) { btn.disabled = false; btn.textContent = label; }
            var msg = plain(res && res.msg);
            if (res && res.result === 'success') {
                showDone(box, "You're in", /almost finished|confirm/i.test(msg)
                    ? 'One more step: check your inbox and confirm your email to finish signing up.'
                    : "Thanks for joining. You'll hear from me when there's something new.");
                form.reset();
            } else if (/already subscribed/i.test(msg)) {
                showDone(box, 'Already on the list', "That email is already subscribed. You're all set.");
            } else {
                var p = document.createElement('p');
                p.className = 'nl-error';
                p.textContent = msg ? msg.replace(/^\d+\s*-\s*/, '').replace(/\s*\(.*?\)\s*$/, '') : 'Something went wrong. Please try again.';
                form.appendChild(p);
            }
        };
        script.onerror = function () { if (!done) { cleanup(); fallback(); } };
        script.src = form.action.replace('/post?', '/post-json?') + '&' + serialize(form) + '&c=' + cb;
        document.body.appendChild(script);
    }

    form.addEventListener('submit', onSubmit);
})();
