// Lightweight replacement for main.js + jQuery plugins (index.html only).
(function () {
	'use strict';

	// full-height panels
	var full = document.querySelectorAll('.js-fullheight');
	function setFullHeight() {
		var h = window.innerHeight + 'px';
		for (var i = 0; i < full.length; i++) full[i].style.height = h;
	}
	setFullHeight();
	var resizeTimer;
	window.addEventListener('resize', function () {
		clearTimeout(resizeTimer);
		resizeTimer = setTimeout(setFullHeight, 100);
	});

	// loader
	var loader = document.getElementById('ftco-loader');
	if (loader) loader.classList.remove('show');

	// fade sections in as they enter the viewport
	var items = document.querySelectorAll('.ftco-animate');
	function reveal(el) { el.classList.add('fadeInUp', 'ftco-animated'); }
	if ('IntersectionObserver' in window) {
		var io = new IntersectionObserver(function (entries) {
			entries.forEach(function (e) {
				if (e.isIntersecting) { reveal(e.target); io.unobserve(e.target); }
			});
		}, { rootMargin: '0px 0px -5% 0px' });
		for (var j = 0; j < items.length; j++) io.observe(items[j]);
	} else {
		for (var k = 0; k < items.length; k++) reveal(items[k]);
	}

	// in-page navigation: make every section visible right away so the jump never lands on hidden content
	function revealAll() { for (var n = 0; n < items.length; n++) reveal(items[n]); }
	if (window.location.hash) revealAll();
	var links = document.querySelectorAll('#colorlib-main-menu a[href^="#"], #mobile-nav a[href^="#"]');
	for (var m = 0; m < links.length; m++) links[m].addEventListener('click', revealAll);

	// highlight the nav entry (sidebar and mobile bar) of the section currently in view
	var spy = [], order = [];
	for (var q = 0; q < links.length; q++) {
		var id = links[q].getAttribute('href').slice(1);
		spy.push({ id: id, node: links[q].closest('li') || links[q] });
		if (order.indexOf(id) < 0) order.push(id);
	}
	var spyTicking = false, pinned = null;
	function updateSpy() {
		spyTicking = false;
		var current = '';
		if (pinned !== null) {
			// the entry the visitor just tapped stays highlighted until they scroll by hand
			current = pinned;
		} else {
			// the trigger line slides from 30% of the viewport down to its bottom edge as the page
			// nears its end, so short sections at the bottom (Honors, Service) each get their turn
			var max = document.documentElement.scrollHeight - window.innerHeight;
			var progress = max > 0 ? Math.min(1, window.pageYOffset / max) : 0;
			var line = window.innerHeight * Math.max(0.3, progress);
			for (var r = 0; r < order.length; r++) {
				var el = order[r] ? document.getElementById(order[r]) : null;
				if (el && el.getBoundingClientRect().top <= line) current = order[r];
			}
		}
		for (var t = 0; t < spy.length; t++) {
			var on = spy[t].id === current;
			spy[t].node.classList.toggle('colorlib-active', on);
			// keep the active chip visible in the horizontally scrolling mobile nav
			if (on && spy[t].node.parentNode.id === 'mobile-nav') {
				var nav = spy[t].node.parentNode, n = spy[t].node;
				if (n.offsetLeft < nav.scrollLeft || n.offsetLeft + n.offsetWidth > nav.scrollLeft + nav.clientWidth) {
					nav.scrollLeft = n.offsetLeft - 10;
				}
			}
		}
	}
	if (spy.length) {
		window.addEventListener('scroll', function () {
			if (!spyTicking) { spyTicking = true; window.requestAnimationFrame(updateSpy); }
		}, { passive: true });
		window.addEventListener('resize', updateSpy);
		for (var u = 0; u < links.length; u++) {
			(function (n) { links[n].addEventListener('click', function () { pinned = spy[n].id; updateSpy(); }); })(u);
		}
		var unpin = function () { if (pinned !== null) { pinned = null; updateSpy(); } };
		['wheel', 'touchmove', 'keydown', 'mousedown'].forEach(function (ev) {
			window.addEventListener(ev, function (e) {
				if (ev === 'mousedown' && e.target.closest && e.target.closest('#colorlib-main-menu, #mobile-bar')) return;
				unpin();
			}, { passive: true });
		});
		updateSpy();
	}

	// mobile top bar: slide away while scrolling down the page, come back when scrolling up
	var bar = document.getElementById('mobile-bar');
	if (bar) {
		var lastY = window.pageYOffset;
		var updateBar = function () {
			var y = window.pageYOffset, d = y - lastY;
			if (y < 60 || pinned !== null) {
				// near the top, or right after tapping a nav chip: always visible
				bar.classList.remove('bar-hidden');
			} else if (d > 6) {
				bar.classList.add('bar-hidden');
			} else if (d < -6) {
				bar.classList.remove('bar-hidden');
			}
			if (Math.abs(d) > 6) lastY = y;
		};
		// scroll events are already delivered at most once per frame, and this handler only toggles a class
		window.addEventListener('scroll', updateBar, { passive: true });
		bar.addEventListener('click', function () { bar.classList.remove('bar-hidden'); });
	}

	// hero background parallax: move a composited layer instead of repainting the background
	var bg = document.getElementById('parallax-bg-layer');
	if (bg && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
		var speed = 0.15, ticking = false;
		function update() {
			bg.style.transform = 'translate3d(0,' + (-window.pageYOffset * speed) + 'px,0)';
			ticking = false;
		}
		window.addEventListener('scroll', function () {
			if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
		}, { passive: true });
		update();
	}
})();
