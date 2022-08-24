define("pages/index/index.js", (function (e, n, t, o, r, a, u, i, l, c, s, d, f, m, v, b, p, h, g, y, x, T, A, k, H, w, S, M, _, E, I, P, j) {
    (global.webpackJsonp = global.webpackJsonp || []).push([["pages/index/index"], {
        8069: function (e, n, t) {
            "use strict";
            t.r(n);
            var o = t("da67"), r = t.n(o);
            for (var a in o) ["default"].indexOf(a) < 0 && function (e) {
                t.d(n, e, (function () {
                    return o[e]
                }))
            }(a);
            n.default = r.a
        }, d537: function (e, n, t) {
            "use strict";
            (function (e) {
                function n(e) {
                    return e && e.__esModule ? e : {default: e}
                }

                t("6cdc"), n(t("dc04")), e(n(t("f75a")).default)
            }).call(this, t("d1fe").createPage)
        }, da67: function (e, n, t) {
            "use strict";
            Object.defineProperty(n, "__esModule", {value: !0}), n.default = void 0;
            var o = d(t("be60")), a = t("dc04"), u = t("267e"), i = t("7b8a"), l = d(t("dbcb")), c = t("4360"),
                s = t("4260");

            function d(e) {
                return e && e.__esModule ? e : {default: e}
            }

            function f(e, n) {
                return function (e) {
                    if (Array.isArray(e)) return e
                }(e) || function (e, n) {
                    var t = null == e ? null : "undefined" != typeof Symbol && e[Symbol.iterator] || e["@@iterator"];
                    if (null != t) {
                        var o, r, a = [], u = !0, i = !1;
                        try {
                            for (t = t.call(e); !(u = (o = t.next()).done) && (a.push(o.value), !n || a.length !== n); u = !0) ;
                        } catch (e) {
                            i = !0, r = e
                        } finally {
                            try {
                                u || null == t.return || t.return()
                            } finally {
                                if (i) throw r
                            }
                        }
                        return a
                    }
                }(e, n) || function (e, n) {
                    if (e) {
                        if ("string" == typeof e) return m(e, n);
                        var t = Object.prototype.toString.call(e).slice(8, -1);
                        return "Object" === t && e.constructor && (t = e.constructor.name), "Map" === t || "Set" === t ? Array.from(e) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? m(e, n) : void 0
                    }
                }(e, n) || function () {
                    throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")
                }()
            }

            function m(e, n) {
                (null == n || n > e.length) && (n = e.length);
                for (var t = 0, o = new Array(n); t < n; t++) o[t] = e[t];
                return o
            }

            var v = {
                components: {
                    Tab: function () {
                        t.e("pages/index/components/Tab").then(function () {
                            return resolve(t("eb39"))
                        }.bind(null, t)).catch(t.oe)
                    }, Home: function () {
                        r.all([t.e("common/vendor"), t.e("pages/index/components/home/index")]).then(function () {
                            return resolve(t("b5c1"))
                        }.bind(null, t)).catch(t.oe)
                    }, Task: function () {
                        r.all([t.e("common/vendor"), t.e("pages/index/components/Task/index")]).then(function () {
                            return resolve(t("6ad1"))
                        }.bind(null, t)).catch(t.oe)
                    }, MineCenter: function () {
                        t.e("pages/index/components/mine/index").then(function () {
                            return resolve(t("3779"))
                        }.bind(null, t)).catch(t.oe)
                    }, TalentNewTask: function () {
                        r.all([t.e("common/vendor"), t.e("components/RedEnvelope/index")]).then(function () {
                            return resolve(t("178c"))
                        }.bind(null, t)).catch(t.oe)
                    }, NewTaskEntry: function () {
                        r.all([t.e("common/vendor"), t.e("components/NewTaskEntry")]).then(function () {
                            return resolve(t("285d"))
                        }.bind(null, t)).catch(t.oe)
                    }, Academy: function () {
                        r.all([t.e("common/vendor"), t.e("pages/index/components/academy/index")]).then(function () {
                            return resolve(t("73bf"))
                        }.bind(null, t)).catch(t.oe)
                    }, Announcement: function () {
                        r.all([t.e("common/vendor"), t.e("components/Announcement/index")]).then(function () {
                            return resolve(t("d95b"))
                        }.bind(null, t)).catch(t.oe)
                    }
                }, onPageScroll: function (e) {
                    i.homeEvent.publish(e), i.mineEvent.publish(e)
                }, setup: function () {
                    var e = (0, a.ref)(!1);
                    f((0, c.useHomeInfo)(), 2)[1].load();
                    var n = f((0, c.useMessage)(), 2), t = n[0].msgInited, r = n[1];
                    r.load();
                    var i = f((0, c.useGlobal)(), 2), d = i[0].toHome, m = i[1].unSignToHome,
                        v = f((0, c.useHomeTab)(), 2), b = v[0], p = b.isHome, h = b.isTask, g = b.isMine,
                        y = b.isAcademy, x = v[1], T = x.setHome, A = x.setTask;
                    f((0, c.useServerTime)(), 2)[1].load();
                    var k = f((0, c.useHomeTasks)(), 2), H = k[0].talentPageId;
                    return (0, k[1].setTalentPageId)(), f((0, c.usePunishment)(), 2)[1].load(), f((0, c.useCollectMessage)(), 2)[1].load(), (0, l.default)("onShow", (function () {
                        e.value || (H.value ? A() : T()), e.value = !0, t.value && r.load(), d.value && (A(), m(), o.default.pageScrollTo({
                            scrollTop: 0,
                            duration: 500
                        }))
                    })), (0, s.reportAppPerf)(), {isHome: p, isTask: h, isMine: g, isAcademy: y, tabH: u.tabH}
                }
            };
            n.default = v
        }, da6e: function (e, n, t) {
            "use strict";
            t.d(n, "b", (function () {
                return o
            })), t.d(n, "c", (function () {
                return r
            })), t.d(n, "a", (function () {
            }));
            var o = function () {
                this.$createElement;
                this._self._c
            }, r = []
        }, f75a: function (e, n, t) {
            "use strict";
            t.r(n);
            var o = t("da6e"), r = t("8069");
            for (var a in r) ["default"].indexOf(a) < 0 && function (e) {
                t.d(n, e, (function () {
                    return r[e]
                }))
            }(a);
            var u = t("f0c5"), i = Object(u.a)(r.default, o.b, o.c, !1, null, null, null, !1, o.a, undefined);
            n.default = i.exports
        }
    }, [["d537", "common/runtime", "common/vendor"]]])
}));
//# sourceMappingURL=index.js.map