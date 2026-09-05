/* The bridge between the game and the dynamic-avatar-drawer library.
 *
 * Ours, not the library's. The library is vendored unmodified next door;
 * everything we need it to do differently happens here, which is what keeps
 * it replaceable under the LGPL.
 *
 * The game is Python running on a canvas, so this deliberately exposes the
 * smallest possible surface: mount once, then hand over a flat object of
 * numbers whenever the character changes. Building a da.Player from Python
 * across the browser bridge would mean a call per property.
 */
(function () {
    "use strict";

    var CONTAINER_ID = "lechery-avatar";
    var GROUP_ID = "lechery-avatar-group";

    var state = {
        ready: false,     // da.load() has resolved
        group: null,      // the canvas group the library draws into
        player: null,
        pending: null,    // last update received before we were ready
        drawing: false,   // a draw is in flight; da.draw is async
        again: false,     // ...and another was asked for while it ran
        box: null,        // last requested placement, in CSS pixels
        status: "starting"
    };

    function container() {
        var element = document.getElementById(CONTAINER_ID);
        if (element === null) {
            element = document.createElement("div");
            element.id = CONTAINER_ID;
            element.style.position = "fixed";
            element.style.overflow = "hidden";
            element.style.pointerEvents = "none";  // taps belong to the game
            element.style.zIndex = "20";           // over the canvas, under inputs
            element.style.display = "none";
            document.body.appendChild(element);
        }
        return element;
    }

    var VIEW = {
        transparentBackground: true,
        printAdditionalInfo: false,   // the game draws its own name and stats
        printHeight: false,
        printVitals: false,
        renderShoeSideView: false,
        offsetX: 0,
        offsetY: 0
    };

    /* The group holds canvases at the library's own fixed size, so it is
     * scaled to whatever box the game gives it. Applied separately from
     * placement because the group does not exist until da.load() resolves,
     * and the first placement almost always arrives before that. */
    function fit() {
        if (state.group === null || state.box === null) {
            return;
        }
        state.group.style.transformOrigin = "top left";
        state.group.style.transform = "scale(" +
            Math.min(state.box.width / 700, state.box.height / 1200) + ")";
    }

    function build(traits) {
        return new da.Player({
            name: traits.name || "",
            fem: traits.fem,
            basedim: traits.basedim
        });
    }

    function redraw() {
        if (!state.ready || state.player === null || state.group === null) {
            return;
        }
        if (state.drawing) {
            // Coalesce: a slider being dragged asks far faster than the
            // library can draw, and queueing every request would run the
            // whole backlog after the player stopped moving.
            state.again = true;
            return;
        }
        state.drawing = true;
        da.draw(state.group, state.player, VIEW).then(function () {
            state.drawing = false;
            if (state.again) {
                state.again = false;
                redraw();
            }
        }).catch(function (error) {
            state.drawing = false;
            state.status = "draw failed: " + (error && error.message ? error.message : error);
            console.error("avatar draw failed", error);
        });
    }

    var api = {
        /* Whether the library loaded. The game keeps its own placeholder
         * figure for when it did not. */
        ready: function () {
            return state.ready;
        },

        /* Position the avatar over a rect, in CSS pixels. */
        place: function (left, top, width, height) {
            var element = container();
            element.style.left = left + "px";
            element.style.top = top + "px";
            element.style.width = width + "px";
            element.style.height = height + "px";
            element.style.display = "block";
            state.box = {width: width, height: height};
            fit();
        },

        /* What the library is doing, in one word the game can draw. There
         * is no console on a phone, so this is the only way a failure here
         * can be seen at all. */
        status: function () {
            return state.status;
        },

        hide: function () {
            container().style.display = "none";
        },

        /* Replace the character. `traits` is {name, fem, basedim:{...}}. */
        update: function (traits) {
            if (!state.ready) {
                state.pending = traits;
                return;
            }
            state.player = build(traits);
            redraw();
        },

        init: function () {
            if (state.ready) {
                return;
            }
            if (typeof da === "undefined") {
                state.status = "no library";
                return;
            }
            state.status = "loading";
            da.load().then(function () {
                // getCanvasGroup looks the holder up by id and reads its
                // style without checking -- its docstring claims it creates
                // one, but it only creates the canvases inside. Passing an
                // id that does not exist throws on null.
                var holder = document.getElementById(GROUP_ID);
                if (holder === null) {
                    holder = document.createElement("div");
                    holder.id = GROUP_ID;
                    container().appendChild(holder);
                }
                state.group = da.getCanvasGroup(GROUP_ID, {
                    width: 700,
                    height: 1200
                });
                state.ready = true;
                state.status = "ready";
                // The group only exists now, so any placement that arrived
                // while loading has to be applied again.
                fit();
                if (state.pending !== null) {
                    api.update(state.pending);
                    state.pending = null;
                }
            }).catch(function (error) {
                state.status = "load failed: " + (error && error.message ? error.message : error);
                console.error("avatar library failed to load", error);
            });
        }
    };

    window.LecheryAvatar = api;
    api.init();
})();
