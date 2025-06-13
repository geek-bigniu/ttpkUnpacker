define("pages/index/index.js", (function (t, e, a, r, n, s, i, c, o, l, u, g, p, f, b, h, m, d, w, v, C, y, x, k, D, L, S, T, R, N, B, P, I, j, F, X, Y, A, E, M) {
    "use strict";

    function O(t) {
        return O = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (t) {
            return typeof t
        } : function (t) {
            return t && "function" == typeof Symbol && t.constructor === Symbol && t !== Symbol.prototype ? "symbol" : typeof t
        }, O(t)
    }

    function U(t, e, a, r, s, i, c) {
        try {
            var o = t[i](c), l = o.value
        } catch (t) {
            return void a(t)
        }
        o.done ? e(l) : n.resolve(l).then(r, s)
    }

    function q(t) {
        return function () {
            var e = this, a = arguments;
            return new n((function (r, n) {
                var s = t.apply(e, a);

                function i(t) {
                    U(s, r, n, i, c, "next", t)
                }

                function c(t) {
                    U(s, r, n, i, c, "throw", t)
                }

                i(void 0)
            }))
        }
    }

    function z(t, e, a) {
        return (e = function (t) {
            var e = function (t, e) {
                if ("object" != O(t) || !t) return t;
                var a = t[Symbol.toPrimitive];
                if (void 0 !== a) {
                    var r = a.call(t, e || "default");
                    if ("object" != O(r)) return r;
                    throw new TypeError("@@toPrimitive must return a primitive value.")
                }
                return ("string" === e ? String : Number)(t)
            }(t, "string");
            return "symbol" == O(e) ? e : e + ""
        }(e)) in t ? Object.defineProperty(t, e, {
            value: a,
            enumerable: !0,
            configurable: !0,
            writable: !0
        }) : t[e] = a, t
    }

    var G = "full-screen", H = "default-screen", J = getApp();
    Page({
        data: {
            imageUrl: J.globalData.imageUrl,
            data: J.globalData.data,
            swiperList: [{swpClass: "small-left", screenClass: ""}, {
                swpClass: "small-center",
                screenClass: ""
            }, {swpClass: "small-right", screenClass: ""}],
            current: 1,
            prevCurrent: 1,
            tabs: [{
                icon: "/image/tab-icon/extend-icon.png",
                select: "/image/tab-icon/select-extend-icon.png",
                text: "扩展能力"
            }, {
                icon: "/image/tab-icon/api-icon.png",
                select: "/image/tab-icon/select-api-icon.png",
                text: "组件"
            }, {
                icon: "/image/tab-icon/interface-icon.png",
                select: "/image/tab-icon/select-interface-icon.png",
                text: "接口"
            }],
            screen: "small",
            isIos: !1,
            switchBig: !1,
            scrollTop: 0,
            system: ""
        }, onLoad: function (t) {
            t.view && this.setData(z({
                current: 2,
                screen: "big",
                view: t.view
            }, "data[2].list[10].open", !0)), t.native && this.switchCard(0);
            var e = tt.getSystemInfoSync();
            this.setData({isIos: e.system.toLowerCase().includes("ios"), system: e})
        }, touchstart: function (t) {
            var e = t.changedTouches[0], a = e.pageX, r = e.pageY;
            this.pageX = a, this.pageY = r
        }, touchmove: function (t) {
        }, touchend: function (t) {
            var e = t.changedTouches[0], a = e.pageX, r = e.pageY, n = a - this.pageX, s = r - this.pageY;
            Math.abs(n) >= 60 && "small" === this.data.screen && this.moveCard(n), (s >= 60 || s < 30) && Math.abs(n) < 60 && this.scaleCard(s)
        }, moveCard: function (t) {
            var e = this.data.swiperList, a = this.data.current, r = e.length;
            if (t > 60) {
                if (0 === a) return;
                a--
            }
            if (t < -60) {
                if (a === r - 1) return;
                a++
            }
            this.switchCard(a)
        }, scrollFlag: !0, bindscroll: function (t) {
            var e = !0;
            t.detail.scrollTop > 5 && (e = !1), this.scrollFlag = e
        }, scaleCard: function (t) {
            var e = this;
            return q(regeneratorRuntime.mark((function a() {
                var r, n, s, i, c, o;
                return regeneratorRuntime.wrap((function (a) {
                    for (; ;) switch (a.prev = a.next) {
                        case 0:
                            if (r = e.data.current, n = e.data.swiperList, s = e.data.swiperList[r].screenClass, !(t > 60 && e.scrollFlag)) {
                                a.next = 9;
                                break
                            }
                            if ("small" !== e.data.screen) {
                                a.next = 6;
                                break
                            }
                            return a.abrupt("return");
                        case 6:
                            i = new RegExp(G), "iOS 12.1.2" !== e.data.system.system && (s = s.replace(i, H)), e.setData({scrollTop: 0}, (function () {
                                e.initScall(n, r, s)
                            }));
                        case 9:
                            if (!(t < -60)) {
                                a.next = 16;
                                break
                            }
                            if ("big" !== e.data.screen) {
                                a.next = 12;
                                break
                            }
                            return a.abrupt("return");
                        case 12:
                            "big" === e.data.screen ? (c = new RegExp(H), s = s.replace(c, G)) : s = "".concat(s, " ").concat(G), o = (o = e.backClassName(r)).map((function (t, e) {
                                return r === e && (t.screenClass = s), t
                            })), e.setData({swiperList: o, screen: "big"});
                        case 16:
                        case"end":
                            return a.stop()
                    }
                }), a)
            })))()
        }, initScall: function (t, e, a) {
            var r = this;
            this.setData(z(z(z({}, "swiperList[".concat(e, "].screenClass"), a), "screen", "small"), "switchBig", !1), (function () {
                s((function () {
                    r.setData({
                        swiperList: t.map((function (t, e) {
                            return t.screenClass = "", t
                        }))
                    })
                }), 300)
            }))
        }, switchTab: function (t) {
            var e = t.currentTarget.dataset.index;
            this.switchCard(e)
        }, switchCard: function (t) {
            var e = this.data.current, a = this.backClassName(t), r = !1;
            "big" === this.data.screen && (r = !0), this.setData({
                swiperList: a.map((function (t) {
                    return t.screenClass = "", t
                })), current: t, prevCurrent: e, switchBig: r
            }), this.scrollFlag = !0
        }, backClassName: function (t) {
            var e = this.data.swiperList, a = e.length, r = e[t - 1], n = e[t + 1], s = e[t];
            if (r) {
                n && (n.swpClass = "small-right", n.bigClass = "big-right"), r.swpClass = "small-left", r.bigClass = "big-left", s.swpClass = "small-center", s.bigClass = this.backBigCenter(t, this.data.current);
                for (var i = 0; i < t; i++) e[i].swpClass = "small-leftNo", e[i].bigClass = "big-leftNo"
            }
            if (n) {
                r && (r.swpClass = "small-left", r.bigClass = "big-left"), s.swpClass = "small-center", s.bigClass = this.backBigCenter(t, this.data.current), n.swpClass = "small-right", n.bigClass = "big-right";
                for (var c = t + 2; c < a; c++) e[c].swpClass = "small-rightNo", e[c].bigClass = "big-rightNo"
            } else r.swpClass = "small-left", s.swpClass = "small-center", r.bigClass = "big-left", s.bigClass = this.backBigCenter(t, this.data.current);
            return e
        }, backBigCenter: function (t, e) {
            return 1 === t && 0 === e ? "big-center" : t > e ? "big-center-left" : t < e ? "big-center-right" : void 0
        }, toRouter: function (t) {
            var e = this.data, a = e.current, r = (e.system, t.currentTarget.dataset), n = r.path, s = r.view;
            if (s && 2 === a) return J.globalData.view = s, void tt.switchTab({url: "/pages/API/index"});
            n && (a < 2 && (n = "/pages/component/".concat(n)), 2 === a && (n = "/pages/API/".concat(n)), tt.navigateTo({url: n}))
        }, showChildren: function (t) {
            var e = this;
            return q(regeneratorRuntime.mark((function a() {
                var r, s, i, c, o;
                return regeneratorRuntime.wrap((function (a) {
                    for (; ;) switch (a.prev = a.next) {
                        case 0:
                            if (r = t.currentTarget.dataset, s = r.index, i = r.num, c = r.open, o = e.data.data, !c) {
                                a.next = 5;
                                break
                            }
                            return e.setData(z({}, "data[".concat(s, "].list[").concat(i, "].open"), !1)), a.abrupt("return");
                        case 5:
                            if (c) {
                                a.next = 9;
                                break
                            }
                            return a.next = 8, n.all(o.map(function () {
                                var t = q(regeneratorRuntime.mark((function t(e) {
                                    return regeneratorRuntime.wrap((function (t) {
                                        for (; ;) switch (t.prev = t.next) {
                                            case 0:
                                                return t.abrupt("return", e);
                                            case 1:
                                            case"end":
                                                return t.stop()
                                        }
                                    }), t)
                                })));
                                return function (e) {
                                    return t.apply(this, arguments)
                                }
                            }()));
                        case 8:
                            o = a.sent;
                        case 9:
                            o[s].list[i].open = !c, e.setData({data: o}), "big" !== e.data.screen && e.scaleCard(-300);
                        case 12:
                        case"end":
                            return a.stop()
                    }
                }), a)
            })))()
        }, initList: function (t) {
            return new n((function (e, a) {
                e(t.map((function (e) {
                    return e.open = !1, t
                }))[0])
            }))
        }
    })
}));
//# sourceMappingURL=index.js.map