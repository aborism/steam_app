// Intersection Observer for reveal animations
(function () {
    try {
        // iframeの中から親ウィンドウ（Streamlitアプリ本体）のドキュメントを参照
        var doc;
        try {
            doc = window.parent.document;
        } catch (e) {
            console.warn("Access to parent document failed, falling back to current document.");
            doc = document;
        }

        const observerOptions = { threshold: 0.1 };

        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    setTimeout(function () {
                        entry.target.classList.add('animated');
                    }, 100);
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        function observeReveal() {
            // 親ドキュメント内の要素を検索（以前の仕様に戻す）
            var targets = doc.querySelectorAll('.reveal-legendary:not(.animated), .reveal-nayuta:not(.animated), .reveal-gold:not(.animated), .reveal-sun:not(.animated)');
            targets.forEach(function (target) {
                observer.observe(target);
            });
        }

        // 初回実行
        observeReveal();

        // 定期的にチェック（Streamlitの動的描画対策）
        setInterval(observeReveal, 200);

    } catch (e) {
        console.error("Animation script error:", e);
    }
})();
