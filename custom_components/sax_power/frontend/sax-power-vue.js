//#region node_modules/@vue/shared/dist/shared.esm-bundler.js
// @__NO_SIDE_EFFECTS__
function e(e) {
	let t = /* @__PURE__ */ Object.create(null);
	for (let n of e.split(",")) t[n] = 1;
	return (e) => e in t;
}
var t = {}, n = [], r = () => {}, i = () => !1, a = (e) => e.charCodeAt(0) === 111 && e.charCodeAt(1) === 110 && (e.charCodeAt(2) > 122 || e.charCodeAt(2) < 97), o = (e) => e.startsWith("onUpdate:"), s = Object.assign, c = (e, t) => {
	let n = e.indexOf(t);
	n > -1 && e.splice(n, 1);
}, l = Object.prototype.hasOwnProperty, u = (e, t) => l.call(e, t), d = Array.isArray, f = (e) => S(e) === "[object Map]", p = (e) => S(e) === "[object Set]", m = (e) => S(e) === "[object Date]", h = (e) => S(e) === "[object RegExp]", g = (e) => typeof e == "function", _ = (e) => typeof e == "string", v = (e) => typeof e == "symbol", y = (e) => typeof e == "object" && !!e, b = (e) => (y(e) || g(e)) && g(e.then) && g(e.catch), x = Object.prototype.toString, S = (e) => x.call(e), C = (e) => S(e).slice(8, -1), w = (e) => S(e) === "[object Object]", T = (e) => _(e) && e !== "NaN" && e[0] !== "-" && "" + parseInt(e, 10) === e, E = /* @__PURE__ */ e(",key,ref,ref_for,ref_key,onVnodeBeforeMount,onVnodeMounted,onVnodeBeforeUpdate,onVnodeUpdated,onVnodeBeforeUnmount,onVnodeUnmounted"), D = (e) => {
	let t = /* @__PURE__ */ Object.create(null);
	return ((n) => t[n] || (t[n] = e(n)));
}, O = /-\w/g, k = D((e) => e.replace(O, (e) => e.slice(1).toUpperCase())), ee = /\B([A-Z])/g, A = D((e) => e.replace(ee, "-$1").toLowerCase()), te = D((e) => e.charAt(0).toUpperCase() + e.slice(1)), ne = D((e) => e ? `on${te(e)}` : ""), j = (e, t) => !Object.is(e, t), re = (e, ...t) => {
	for (let n = 0; n < e.length; n++) e[n](...t);
}, M = (e, t, n, r = !1) => {
	Object.defineProperty(e, t, {
		configurable: !0,
		enumerable: !1,
		writable: r,
		value: n
	});
}, N = (e) => {
	let t = parseFloat(e);
	return isNaN(t) ? e : t;
}, ie = (e) => {
	let t = _(e) ? Number(e) : NaN;
	return isNaN(t) ? e : t;
}, ae, oe = () => ae ||= typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : typeof global < "u" ? global : {};
function se(e) {
	if (d(e)) {
		let t = {};
		for (let n = 0; n < e.length; n++) {
			let r = e[n], i = _(r) ? de(r) : se(r);
			if (i) for (let e in i) t[e] = i[e];
		}
		return t;
	}
	if (_(e) || y(e)) return e;
}
var ce = /;(?![^(]*\))/g, le = /:([^]+)/, ue = /\/\*[^]*?\*\//g;
function de(e) {
	let t = {};
	return e.replace(ue, "").split(ce).forEach((e) => {
		if (e) {
			let n = e.split(le);
			n.length > 1 && (t[n[0].trim()] = n[1].trim());
		}
	}), t;
}
function P(e) {
	let t = "";
	if (_(e)) t = e;
	else if (d(e)) for (let n = 0; n < e.length; n++) {
		let r = P(e[n]);
		r && (t += r + " ");
	}
	else if (y(e)) for (let n in e) e[n] && (t += n + " ");
	return t.trim();
}
var fe = "itemscope,allowfullscreen,formnovalidate,ismap,nomodule,novalidate,readonly", pe = /* @__PURE__ */ e(fe);
fe + "";
function me(e) {
	return !!e || e === "";
}
function he(e, t) {
	if (e.length !== t.length) return !1;
	let n = !0;
	for (let r = 0; n && r < e.length; r++) n = _e(e[r], t[r]);
	return n;
}
function ge(e, t) {
	if (e.size !== t.size) return !1;
	let n = Array.from(t), r = new Uint8Array(n.length);
	for (let t of e) {
		let e = -1;
		for (let i = 0; i < n.length; i++) if (!r[i] && _e(t, n[i])) {
			e = i;
			break;
		}
		if (e < 0) return !1;
		r[e] = 1;
	}
	return !0;
}
function _e(e, t) {
	if (e === t) return !0;
	let n = m(e), r = m(t);
	if (n || r) return n && r ? e.getTime() === t.getTime() : !1;
	if (n = v(e), r = v(t), n || r) return e === t;
	if (n = d(e), r = d(t), n || r) return n && r ? he(e, t) : !1;
	if (n = y(e), r = y(t), n || r) {
		if (!n || !r) return !1;
		if (n = f(e), r = f(t), n || r || (n = p(e), r = p(t), n || r)) return n && r ? ge(e, t) : !1;
		if (Object.keys(e).length !== Object.keys(t).length) return !1;
		for (let n in e) {
			let r = e.hasOwnProperty(n), i = t.hasOwnProperty(n);
			if (r && !i || !r && i || !_e(e[n], t[n])) return !1;
		}
	}
	return String(e) === String(t);
}
function ve(e, t) {
	return e.findIndex((e) => _e(e, t));
}
var ye = (e) => !!(e && e.__v_isRef === !0), F = (e) => _(e) ? e : e == null ? "" : d(e) || y(e) && (e.toString === x || !g(e.toString)) ? ye(e) ? F(e.value) : JSON.stringify(e, be, 2) : String(e), be = (e, t) => ye(t) ? be(e, t.value) : f(t) ? { [`Map(${t.size})`]: [...t.entries()].reduce((e, [t, n], r) => (e[xe(t, r) + " =>"] = n, e), {}) } : p(t) ? { [`Set(${t.size})`]: [...t.values()].map((e) => xe(e)) } : v(t) ? xe(t) : y(t) && !d(t) && !w(t) ? String(t) : t, xe = (e, t = "") => v(e) ? `Symbol(${e.description ?? t})` : e, I, Se = class {
	constructor(e = !1) {
		this.detached = e, this._active = !0, this._on = 0, this.effects = [], this.cleanups = [], this._isPaused = !1, this._warnOnRun = !0, this.__v_skip = !0, !e && I && (I.active ? (this.parent = I, this.index = (I.scopes || (I.scopes = [])).push(this) - 1) : (this._active = !1, this._warnOnRun = !1));
	}
	get active() {
		return this._active;
	}
	pause() {
		if (this._active) {
			this._isPaused = !0;
			let e, t;
			if (this.scopes) {
				let n = this.scopes.slice();
				for (e = 0, t = n.length; e < t; e++) n[e].pause();
			}
			for (e = 0, t = this.effects.length; e < t; e++) this.effects[e].pause();
		}
	}
	resume() {
		if (this._active && this._isPaused) {
			this._isPaused = !1;
			let e, t;
			if (this.scopes) {
				let n = this.scopes.slice();
				for (e = 0, t = n.length; e < t; e++) n[e].resume();
			}
			let n = this.effects.slice();
			for (e = 0, t = n.length; e < t; e++) n[e].resume();
		}
	}
	run(e) {
		if (this._active) {
			let t = I;
			try {
				return I = this, e();
			} finally {
				I = t;
			}
		}
	}
	on() {
		++this._on === 1 && (this.prevScope = I, I = this);
	}
	off() {
		if (this._on > 0 && --this._on === 0) {
			if (I === this) I = this.prevScope;
			else {
				let e = I;
				for (; e;) {
					if (e.prevScope === this) {
						e.prevScope = this.prevScope;
						break;
					}
					e = e.prevScope;
				}
			}
			this.prevScope = void 0;
		}
	}
	stop(e) {
		if (this._active) {
			this._active = !1;
			let t, n;
			for (t = 0, n = this.effects.length; t < n; t++) this.effects[t].stop();
			for (this.effects.length = 0, t = 0, n = this.cleanups.length; t < n; t++) this.cleanups[t]();
			if (this.cleanups.length = 0, this.scopes) {
				let e = this.scopes.slice();
				for (t = 0, n = e.length; t < n; t++) e[t].stop(!0);
				this.scopes.length = 0;
			}
			if (!this.detached && this.parent && !e) {
				let e = this.parent.scopes.pop();
				e && e !== this && (this.parent.scopes[this.index] = e, e.index = this.index);
			}
			this.parent = void 0;
		}
	}
};
function Ce() {
	return I;
}
function we(e, t = !1) {
	I && I.cleanups.push(e);
}
var L, Te = /* @__PURE__ */ new WeakSet(), Ee = class {
	constructor(e) {
		this.fn = e, this.deps = void 0, this.depsTail = void 0, this.flags = 5, this.next = void 0, this.cleanup = void 0, this.scheduler = void 0, I && (I.active ? I.effects.push(this) : this.flags &= -2);
	}
	pause() {
		this.flags |= 64;
	}
	resume() {
		this.flags & 64 && (this.flags &= -65, Te.has(this) && (Te.delete(this), this.trigger()));
	}
	notify() {
		this.flags & 2 && !(this.flags & 32) || this.flags & 8 || Ae(this);
	}
	run() {
		if (!(this.flags & 1)) return this.fn();
		this.flags |= 2, Ue(this), Ne(this);
		let e = L, t = ze;
		L = this, ze = !0;
		try {
			return this.fn();
		} finally {
			Pe(this), L = e, ze = t, this.flags &= -3;
		}
	}
	stop() {
		if (this.flags & 1) {
			for (let e = this.deps; e; e = e.nextDep) Le(e);
			this.deps = this.depsTail = void 0, Ue(this), this.onStop && this.onStop(), this.flags &= -2;
		}
	}
	trigger() {
		this.flags & 64 ? Te.add(this) : this.scheduler ? this.scheduler() : this.runIfDirty();
	}
	runIfDirty() {
		Fe(this) && this.run();
	}
	get dirty() {
		return Fe(this);
	}
}, De = 0, Oe, ke;
function Ae(e, t = !1) {
	if (e.flags |= 8, t) {
		e.next = ke, ke = e;
		return;
	}
	e.next = Oe, Oe = e;
}
function je() {
	De++;
}
function Me() {
	if (--De > 0) return;
	if (ke) {
		let e = ke;
		for (ke = void 0; e;) {
			let t = e.next;
			e.next = void 0, e.flags &= -9, e = t;
		}
	}
	let e;
	for (; Oe;) {
		let t = Oe;
		for (Oe = void 0; t;) {
			let n = t.next;
			if (t.next = void 0, t.flags &= -9, t.flags & 1) try {
				t.trigger();
			} catch (t) {
				e ||= t;
			}
			t = n;
		}
	}
	if (e) throw e;
}
function Ne(e) {
	for (let t = e.deps; t; t = t.nextDep) t.version = -1, t.prevActiveLink = t.dep.activeLink, t.dep.activeLink = t;
}
function Pe(e) {
	let t, n = e.depsTail, r = n;
	for (; r;) {
		let e = r.prevDep;
		r.version === -1 ? (r === n && (n = e), Le(r), Re(r)) : t = r, r.dep.activeLink = r.prevActiveLink, r.prevActiveLink = void 0, r = e;
	}
	e.deps = t, e.depsTail = n;
}
function Fe(e) {
	for (let t = e.deps; t; t = t.nextDep) if (t.dep.version !== t.version || t.dep.computed && (Ie(t.dep.computed) || t.dep.version !== t.version)) return !0;
	return !!e._dirty;
}
function Ie(e) {
	if (e.flags & 4 && !(e.flags & 16) || (e.flags &= -17, e.globalVersion === We) || (e.globalVersion = We, !e.isSSR && e.flags & 128 && (!e.deps && !e._dirty || !Fe(e)))) return;
	e.flags |= 2;
	let t = e.dep, n = L, r = ze;
	L = e, ze = !0;
	try {
		Ne(e);
		let n = e.fn(e._value);
		(t.version === 0 || j(n, e._value)) && (e.flags |= 128, e._value = n, t.version++);
	} catch (e) {
		throw t.version++, e;
	} finally {
		L = n, ze = r, Pe(e), e.flags &= -3;
	}
}
function Le(e, t = !1) {
	let { dep: n, prevSub: r, nextSub: i } = e;
	if (r && (r.nextSub = i, e.prevSub = void 0), i && (i.prevSub = r, e.nextSub = void 0), n.subs === e && (n.subs = r, !r && n.computed)) {
		n.computed.flags &= -5;
		for (let e = n.computed.deps; e; e = e.nextDep) Le(e, !0);
	}
	!t && !--n.sc && n.map && n.map.delete(n.key);
}
function Re(e) {
	let { prevDep: t, nextDep: n } = e;
	t && (t.nextDep = n, e.prevDep = void 0), n && (n.prevDep = t, e.nextDep = void 0);
}
var ze = !0, Be = [];
function Ve() {
	Be.push(ze), ze = !1;
}
function He() {
	let e = Be.pop();
	ze = e === void 0 || e;
}
function Ue(e) {
	let { cleanup: t } = e;
	if (e.cleanup = void 0, t) {
		let e = L;
		L = void 0;
		try {
			t();
		} finally {
			L = e;
		}
	}
}
var We = 0, Ge = class {
	constructor(e, t) {
		this.sub = e, this.dep = t, this.version = t.version, this.nextDep = this.prevDep = this.nextSub = this.prevSub = this.prevActiveLink = void 0;
	}
}, Ke = class {
	constructor(e) {
		this.computed = e, this.version = 0, this.activeLink = void 0, this.subs = void 0, this.map = void 0, this.key = void 0, this.sc = 0, this.__v_skip = !0;
	}
	track(e) {
		if (!L || !ze || L === this.computed) return;
		let t = this.activeLink;
		if (t === void 0 || t.sub !== L) t = this.activeLink = new Ge(L, this), L.deps ? (t.prevDep = L.depsTail, L.depsTail.nextDep = t, L.depsTail = t) : L.deps = L.depsTail = t, qe(t);
		else if (t.version === -1 && (t.version = this.version, t.nextDep)) {
			let e = t.nextDep;
			e.prevDep = t.prevDep, t.prevDep && (t.prevDep.nextDep = e), t.prevDep = L.depsTail, t.nextDep = void 0, L.depsTail.nextDep = t, L.depsTail = t, L.deps === t && (L.deps = e);
		}
		return t;
	}
	trigger(e) {
		this.version++, We++, this.notify(e);
	}
	notify(e) {
		je();
		try {
			for (let e = this.subs; e; e = e.prevSub) e.sub.notify() && e.sub.dep.notify();
		} finally {
			Me();
		}
	}
};
function qe(e) {
	if (e.dep.sc++, e.sub.flags & 4) {
		let t = e.dep.computed;
		if (t && !e.dep.subs) {
			t.flags |= 20;
			for (let e = t.deps; e; e = e.nextDep) qe(e);
		}
		let n = e.dep.subs;
		n !== e && (e.prevSub = n, n && (n.nextSub = e)), e.dep.subs = e;
	}
}
var Je = /* @__PURE__ */ new WeakMap(), Ye = /* @__PURE__ */ Symbol(""), Xe = /* @__PURE__ */ Symbol(""), Ze = /* @__PURE__ */ Symbol("");
function Qe(e, t, n) {
	if (ze && L) {
		let t = Je.get(e);
		t || Je.set(e, t = /* @__PURE__ */ new Map());
		let r = t.get(n);
		r || (t.set(n, r = new Ke()), r.map = t, r.key = n), r.track();
	}
}
function $e(e, t, n, r, i, a) {
	let o = Je.get(e);
	if (!o) {
		We++;
		return;
	}
	let s = (e) => {
		e && e.trigger();
	};
	if (je(), t === "clear") o.forEach(s);
	else {
		let i = d(e), a = i && T(n);
		if (i && n === "length") {
			let e = Number(r);
			o.forEach((t, n) => {
				(n === "length" || n === Ze || !v(n) && n >= e) && s(t);
			});
		} else switch ((n !== void 0 || o.has(void 0)) && s(o.get(n)), a && s(o.get(Ze)), t) {
			case "add":
				i ? a && s(o.get("length")) : (s(o.get(Ye)), f(e) && s(o.get(Xe)));
				break;
			case "delete":
				i || (s(o.get(Ye)), f(e) && s(o.get(Xe)));
				break;
			case "set": f(e) && s(o.get(Ye));
		}
	}
	Me();
}
function et(e) {
	let t = /* @__PURE__ */ R(e);
	return t === e ? t : (Qe(t, "iterate", Ze), /* @__PURE__ */ zt(e) ? t : t.map(Ht));
}
function tt(e) {
	return Qe(e = /* @__PURE__ */ R(e), "iterate", Ze), e;
}
function nt(e, t) {
	return /* @__PURE__ */ Rt(e) ? Ut(/* @__PURE__ */ Lt(e) ? Ht(t) : t) : Ht(t);
}
var rt = {
	__proto__: null,
	[Symbol.iterator]() {
		return it(this, Symbol.iterator, (e) => nt(this, e));
	},
	concat(...e) {
		return et(this).concat(...e.map((e) => d(e) ? et(e) : e));
	},
	entries() {
		return it(this, "entries", (e) => (e[1] = nt(this, e[1]), e));
	},
	every(e, t) {
		return ot(this, "every", e, t, void 0, arguments);
	},
	filter(e, t) {
		return ot(this, "filter", e, t, (e) => e.map((e) => nt(this, e)), arguments);
	},
	find(e, t) {
		return ot(this, "find", e, t, (e) => nt(this, e), arguments);
	},
	findIndex(e, t) {
		return ot(this, "findIndex", e, t, void 0, arguments);
	},
	findLast(e, t) {
		return ot(this, "findLast", e, t, (e) => nt(this, e), arguments);
	},
	findLastIndex(e, t) {
		return ot(this, "findLastIndex", e, t, void 0, arguments);
	},
	forEach(e, t) {
		return ot(this, "forEach", e, t, void 0, arguments);
	},
	includes(...e) {
		return ct(this, "includes", e);
	},
	indexOf(...e) {
		return ct(this, "indexOf", e);
	},
	join(e) {
		return et(this).join(e);
	},
	lastIndexOf(...e) {
		return ct(this, "lastIndexOf", e);
	},
	map(e, t) {
		return ot(this, "map", e, t, void 0, arguments);
	},
	pop() {
		return lt(this, "pop");
	},
	push(...e) {
		return lt(this, "push", e);
	},
	reduce(e, ...t) {
		return st(this, "reduce", e, t);
	},
	reduceRight(e, ...t) {
		return st(this, "reduceRight", e, t);
	},
	shift() {
		return lt(this, "shift");
	},
	some(e, t) {
		return ot(this, "some", e, t, void 0, arguments);
	},
	splice(...e) {
		return lt(this, "splice", e);
	},
	toReversed() {
		return et(this).toReversed();
	},
	toSorted(e) {
		return et(this).toSorted(e);
	},
	toSpliced(...e) {
		return et(this).toSpliced(...e);
	},
	unshift(...e) {
		return lt(this, "unshift", e);
	},
	values() {
		return it(this, "values", (e) => nt(this, e));
	}
};
function it(e, t, n) {
	let r = tt(e), i = r[t]();
	return r !== e && !/* @__PURE__ */ zt(e) && (i._next = i.next, i.next = () => {
		let e = i._next();
		return e.done || (e.value = n(e.value)), e;
	}), i;
}
var at = Array.prototype;
function ot(e, t, n, r, i, a) {
	let o = tt(e), s = o !== e && !/* @__PURE__ */ zt(e), c = o[t];
	if (c !== at[t]) {
		let t = c.apply(e, a);
		return s ? Ht(t) : t;
	}
	let l = n;
	o !== e && (s ? l = function(t, r) {
		return n.call(this, nt(e, t), r, e);
	} : n.length > 2 && (l = function(t, r) {
		return n.call(this, t, r, e);
	}));
	let u = c.call(o, l, r);
	return s && i ? i(u) : u;
}
function st(e, t, n, r) {
	let i = tt(e), a = i !== e && !/* @__PURE__ */ zt(e), o = n, s = !1;
	i !== e && (a ? (s = r.length === 0, o = function(t, r, i) {
		return s && (s = !1, t = nt(e, t)), n.call(this, t, nt(e, r), i, e);
	}) : n.length > 3 && (o = function(t, r, i) {
		return n.call(this, t, r, i, e);
	}));
	let c = i[t](o, ...r);
	return s ? nt(e, c) : c;
}
function ct(e, t, n) {
	let r = /* @__PURE__ */ R(e);
	Qe(r, "iterate", Ze);
	let i = r[t](...n);
	return (i === -1 || i === !1) && /* @__PURE__ */ Bt(n[0]) ? (n[0] = /* @__PURE__ */ R(n[0]), r[t](...n)) : i;
}
function lt(e, t, n = []) {
	Ve(), je();
	let r = (/* @__PURE__ */ R(e))[t].apply(e, n);
	return Me(), He(), r;
}
var ut = /* @__PURE__ */ e("__proto__,__v_isRef,__isVue"), dt = new Set(/* @__PURE__ */ Object.getOwnPropertyNames(Symbol).filter((e) => e !== "arguments" && e !== "caller").map((e) => Symbol[e]).filter(v));
function ft(e) {
	v(e) || (e = String(e));
	let t = /* @__PURE__ */ R(this);
	return Qe(t, "has", e), t.hasOwnProperty(e);
}
var pt = class {
	constructor(e = !1, t = !1) {
		this._isReadonly = e, this._isShallow = t;
	}
	get(e, t, n) {
		if (t === "__v_skip") return e.__v_skip;
		let r = this._isReadonly, i = this._isShallow;
		if (t === "__v_isReactive") return !r;
		if (t === "__v_isReadonly") return r;
		if (t === "__v_isShallow") return i;
		if (t === "__v_raw") return n === (r ? i ? jt : At : i ? kt : Ot).get(e) || Object.getPrototypeOf(e) === Object.getPrototypeOf(n) ? e : void 0;
		let a = d(e);
		if (!r) {
			let e;
			if (a && (e = rt[t])) return e;
			if (t === "hasOwnProperty") return ft;
		}
		let o = Reflect.get(e, t, /* @__PURE__ */ Wt(e) ? e : n);
		if ((v(t) ? dt.has(t) : ut(t)) || (r || Qe(e, "get", t), i)) return o;
		if (/* @__PURE__ */ Wt(o)) {
			let e = a && T(t) ? o : o.value;
			return r && y(e) ? /* @__PURE__ */ Ft(e) : e;
		}
		return y(o) ? r ? /* @__PURE__ */ Ft(o) : /* @__PURE__ */ Nt(o) : o;
	}
}, mt = class extends pt {
	constructor(e = !1) {
		super(!1, e);
	}
	set(e, t, n, r) {
		let i = e[t], a = d(e) && T(t);
		if (!this._isShallow) {
			let e = /* @__PURE__ */ Rt(i);
			if (!/* @__PURE__ */ zt(n) && !/* @__PURE__ */ Rt(n) && (i = /* @__PURE__ */ R(i), n = /* @__PURE__ */ R(n)), !a && /* @__PURE__ */ Wt(i) && !/* @__PURE__ */ Wt(n)) return e || (i.value = n), !0;
		}
		let o = a ? Number(t) < e.length : u(e, t), s = Reflect.set(e, t, n, /* @__PURE__ */ Wt(e) ? e : r);
		return e === /* @__PURE__ */ R(r) && s && (o ? j(n, i) && $e(e, "set", t, n, i) : $e(e, "add", t, n)), s;
	}
	deleteProperty(e, t) {
		let n = u(e, t), r = e[t], i = Reflect.deleteProperty(e, t);
		return i && n && $e(e, "delete", t, void 0, r), i;
	}
	has(e, t) {
		let n = Reflect.has(e, t);
		return (!v(t) || !dt.has(t)) && Qe(e, "has", t), n;
	}
	ownKeys(e) {
		return Qe(e, "iterate", d(e) ? "length" : Ye), Reflect.ownKeys(e);
	}
}, ht = class extends pt {
	constructor(e = !1) {
		super(!0, e);
	}
	set(e, t) {
		return !0;
	}
	deleteProperty(e, t) {
		return !0;
	}
}, gt = /* @__PURE__ */ new mt(), _t = /* @__PURE__ */ new ht(), vt = /* @__PURE__ */ new mt(!0), yt = (e) => e, bt = (e) => Reflect.getPrototypeOf(e);
function xt(e, t, n) {
	return function(...r) {
		let i = this.__v_raw, a = /* @__PURE__ */ R(i), o = f(a), c = e === "entries" || e === Symbol.iterator && o, l = e === "keys" && o, u = i[e](...r), d = n ? yt : t ? Ut : Ht;
		return !t && Qe(a, "iterate", l ? Xe : Ye), s(Object.create(u), { next() {
			let { value: e, done: t } = u.next();
			return t ? {
				value: e,
				done: t
			} : {
				value: c ? [d(e[0]), d(e[1])] : d(e),
				done: t
			};
		} });
	};
}
function St(e) {
	return function(...t) {
		return e === "delete" ? !1 : e === "clear" ? void 0 : this;
	};
}
function Ct(e, t) {
	let n = {
		get(n) {
			let r = this.__v_raw, i = /* @__PURE__ */ R(r), a = /* @__PURE__ */ R(n);
			e || (j(n, a) && Qe(i, "get", n), Qe(i, "get", a));
			let { has: o } = bt(i), s = t ? yt : e ? Ut : Ht;
			if (o.call(i, n)) return s(r.get(n));
			if (o.call(i, a)) return s(r.get(a));
			r !== i && r.get(n);
		},
		get size() {
			let t = this.__v_raw;
			return !e && Qe(/* @__PURE__ */ R(t), "iterate", Ye), t.size;
		},
		has(t) {
			let n = this.__v_raw, r = /* @__PURE__ */ R(n), i = /* @__PURE__ */ R(t);
			return e || (j(t, i) && Qe(r, "has", t), Qe(r, "has", i)), t === i ? n.has(t) : n.has(t) || n.has(i);
		},
		forEach(n, r) {
			let i = this, a = i.__v_raw, o = /* @__PURE__ */ R(a), s = t ? yt : e ? Ut : Ht;
			return !e && Qe(o, "iterate", Ye), a.forEach((e, t) => n.call(r, s(e), s(t), i));
		}
	};
	return s(n, e ? {
		add: St("add"),
		set: St("set"),
		delete: St("delete"),
		clear: St("clear")
	} : {
		add(e) {
			let n = /* @__PURE__ */ R(this), r = bt(n), i = /* @__PURE__ */ R(e), a = !t && !/* @__PURE__ */ zt(e) && !/* @__PURE__ */ Rt(e) ? i : e;
			return r.has.call(n, a) || j(e, a) && r.has.call(n, e) || j(i, a) && r.has.call(n, i) || (n.add(a), $e(n, "add", a, a)), this;
		},
		set(e, n) {
			!t && !/* @__PURE__ */ zt(n) && !/* @__PURE__ */ Rt(n) && (n = /* @__PURE__ */ R(n));
			let r = /* @__PURE__ */ R(this), { has: i, get: a } = bt(r), o = i.call(r, e);
			o ||= (e = /* @__PURE__ */ R(e), i.call(r, e));
			let s = a.call(r, e);
			return r.set(e, n), o ? j(n, s) && $e(r, "set", e, n, s) : $e(r, "add", e, n), this;
		},
		delete(e) {
			let t = /* @__PURE__ */ R(this), { has: n, get: r } = bt(t), i = n.call(t, e);
			i ||= (e = /* @__PURE__ */ R(e), n.call(t, e));
			let a = r ? r.call(t, e) : void 0, o = t.delete(e);
			return i && $e(t, "delete", e, void 0, a), o;
		},
		clear() {
			let e = /* @__PURE__ */ R(this), t = e.size !== 0, n = e.clear();
			return t && $e(e, "clear", void 0, void 0, void 0), n;
		}
	}), [
		"keys",
		"values",
		"entries",
		Symbol.iterator
	].forEach((r) => {
		n[r] = xt(r, e, t);
	}), n;
}
function wt(e, t) {
	let n = Ct(e, t);
	return (t, r, i) => r === "__v_isReactive" ? !e : r === "__v_isReadonly" ? e : r === "__v_raw" ? t : Reflect.get(u(n, r) && r in t ? n : t, r, i);
}
var Tt = { get: /* @__PURE__ */ wt(!1, !1) }, Et = { get: /* @__PURE__ */ wt(!1, !0) }, Dt = { get: /* @__PURE__ */ wt(!0, !1) }, Ot = /* @__PURE__ */ new WeakMap(), kt = /* @__PURE__ */ new WeakMap(), At = /* @__PURE__ */ new WeakMap(), jt = /* @__PURE__ */ new WeakMap();
function Mt(e) {
	switch (e) {
		case "Object":
		case "Array": return 1;
		case "Map":
		case "Set":
		case "WeakMap":
		case "WeakSet": return 2;
		default: return 0;
	}
}
// @__NO_SIDE_EFFECTS__
function Nt(e) {
	return /* @__PURE__ */ Rt(e) ? e : It(e, !1, gt, Tt, Ot);
}
// @__NO_SIDE_EFFECTS__
function Pt(e) {
	return It(e, !1, vt, Et, kt);
}
// @__NO_SIDE_EFFECTS__
function Ft(e) {
	return It(e, !0, _t, Dt, At);
}
function It(e, t, n, r, i) {
	if (!y(e) || e.__v_raw && !(t && e.__v_isReactive) || e.__v_skip || !Object.isExtensible(e)) return e;
	let a = i.get(e);
	if (a) return a;
	let o = Mt(C(e));
	if (o === 0) return e;
	let s = new Proxy(e, o === 2 ? r : n);
	return i.set(e, s), s;
}
// @__NO_SIDE_EFFECTS__
function Lt(e) {
	return /* @__PURE__ */ Rt(e) ? /* @__PURE__ */ Lt(e.__v_raw) : !!(e && e.__v_isReactive);
}
// @__NO_SIDE_EFFECTS__
function Rt(e) {
	return !!(e && e.__v_isReadonly);
}
// @__NO_SIDE_EFFECTS__
function zt(e) {
	return !!(e && e.__v_isShallow);
}
// @__NO_SIDE_EFFECTS__
function Bt(e) {
	return e ? !!e.__v_raw : !1;
}
// @__NO_SIDE_EFFECTS__
function R(e) {
	let t = e && e.__v_raw;
	return t ? /* @__PURE__ */ R(t) : e;
}
function Vt(e) {
	return !u(e, "__v_skip") && Object.isExtensible(e) && M(e, "__v_skip", !0), e;
}
var Ht = (e) => y(e) ? /* @__PURE__ */ Nt(e) : e, Ut = (e) => y(e) ? /* @__PURE__ */ Ft(e) : e;
// @__NO_SIDE_EFFECTS__
function Wt(e) {
	return e ? e.__v_isRef === !0 : !1;
}
// @__NO_SIDE_EFFECTS__
function z(e) {
	return Kt(e, !1);
}
// @__NO_SIDE_EFFECTS__
function Gt(e) {
	return Kt(e, !0);
}
function Kt(e, t) {
	return /* @__PURE__ */ Wt(e) ? e : new qt(e, t);
}
var qt = class {
	constructor(e, t) {
		this.dep = new Ke(), this.__v_isRef = !0, this.__v_isShallow = !1, this._rawValue = t ? e : /* @__PURE__ */ R(e), this._value = t ? e : Ht(e), this.__v_isShallow = t;
	}
	get value() {
		return this.dep.track(), this._value;
	}
	set value(e) {
		let t = this._rawValue, n = this.__v_isShallow || /* @__PURE__ */ zt(e) || /* @__PURE__ */ Rt(e);
		e = n ? e : /* @__PURE__ */ R(e), j(e, t) && (this._rawValue = e, this._value = n ? e : Ht(e), this.dep.trigger());
	}
};
function B(e) {
	return /* @__PURE__ */ Wt(e) ? e.value : e;
}
var Jt = {
	get: (e, t, n) => t === "__v_raw" ? e : B(Reflect.get(e, t, n)),
	set: (e, t, n, r) => {
		let i = e[t];
		return /* @__PURE__ */ Wt(i) && !/* @__PURE__ */ Wt(n) ? (i.value = n, !0) : Reflect.set(e, t, n, r);
	}
};
function Yt(e) {
	return /* @__PURE__ */ Lt(e) ? e : new Proxy(e, Jt);
}
var Xt = class {
	constructor(e) {
		this.__v_isRef = !0, this._value = void 0;
		let t = this.dep = new Ke(), { get: n, set: r } = e(t.track.bind(t), t.trigger.bind(t));
		this._get = n, this._set = r;
	}
	get value() {
		return this._value = this._get();
	}
	set value(e) {
		this._set(e);
	}
};
function Zt(e) {
	return new Xt(e);
}
var Qt = class {
	constructor(e, t, n) {
		this.fn = e, this.setter = t, this._value = void 0, this.dep = new Ke(this), this.__v_isRef = !0, this.deps = void 0, this.depsTail = void 0, this.flags = 16, this.globalVersion = We - 1, this.next = void 0, this.effect = this, this.__v_isReadonly = !t, this.isSSR = n;
	}
	notify() {
		if (this.flags |= 16, !(this.flags & 8) && L !== this) return Ae(this, !0), !0;
	}
	get value() {
		let e = this.dep.track();
		return Ie(this), e && (e.version = this.dep.version), this._value;
	}
	set value(e) {
		this.setter && this.setter(e);
	}
};
// @__NO_SIDE_EFFECTS__
function $t(e, t, n = !1) {
	let r, i;
	return g(e) ? r = e : (r = e.get, i = e.set), new Qt(r, i, n);
}
var en = {}, tn = /* @__PURE__ */ new WeakMap(), nn = void 0;
function rn(e, t = !1, n = nn) {
	if (n) {
		let t = tn.get(n);
		t || tn.set(n, t = []), t.push(e);
	}
}
function an(e, n, i = t) {
	let { immediate: a, deep: o, once: s, scheduler: l, augmentJob: u, call: f } = i, p = (e) => o ? e : /* @__PURE__ */ zt(e) || o === !1 || o === 0 ? on(e, 1) : on(e), m, h, _, v, y = !1, b = !1;
	if (/* @__PURE__ */ Wt(e) ? (h = () => e.value, y = /* @__PURE__ */ zt(e)) : /* @__PURE__ */ Lt(e) ? (h = () => p(e), y = !0) : d(e) ? (b = !0, y = e.some((e) => /* @__PURE__ */ Lt(e) || /* @__PURE__ */ zt(e)), h = () => e.map((e) => {
		if (/* @__PURE__ */ Wt(e)) return e.value;
		if (/* @__PURE__ */ Lt(e)) return p(e);
		if (g(e)) return f ? f(e, 2) : e();
	})) : h = g(e) ? n ? f ? () => f(e, 2) : e : () => {
		if (_) {
			Ve();
			try {
				_();
			} finally {
				He();
			}
		}
		let t = nn;
		nn = m;
		try {
			return f ? f(e, 3, [v]) : e(v);
		} finally {
			nn = t;
		}
	} : r, n && o) {
		let e = h, t = o === !0 ? Infinity : o;
		h = () => on(e(), t);
	}
	let x = Ce(), S = () => {
		m.stop(), x && x.active && c(x.effects, m);
	};
	if (s && n) {
		let e = n;
		n = (...t) => {
			let n = e(...t);
			return S(), n;
		};
	}
	let C = b ? Array(e.length).fill(en) : en, w = (e) => {
		if (m.flags & 1 && (m.dirty || e)) {
			if (n) {
				let t = m.run();
				if (e || o || y || (b ? t.some((e, t) => j(e, C[t])) : j(t, C))) {
					_ && _();
					let e = nn;
					nn = m;
					try {
						let e = [
							t,
							C === en ? void 0 : b && C[0] === en ? [] : C,
							v
						];
						C = t, f ? f(n, 3, e) : n(...e);
					} finally {
						nn = e;
					}
				}
			} else m.run();
		}
	};
	return u && u(w), m = new Ee(h), m.scheduler = l ? () => l(w, !1) : w, v = (e) => rn(e, !1, m), _ = m.onStop = () => {
		let e = tn.get(m);
		if (e) {
			if (f) f(e, 4);
			else for (let t of e) t();
			tn.delete(m);
		}
	}, n ? a ? w(!0) : C = m.run() : l ? l(w.bind(null, !0), !0) : m.run(), S.pause = m.pause.bind(m), S.resume = m.resume.bind(m), S.stop = S, S;
}
function on(e, t = Infinity, n) {
	if (t <= 0 || !y(e) || e.__v_skip || (n ||= /* @__PURE__ */ new Map(), (n.get(e) || 0) >= t)) return e;
	if (n.set(e, t), t--, /* @__PURE__ */ Wt(e)) on(e.value, t, n);
	else if (d(e)) for (let r = 0; r < e.length; r++) on(e[r], t, n);
	else if (p(e) || f(e)) e.forEach((e) => {
		on(e, t, n);
	});
	else if (w(e)) {
		for (let r in e) on(e[r], t, n);
		for (let r of Object.getOwnPropertySymbols(e)) Object.prototype.propertyIsEnumerable.call(e, r) && on(e[r], t, n);
	}
	return e;
}
//#endregion
//#region node_modules/@vue/runtime-core/dist/runtime-core.esm-bundler.js
function sn(e, t, n, r) {
	try {
		return r ? e(...r) : e();
	} catch (e) {
		ln(e, t, n);
	}
}
function cn(e, t, n, r) {
	if (g(e)) {
		let i = sn(e, t, n, r);
		return i && b(i) && i.catch((e) => {
			ln(e, t, n);
		}), i;
	}
	if (d(e)) {
		let i = [];
		for (let a = 0; a < e.length; a++) i.push(cn(e[a], t, n, r));
		return i;
	}
}
function ln(e, n, r, i = !0) {
	let a = n ? n.vnode : null, { errorHandler: o, throwUnhandledErrorInProduction: s } = n && n.appContext.config || t;
	if (n) {
		let t = n.parent, i = n.proxy, a = `https://vuejs.org/error-reference/#runtime-${r}`;
		for (; t;) {
			let n = t.ec;
			if (n) {
				for (let t = 0; t < n.length; t++) if (n[t](e, i, a) === !1) return;
			}
			t = t.parent;
		}
		if (o) {
			Ve(), sn(o, null, 10, [
				e,
				i,
				a
			]), He();
			return;
		}
	}
	un(e, r, a, i, s);
}
function un(e, t, n, r = !0, i = !1) {
	if (i) throw e;
	console.error(e);
}
var dn = [], fn = -1, pn = [], mn = null, hn = 0, gn = /* @__PURE__ */ Promise.resolve(), _n = null;
function vn(e) {
	let t = _n || gn;
	return e ? t.then(this ? e.bind(this) : e) : t;
}
function yn(e) {
	let t = fn + 1, n = dn.length;
	for (; t < n;) {
		let r = t + n >>> 1, i = dn[r], a = Tn(i);
		a < e || a === e && i.flags & 2 ? t = r + 1 : n = r;
	}
	return t;
}
function bn(e) {
	if (!(e.flags & 1)) {
		let t = Tn(e), n = dn[dn.length - 1];
		!n || !(e.flags & 2) && t >= Tn(n) ? dn.push(e) : dn.splice(yn(t), 0, e), e.flags |= 1, xn();
	}
}
function xn() {
	_n ||= gn.then(En);
}
function Sn(e) {
	if (!d(e)) mn && e.id === -1 ? mn.splice(hn + 1, 0, e) : e.flags & 1 || (pn.push(e), e.flags |= 1);
	else for (let t = 0; t < e.length; t++) pn.push(e[t]);
	xn();
}
function Cn(e, t, n = fn + 1) {
	for (; n < dn.length; n++) {
		let t = dn[n];
		if (t && t.flags & 2) {
			if (e && t.id !== e.uid) continue;
			dn.splice(n, 1), n--, t.flags & 4 && (t.flags &= -2), t(), t.flags & 4 || (t.flags &= -2);
		}
	}
}
function wn(e) {
	if (pn.length) {
		let e = [...new Set(pn)].sort((e, t) => Tn(e) - Tn(t));
		if (pn.length = 0, mn) {
			for (let t = 0; t < e.length; t++) mn.push(e[t]);
			return;
		}
		for (mn = e, hn = 0; hn < mn.length; hn++) {
			let e = mn[hn];
			e.flags & 4 && (e.flags &= -2), e.flags & 8 || e(), e.flags &= -2;
		}
		mn = null, hn = 0;
	}
}
var Tn = (e) => e.id == null ? e.flags & 2 ? -1 : Infinity : e.id;
function En(e) {
	try {
		for (fn = 0; fn < dn.length; fn++) {
			let e = dn[fn];
			e && !(e.flags & 8) && (e.flags & 4 && (e.flags &= -2), sn(e, e.i, e.i ? 15 : 14), e.flags & 4 || (e.flags &= -2));
		}
	} finally {
		for (; fn < dn.length; fn++) {
			let e = dn[fn];
			e && (e.flags &= -2);
		}
		fn = -1, dn.length = 0, wn(e), _n = null, (dn.length || pn.length) && En(e);
	}
}
var Dn = null, On = null;
function kn(e) {
	let t = Dn;
	return Dn = e, On = e && e.type.__scopeId || null, t;
}
function An(e, t = Dn, n) {
	if (!t || e._n) return e;
	let r = (...n) => {
		r._d && _i(-1);
		let i = kn(t), a = pi.length, o;
		try {
			o = e(...n);
		} finally {
			for (let e = pi.length; e > a; e--) hi();
			kn(i), r._d && _i(1);
		}
		return o;
	};
	return r._n = !0, r._c = !0, r._d = !0, r;
}
function jn(e, n) {
	if (Dn === null) return e;
	let r = Ji(Dn), i = e.dirs ||= [];
	for (let e = 0; e < n.length; e++) {
		let [a, o, s, c = t] = n[e];
		a && (g(a) && (a = {
			mounted: a,
			updated: a
		}), a.deep && on(o), i.push({
			dir: a,
			instance: r,
			value: o,
			oldValue: void 0,
			arg: s,
			modifiers: c
		}));
	}
	return e;
}
function Mn(e, t, n, r) {
	let i = e.dirs, a = t && t.dirs;
	for (let o = 0; o < i.length; o++) {
		let s = i[o];
		a && (s.oldValue = a[o].value);
		let c = s.dir[r];
		c && (Ve(), cn(c, n, 8, [
			e.el,
			s,
			e,
			t
		]), He());
	}
}
function Nn(e, t) {
	if (Pi) {
		let n = Pi.provides, r = Pi.parent && Pi.parent.provides;
		r === n && (n = Pi.provides = Object.create(r)), n[e] = t;
	}
}
function Pn(e, t, n = !1) {
	let r = Fi();
	if (r || xr) {
		let i = xr ? xr._context.provides : r ? r.parent == null || r.ce ? r.vnode.appContext && r.vnode.appContext.provides : r.parent.provides : void 0;
		if (i && e in i) return i[e];
		if (arguments.length > 1) return n && g(t) ? t.call(r && r.proxy) : t;
	}
}
var Fn = /* @__PURE__ */ Symbol.for("v-scx"), In = () => Pn(Fn);
function Ln(e, t) {
	return Rn(e, null, { flush: "sync" });
}
function V(e, t, n) {
	return Rn(e, t, n);
}
function Rn(e, n, i = t) {
	let { immediate: a, deep: o, flush: c, once: l } = i, u = s({}, i), d = n && a || !n && c !== "post", f;
	if (Vi) {
		if (c === "sync") {
			let e = In();
			f = e.__watcherHandles ||= [];
		} else if (!d) {
			let e = () => {};
			return e.stop = r, e.resume = r, e.pause = r, e;
		}
	}
	let p = Pi;
	u.call = (e, t, n) => cn(e, p, t, n);
	let m = !1;
	c === "post" ? u.scheduler = (e) => {
		Zr(e, p && p.suspense);
	} : c !== "sync" && (m = !0, u.scheduler = (e, t) => {
		t ? e() : bn(e);
	}), u.augmentJob = (e) => {
		n && (e.flags |= 4), m && (e.flags |= 2, p && (e.id = p.uid, e.i = p));
	};
	let h = an(e, n, u);
	return Vi && (f ? f.push(h) : d && h()), h;
}
var zn = /* @__PURE__ */ Symbol("_vte"), Bn = (e) => e.__isTeleport, Vn = /* @__PURE__ */ Symbol("_leaveCb");
function Hn(e) {
	let t = e[0];
	if (e.length > 1) {
		for (let n of e) if (n.type !== di) {
			t = n;
			break;
		}
	}
	return t;
}
function Un(e) {
	if (!$n(e)) return Bn(e.type) && e.children ? Hn(e.children) : e;
	if (e.component) return e.component.subTree;
	let { shapeFlag: t, children: n } = e;
	if (n) {
		if (t & 16) return n[0];
		if (t & 32 && g(n.default)) return n.default();
	}
}
function Wn(e, t) {
	if (e.shapeFlag & 6 && e.component) {
		e.transition = t;
		let n = e.component.subTree;
		Wn(Bn(n.type) && Un(n) || n, t);
	} else e.shapeFlag & 128 ? (e.ssContent.transition = t.clone(e.ssContent), e.ssFallback.transition = t.clone(e.ssFallback)) : e.transition = t;
}
// @__NO_SIDE_EFFECTS__
function Gn(e, t) {
	return g(e) ? /* @__PURE__ */ s({ name: e.name }, t, { setup: e }) : e;
}
function Kn() {
	let e = Fi();
	return e ? (e.appContext.config.idPrefix || "v") + "-" + e.ids[0] + e.ids[1]++ : "";
}
function qn(e) {
	e.ids = [
		e.ids[0] + e.ids[2]++ + "-",
		0,
		0
	];
}
function Jn(e, t) {
	let n;
	return !!((n = Object.getOwnPropertyDescriptor(e, t)) && !n.configurable);
}
var Yn = /* @__PURE__ */ new WeakMap();
function Xn(e, n, r, a, o = !1) {
	if (d(e)) {
		e.forEach((e, t) => Xn(e, n && (d(n) ? n[t] : n), r, a, o));
		return;
	}
	if (Qn(a) && !o) {
		a.shapeFlag & 512 && a.type.__asyncResolved && a.component.subTree.component && Xn(e, n, r, a.component.subTree);
		return;
	}
	let s = a.shapeFlag & 4 ? Ji(a.component) : a.el, l = o ? null : s, { i: f, r: p } = e, m = n && n.r, h = f.refs === t ? f.refs = {} : f.refs, v = f.setupState, y = /* @__PURE__ */ R(v), b = v === t ? i : (e) => !Jn(h, e) && u(y, e), x = (e, t) => !(t && Jn(h, t));
	if (m != null && m !== p) {
		if (Zn(n), _(m)) h[m] = null, b(m) && (v[m] = null);
		else if (/* @__PURE__ */ Wt(m)) {
			let e = n;
			x(m, e.k) && (m.value = null), e.k && (h[e.k] = null);
		}
	}
	if (g(p)) sn(p, f, 12, [l, h]);
	else {
		let t = _(p), n = /* @__PURE__ */ Wt(p);
		if (t || n) {
			let i = () => {
				if (e.f) {
					let n = t ? b(p) ? v[p] : h[p] : x(p) || !e.k ? p.value : h[e.k];
					if (o) d(n) && c(n, s);
					else if (d(n)) n.includes(s) || n.push(s);
					else if (t) h[p] = [s], b(p) && (v[p] = h[p]);
					else {
						let t = [s];
						x(p, e.k) && (p.value = t), e.k && (h[e.k] = t);
					}
				} else t ? (h[p] = l, b(p) && (v[p] = l)) : n && (x(p, e.k) && (p.value = l), e.k && (h[e.k] = l));
			};
			if (l) {
				let t = () => {
					i(), Yn.delete(e);
				};
				t.id = -1, Yn.set(e, t), Zr(t, r);
			} else Zn(e), i();
		}
	}
}
function Zn(e) {
	let t = Yn.get(e);
	t && (t.flags |= 8, Yn.delete(e));
}
oe().requestIdleCallback, oe().cancelIdleCallback;
var Qn = (e) => !!e.type.__asyncLoader, $n = (e) => e.type.__isKeepAlive, er = {
	name: "KeepAlive",
	__isKeepAlive: !0,
	props: {
		include: [
			String,
			RegExp,
			Array
		],
		exclude: [
			String,
			RegExp,
			Array
		],
		max: [String, Number]
	},
	setup(e, { slots: t }) {
		let n = Fi(), r = n.ctx;
		if (!r.renderer) return () => {
			let e = t.default && t.default();
			return e && e.length === 1 ? e[0] : e;
		};
		let i = /* @__PURE__ */ new Map(), a = /* @__PURE__ */ new Set(), o = null, s = n.suspense, { renderer: { p: c, m: l, um: u, o: { createElement: d } } } = r, f = d("div");
		r.activate = (e, t, n, r, i) => {
			let a = e.component;
			l(e, t, n, 0, s), c(a.vnode, e, t, n, a, s, r, e.slotScopeIds, i), Zr(() => {
				a.isDeactivated = !1, a.a && re(a.a);
				let t = e.props && e.props.onVnodeMounted;
				t && Ai(t, a.parent, e);
			}, s);
		}, r.deactivate = (e) => {
			let t = e.component;
			oi(t.m), oi(t.a), l(e, f, null, 1, s), Zr(() => {
				t.da && re(t.da);
				let n = e.props && e.props.onVnodeUnmounted;
				n && Ai(n, t.parent, e), t.isDeactivated = !0;
			}, s);
		};
		function p(e) {
			nr(e), u(e, n, s, !0);
		}
		function m(e) {
			i.forEach((t, n) => {
				let r = Yi(Qn(t) ? t.type.__asyncResolved || {} : t.type);
				r && !e(r) && h(n);
			});
		}
		function h(e) {
			let t = i.get(e);
			t && (!o || !bi(t, o)) ? p(t) : o && nr(o), i.delete(e), a.delete(e);
		}
		V(() => [e.include, e.exclude], ([e, t]) => {
			e && m((t) => tr(e, t)), t && m((e) => !tr(t, e));
		}, {
			flush: "post",
			deep: !0
		});
		let g = null, _ = () => {
			g != null && (ci(n.subTree.type) ? Zr(() => {
				let e = rr(n.subTree);
				e.component && i.set(g, e);
			}, n.subTree.suspense) : i.set(g, rr(n.subTree)));
		};
		return or(_), sr(_), cr(() => {
			i.forEach((e) => {
				let { subTree: t, suspense: r } = n, i = rr(t);
				if (e.type === i.type && e.key === i.key) {
					nr(i);
					let e = i.component.da;
					e && Zr(e, r);
					return;
				}
				p(e);
			});
		}), () => {
			if (g = null, !t.default) return o = null;
			let n = t.default(), r = n[0];
			if (n.length > 1) return o = null, n;
			if (!yi(r) || !(r.shapeFlag & 4) && !(r.shapeFlag & 128)) return o = null, r;
			let s = rr(r);
			if (s.type === di) return o = null, s;
			let c = s.type, l = Yi(Qn(s) ? s.type.__asyncResolved || {} : c), { include: u, exclude: d, max: f } = e;
			if (u && (!l || !tr(u, l)) || d && l && tr(d, l)) return s.shapeFlag &= -257, o = s, r;
			let p = s.key == null ? c : s.key, m = i.get(p);
			return s.el && (s = Ti(s), r.shapeFlag & 128 && (r.ssContent = s)), g = p, m ? (s.el = m.el, s.component = m.component, s.transition && Wn(s, s.transition), s.shapeFlag |= 512, a.delete(p), a.add(p)) : (a.add(p), f && a.size > parseInt(f, 10) && h(a.values().next().value)), s.shapeFlag |= 256, o = s, ci(r.type) ? r : s;
		};
	}
};
function tr(e, t) {
	return d(e) ? e.some((e) => tr(e, t)) : _(e) ? e.split(",").includes(t) : h(e) ? (e.lastIndex = 0, e.test(t)) : !1;
}
function nr(e) {
	e.shapeFlag &= -257, e.shapeFlag &= -513;
}
function rr(e) {
	return e.shapeFlag & 128 ? e.ssContent : e;
}
function ir(e, t, n = Pi, r = !1) {
	if (n) {
		let i = n[e] || (n[e] = []), a = t.__weh ||= (...r) => {
			Ve();
			let i = Ri(n), a = cn(t, n, e, r);
			return i(), He(), a;
		};
		return r ? i.unshift(a) : i.push(a), a;
	}
}
var ar = (e) => (t, n = Pi) => {
	(!Vi || e === "sp") && ir(e, (...e) => t(...e), n);
}, or = ar("m"), sr = ar("u"), cr = ar("bum"), lr = /* @__PURE__ */ Symbol.for("v-ndc");
function H(e, t, n, r) {
	let i, a = n && n[r], o = d(e);
	if (o || _(e)) {
		let n = o && /* @__PURE__ */ Lt(e), r = !1, s = !1;
		n && (r = !/* @__PURE__ */ zt(e), s = /* @__PURE__ */ Rt(e), e = tt(e)), i = Array(e.length);
		for (let n = 0, o = e.length; n < o; n++) i[n] = t(r ? s ? Ut(Ht(e[n])) : Ht(e[n]) : e[n], n, void 0, a && a[n]);
	} else if (typeof e == "number") {
		i = Array(e);
		for (let n = 0; n < e; n++) i[n] = t(n + 1, n, void 0, a && a[n]);
	} else if (y(e)) {
		if (e[Symbol.iterator]) i = Array.from(e, (e, n) => t(e, n, void 0, a && a[n]));
		else {
			let n = Object.keys(e);
			i = Array(n.length);
			for (let r = 0, o = n.length; r < o; r++) {
				let o = n[r];
				i[r] = t(e[o], o, r, a && a[r]);
			}
		}
	} else i = [];
	return n && (n[r] = i), i;
}
function ur(e, t, n, r, i, a) {
	if (n ??= {}, Dn.ce || Dn.parent && Qn(Dn.parent) && Dn.parent.ce) {
		let e = a != null && n.key == null ? s({}, n, { key: a }) : n, i = Object.keys(e).length > 0;
		return t !== "default" && (e.name = t), W(), K(U, null, [J("slot", e, r && r())], i ? -2 : 64);
	}
	let o = e[t];
	o && o._c && (o._d = !1);
	let c = pi.length;
	W();
	let l;
	try {
		let i = o && dr(o(n)), s = n.key || a || i && i.key;
		l = K(U, { key: (s && !v(s) ? s : `_${t}`) + (!i && r ? "_fb" : "") }, i || (r ? r() : []), i && e._ === 1 ? 64 : -2);
	} catch (e) {
		for (let e = pi.length; e > c; e--) hi();
		throw e;
	} finally {
		o && o._c && (o._d = !0);
	}
	return !i && l.scopeId && (l.slotScopeIds = [l.scopeId + "-s"]), l;
}
function dr(e) {
	return e.some((e) => !yi(e) || !(e.type === di || e.type === U && !dr(e.children))) ? e : null;
}
var fr = (e) => e ? Bi(e) ? Ji(e) : fr(e.parent) : null, pr = /* @__PURE__ */ s(/* @__PURE__ */ Object.create(null), {
	$: (e) => e,
	$el: (e) => e.vnode.el,
	$data: (e) => e.data,
	$props: (e) => e.props,
	$attrs: (e) => e.attrs,
	$slots: (e) => e.slots,
	$refs: (e) => e.refs,
	$parent: (e) => fr(e.parent),
	$root: (e) => fr(e.root),
	$host: (e) => e.ce,
	$emit: (e) => e.emit,
	$options: (e) => e.type,
	$forceUpdate: (e) => e.f ||= () => {
		bn(e.update);
	},
	$nextTick: (e) => e.n ||= vn.bind(e.proxy),
	$watch: (e) => r
}), mr = (e, n) => e !== t && !e.__isScriptSetup && u(e, n), hr = {
	get({ _: e }, n) {
		if (n === "__v_skip") return !0;
		let { ctx: r, setupState: i, data: a, props: o, accessCache: s, type: c, appContext: l } = e;
		if (n[0] !== "$") {
			let e = s[n];
			if (e !== void 0) switch (e) {
				case 1: return i[n];
				case 2: return a[n];
				case 4: return r[n];
				case 3: return o[n];
			}
			else if (mr(i, n)) return s[n] = 1, i[n];
			else if (u(o, n)) return s[n] = 3, o[n];
			else if (r !== t && u(r, n)) return s[n] = 4, r[n];
			else s[n] = 0;
		}
		let d = pr[n], f, p;
		if (d) return n === "$attrs" && Qe(e.attrs, "get", ""), d(e);
		if ((f = c.__cssModules) && (f = f[n])) return f;
		if (r !== t && u(r, n)) return s[n] = 4, r[n];
		if (p = l.config.globalProperties, u(p, n)) return p[n];
	},
	set({ _: e }, t, n) {
		let { data: r, setupState: i, ctx: a } = e;
		return mr(i, t) ? (i[t] = n, !0) : u(e.props, t) || t[0] === "$" && t.slice(1) in e ? !1 : (a[t] = n, !0);
	},
	has({ _: { data: e, setupState: t, accessCache: n, ctx: r, appContext: i, props: a, type: o } }, s) {
		let c;
		return !!(n[s] || mr(t, s) || u(a, s) || u(r, s) || u(pr, s) || u(i.config.globalProperties, s) || (c = o.__cssModules) && c[s]);
	},
	defineProperty(e, t, n) {
		return n.get == null ? u(n, "value") && this.set(e, t, n.value, null) : e._.accessCache[t] = 0, Reflect.defineProperty(e, t, n);
	}
};
function gr(e) {
	return d(e) ? e.reduce((e, t) => (e[t] = null, e), {}) : e;
}
function _r(e, t) {
	return !e || !t ? e || t : d(e) && d(t) ? e.concat(t) : s({}, gr(e), gr(t));
}
function vr() {
	return {
		app: null,
		config: {
			isNativeTag: i,
			performance: !1,
			globalProperties: {},
			optionMergeStrategies: {},
			errorHandler: void 0,
			warnHandler: void 0,
			compilerOptions: {}
		},
		mixins: [],
		components: {},
		directives: {},
		provides: /* @__PURE__ */ Object.create(null),
		optionsCache: /* @__PURE__ */ new WeakMap(),
		propsCache: /* @__PURE__ */ new WeakMap(),
		emitsCache: /* @__PURE__ */ new WeakMap()
	};
}
var yr = 0;
function br(e, t) {
	return function(n, r = null) {
		g(n) || (n = s({}, n)), r != null && !y(r) && (r = null);
		let i = vr(), a = /* @__PURE__ */ new WeakSet(), o = [], c = !1, l = i.app = {
			_uid: yr++,
			_component: n,
			_props: r,
			_container: null,
			_context: i,
			_instance: null,
			version: Zi,
			get config() {
				return i.config;
			},
			set config(e) {},
			use(e, ...t) {
				return a.has(e) || (e && g(e.install) ? (a.add(e), e.install(l, ...t)) : g(e) && (a.add(e), e(l, ...t))), l;
			},
			mixin(e) {
				return l;
			},
			component(e, t) {
				return t ? (i.components[e] = t, l) : i.components[e];
			},
			directive(e, t) {
				return t ? (i.directives[e] = t, l) : i.directives[e];
			},
			mount(a, o, s) {
				if (!c) {
					let u = l._ceVNode || J(n, r);
					return u.appContext = i, s === !0 ? s = "svg" : s === !1 && (s = void 0), o && t ? t(u, a) : e(u, a, s), c = !0, l._container = a, a.__vue_app__ = l, Ji(u.component);
				}
			},
			onUnmount(e) {
				o.push(e);
			},
			unmount() {
				c && (cn(o, l._instance, 16), e(null, l._container), delete l._container.__vue_app__);
			},
			provide(e, t) {
				return i.provides[e] = t, l;
			},
			runWithContext(e) {
				let t = xr;
				xr = l;
				try {
					return e();
				} finally {
					xr = t;
				}
			}
		};
		return l;
	};
}
var xr = null;
function Sr(e, n, r = t) {
	let i = Fi(), a = k(n), o = A(n), s = Cr(e, a), c = Zt((s, c) => {
		let l, u = t, d;
		return Ln(() => {
			let t = e[a];
			j(l, t) && (l = t, c());
		}), {
			get() {
				return s(), r.get ? r.get(l) : l;
			},
			set(e) {
				let s = r.set ? r.set(e) : e;
				if (!j(s, l) && !(u !== t && j(e, u))) return;
				let f = i.vnode.props, p = !!(f && (n in f || a in f || o in f) && (`onUpdate:${n}` in f || `onUpdate:${a}` in f || `onUpdate:${o}` in f));
				p || (l = e, c()), i.emit(`update:${n}`, s), j(e, u) && (j(e, s) && !j(s, d) || p && u !== t && !j(s, l)) && c(), u = e, d = s;
			}
		};
	});
	return c[Symbol.iterator] = () => {
		let e = 0;
		return { next() {
			return e < 2 ? {
				value: e++ ? s || t : c,
				done: !1
			} : { done: !0 };
		} };
	}, c;
}
var Cr = (e, t) => t === "modelValue" || t === "model-value" ? e.modelModifiers : e[`${t}Modifiers`] || e[`${k(t)}Modifiers`] || e[`${A(t)}Modifiers`];
function wr(e, n, ...r) {
	if (e.isUnmounted) return;
	let i = e.vnode.props || t, a = r, o = n.startsWith("update:"), s = o && Cr(i, n.slice(7));
	s && (s.trim && (a = r.map((e) => _(e) ? e.trim() : e)), s.number && (a = a.map(N)));
	let c, l = i[c = ne(n)] || i[c = ne(k(n))];
	!l && o && (l = i[c = ne(A(n))]), l && cn(l, e, 6, a);
	let u = i[c + "Once"];
	if (u) {
		if (!e.emitted) e.emitted = {};
		else if (e.emitted[c]) return;
		e.emitted[c] = !0, cn(u, e, 6, a);
	}
}
function Tr(e, t, n = !1) {
	let r = t.emitsCache, i = r.get(e);
	if (i !== void 0) return i;
	let a = e.emits, o = {};
	return a ? (d(a) ? a.forEach((e) => o[e] = null) : s(o, a), y(e) && r.set(e, o), o) : (y(e) && r.set(e, null), null);
}
function Er(e, t) {
	return !e || !a(t) ? !1 : (t = t.slice(2), t = t === "Once" ? t : t.replace(/Once$/, ""), u(e, t[0].toLowerCase() + t.slice(1)) || u(e, A(t)) || u(e, t));
}
function Dr(e) {
	let { type: t, vnode: n, proxy: r, withProxy: i, propsOptions: [a], slots: s, attrs: c, emit: l, render: u, renderCache: d, props: f, data: p, setupState: m, ctx: h, inheritAttrs: g } = e, _ = kn(e), v, y;
	try {
		if (n.shapeFlag & 4) {
			let e = i || r, t = e;
			v = Ei(u.call(t, e, d, f, m, p, h)), y = c;
		} else {
			let e = t;
			v = Ei(e.length > 1 ? e(f, {
				attrs: c,
				slots: s,
				emit: l
			}) : e(f, null)), y = t.props ? c : Or(c);
		}
	} catch (t) {
		pi.length = 0, ln(t, e, 1), v = J(di);
	}
	let b = v;
	if (y && g !== !1) {
		let e = Object.keys(y), { shapeFlag: t } = b;
		e.length && t & 7 && (a && e.some(o) && (y = kr(y, a)), b = Ti(b, y, !1, !0));
	}
	return n.dirs && (b = Ti(b, null, !1, !0), b.dirs = b.dirs ? b.dirs.concat(n.dirs) : n.dirs), n.transition && Wn(Bn(b.type) && Un(b) || b, n.transition), v = b, kn(_), v;
}
var Or = (e) => {
	let t;
	for (let n in e) (n === "class" || n === "style" || a(n)) && ((t ||= {})[n] = e[n]);
	return t;
}, kr = (e, t) => {
	let n = {};
	for (let r in e) (!o(r) || !(r.slice(9) in t)) && (n[r] = e[r]);
	return n;
};
function Ar(e, t, n) {
	let { props: r, children: i, component: a } = e, { props: o, children: s, patchFlag: c } = t, l = a.emitsOptions;
	if (t.dirs || t.transition) return !0;
	if (n && c >= 0) {
		if (c & 1024) return !0;
		if (c & 16) return r ? jr(r, o, l) : !!o;
		if (c & 8) {
			let e = t.dynamicProps;
			for (let t = 0; t < e.length; t++) {
				let n = e[t];
				if (Mr(o, r, n) && !Er(l, n)) return !0;
			}
		}
	} else return (i || s) && (!s || !s.$stable) ? !0 : r === o ? !1 : r ? !o || jr(r, o, l) : !!o;
	return !1;
}
function jr(e, t, n) {
	let r = Object.keys(t);
	if (r.length !== Object.keys(e).length) return !0;
	for (let i = 0; i < r.length; i++) {
		let a = r[i];
		if (Mr(t, e, a) && !Er(n, a)) return !0;
	}
	return !1;
}
function Mr(e, t, n) {
	let r = e[n], i = t[n];
	return n === "style" && y(r) && y(i) ? !_e(r, i) : r !== i;
}
function Nr({ vnode: e, parent: t, suspense: n }, r) {
	for (; t;) {
		let n = t.subTree;
		if (n.suspense && n.suspense.activeBranch === e && (n.suspense.vnode.el = n.el = r, e = n), n === e) (e = t.vnode).el = r, t = t.parent;
		else break;
	}
	n && n.activeBranch === e && (n.vnode.el = r);
}
var Pr = {}, Fr = () => Object.create(Pr), Ir = (e) => Object.getPrototypeOf(e) === Pr;
function Lr(e, t, n, r = !1) {
	let i = {}, a = Fr();
	e.propsDefaults = /* @__PURE__ */ Object.create(null), zr(e, t, i, a);
	for (let t in e.propsOptions[0]) t in i || (i[t] = void 0);
	e.props = n ? r ? i : /* @__PURE__ */ Pt(i) : e.type.props ? i : a, e.attrs = a;
}
function Rr(e, t, n, r) {
	let { props: i, attrs: a, vnode: { patchFlag: o } } = e, s = /* @__PURE__ */ R(i), [c] = e.propsOptions, l = !1;
	if ((r || o > 0) && !(o & 16)) {
		if (o & 8) {
			let n = e.vnode.dynamicProps;
			for (let r = 0; r < n.length; r++) {
				let o = n[r];
				if (Er(e.emitsOptions, o)) continue;
				let d = t[o];
				if (c) {
					if (u(a, o)) d !== a[o] && (a[o] = d, l = !0);
					else {
						let t = k(o);
						i[t] = Br(c, s, t, d, e, !1);
					}
				} else d !== a[o] && (a[o] = d, l = !0);
			}
		}
	} else {
		zr(e, t, i, a) && (l = !0);
		let r;
		for (let a in s) (!t || !u(t, a) && ((r = A(a)) === a || !u(t, r))) && (c ? n && (n[a] !== void 0 || n[r] !== void 0) && (i[a] = Br(c, s, a, void 0, e, !0)) : delete i[a]);
		if (a !== s) for (let e in a) (!t || !u(t, e)) && (delete a[e], l = !0);
	}
	l && $e(e.attrs, "set", "");
}
function zr(e, n, r, i) {
	let [a, o] = e.propsOptions, s = !1, c;
	if (n) for (let t in n) {
		if (E(t)) continue;
		let l = n[t], d;
		a && u(a, d = k(t)) ? !o || !o.includes(d) ? r[d] = l : (c ||= {})[d] = l : Er(e.emitsOptions, t) || (!(t in i) || l !== i[t]) && (i[t] = l, s = !0);
	}
	if (o) {
		let n = /* @__PURE__ */ R(r), i = c || t;
		for (let t = 0; t < o.length; t++) {
			let s = o[t];
			r[s] = Br(a, n, s, i[s], e, !u(i, s));
		}
	}
	return s;
}
function Br(e, t, n, r, i, a) {
	let o = e[n];
	if (o != null) {
		let e = u(o, "default");
		if (e && r === void 0) {
			let e = o.default;
			if (o.type !== Function && !o.skipFactory && g(e)) {
				let { propsDefaults: a } = i;
				if (n in a) r = a[n];
				else {
					let o = Ri(i);
					r = a[n] = e.call(null, t), o();
				}
			} else r = e;
			i.ce && i.ce._setProp(n, r);
		}
		o[0] && (a && !e ? r = !1 : o[1] && (r === "" || r === A(n)) && (r = !0));
	}
	return r;
}
function Vr(e, r, i = !1) {
	let a = r.propsCache, o = a.get(e);
	if (o) return o;
	let c = e.props, l = {}, f = [];
	if (!c) return y(e) && a.set(e, n), n;
	if (d(c)) for (let e = 0; e < c.length; e++) {
		let n = k(c[e]);
		Hr(n) && (l[n] = t);
	}
	else if (c) for (let e in c) {
		let t = k(e);
		if (Hr(t)) {
			let n = c[e], r = l[t] = d(n) || g(n) ? { type: n } : s({}, n), i = r.type, a = !1, o = !0;
			if (d(i)) for (let e = 0; e < i.length; ++e) {
				let t = i[e], n = g(t) && t.name;
				if (n === "Boolean") {
					a = !0;
					break;
				}
				n === "String" && (o = !1);
			}
			else a = g(i) && i.name === "Boolean";
			r[0] = a, r[1] = o, (a || u(r, "default")) && f.push(t);
		}
	}
	let p = [l, f];
	return y(e) && a.set(e, p), p;
}
function Hr(e) {
	return e[0] !== "$" && !E(e);
}
var Ur = (e) => e === "_" || e === "_ctx" || e === "$stable", Wr = (e) => d(e) ? e.map(Ei) : [Ei(e)], Gr = (e, t, n) => {
	if (t._n) return t;
	let r = An((...e) => Wr(t(...e)), n);
	return r._c = !1, r;
}, Kr = (e, t, n) => {
	let r = e._ctx;
	for (let n in e) {
		if (Ur(n)) continue;
		let i = e[n];
		if (g(i)) t[n] = Gr(n, i, r);
		else if (i != null) {
			let e = Wr(i);
			t[n] = () => e;
		}
	}
}, qr = (e, t) => {
	let n = Wr(t);
	e.slots.default = () => n;
}, Jr = (e, t, n) => {
	for (let r in t) (n || !Ur(r)) && (e[r] = t[r]);
}, Yr = (e, t, n) => {
	let r = e.slots = Fr();
	if (e.vnode.shapeFlag & 32) {
		let e = t._;
		e ? (Jr(r, t, n), n && M(r, "_", e, !0)) : Kr(t, r);
	} else t && qr(e, t);
}, Xr = (e, n, r) => {
	let { vnode: i, slots: a } = e, o = !0, s = t;
	if (i.shapeFlag & 32) {
		let e = n._;
		e ? r && e === 1 ? o = !1 : Jr(a, n, r) : (o = !n.$stable, Kr(n, a)), s = n;
	} else n && (qr(e, n), s = { default: 1 });
	if (o) for (let e in a) !Ur(e) && s[e] == null && delete a[e];
}, Zr = li;
function Qr(e) {
	return $r(e);
}
function $r(e, i) {
	let a = oe();
	a.__VUE__ = !0;
	let { insert: o, remove: s, patchProp: c, createElement: l, createText: u, createComment: d, setText: f, setElementText: p, parentNode: m, nextSibling: h, setScopeId: g = r, insertStaticContent: _ } = e, v = (e, t, n, r = null, i = null, a = null, o = void 0, s = null, c = !!t.dynamicChildren) => {
		if (e === t) return;
		e && !bi(e, t) && (r = me(e), ue(e, i, a, !0), e = null), t.patchFlag === -2 && (c = !1, t.dynamicChildren = null);
		let { type: l, ref: u, shapeFlag: d } = t;
		switch (l) {
			case ui:
				y(e, t, n, r);
				break;
			case di:
				b(e, t, n, r);
				break;
			case fi:
				e ?? x(t, n, r, o);
				break;
			case U:
				te(e, t, n, r, i, a, o, s, c);
				break;
			default: d & 1 ? w(e, t, n, r, i, a, o, s, c) : d & 6 ? ne(e, t, n, r, i, a, o, s, c) : (d & 64 || d & 128) && l.process(e, t, n, r, i, a, o, s, c, _e);
		}
		u != null && i ? Xn(u, e && e.ref, a, t || e, !t) : u == null && e && e.ref != null && Xn(e.ref, null, a, e, !0);
	}, y = (e, t, n, r) => {
		if (e == null) o(t.el = u(t.children), n, r);
		else {
			let n = t.el = e.el;
			t.children !== e.children && f(n, t.children);
		}
	}, b = (e, t, n, r) => {
		e == null ? o(t.el = d(t.children || ""), n, r) : t.el = e.el;
	}, x = (e, t, n, r) => {
		[e.el, e.anchor] = _(e.children, t, n, r, e.el, e.anchor);
	}, S = ({ el: e, anchor: t }, n, r) => {
		let i;
		for (; e && e !== t;) i = h(e), o(e, n, r), e = i;
		o(t, n, r);
	}, C = ({ el: e, anchor: t }) => {
		let n;
		for (; e && e !== t;) n = h(e), s(e), e = n;
		s(t);
	}, w = (e, t, n, r, i, a, o, s, c) => {
		if (t.type === "svg" ? o = "svg" : t.type === "math" && (o = "mathml"), e == null) T(t, n, r, i, a, o, s, c);
		else {
			let n = e.el && e.el._isVueCE ? e.el : null;
			try {
				n && n._beginPatch(), k(e, t, i, a, o, s, c);
			} finally {
				n && n._endPatch();
			}
		}
	}, T = (e, t, n, r, i, a, s, u) => {
		let d, f, { props: m, shapeFlag: h, transition: g, dirs: _ } = e;
		if (d = e.el = l(e.type, a, m && m.is, m), h & 8 ? p(d, e.children) : h & 16 && O(e.children, d, null, r, i, ei(e, a), s, u), _ && Mn(e, null, r, "created"), D(d, e, e.scopeId, s, r), m) {
			for (let e in m) e !== "value" && !E(e) && c(d, e, null, m[e], a, r);
			"value" in m && c(d, "value", null, m.value, a), (f = m.onVnodeBeforeMount) && Ai(f, r, e);
		}
		_ && Mn(e, null, r, "beforeMount");
		let v = ni(i, g);
		v && g.beforeEnter(d), o(d, t, n), ((f = m && m.onVnodeMounted) || v || _) && Zr(() => {
			try {
				f && Ai(f, r, e), v && g.enter(d), _ && Mn(e, null, r, "mounted");
			} finally {}
		}, i);
	}, D = (e, t, n, r, i) => {
		if (n && g(e, n), r) for (let t = 0; t < r.length; t++) g(e, r[t]);
		if (i) {
			let n = i.subTree;
			if (t === n || ci(n.type) && (n.ssContent === t || n.ssFallback === t)) {
				let t = i.vnode;
				D(e, t, t.scopeId, t.slotScopeIds, i.parent);
			}
		}
	}, O = (e, t, n, r, i, a, o, s, c = 0) => {
		for (let l = c; l < e.length; l++) {
			let c = e[l] = s ? Di(e[l]) : Ei(e[l]);
			v(null, c, t, n, r, i, a, o, s);
		}
	}, k = (e, n, r, i, a, o, s) => {
		let l = n.el = e.el, { patchFlag: u, dynamicChildren: d, dirs: f } = n;
		u |= e.patchFlag & 16;
		let m = e.props || t, h = n.props || t, g;
		if (r && ti(r, !1), (g = h.onVnodeBeforeUpdate) && Ai(g, r, n, e), f && Mn(n, e, r, "beforeUpdate"), r && ti(r, !0), d && (!e.dynamicChildren || e.dynamicChildren.length !== d.length) && (u = 0, s = !1, d = null), (m.innerHTML && h.innerHTML == null || m.textContent && h.textContent == null) && p(l, ""), d ? ee(e.dynamicChildren, d, l, r, i, ei(n, a), o) : s || ae(e, n, l, null, r, i, ei(n, a), o, !1), u > 0) {
			if (u & 16) A(l, m, h, r, a);
			else if (u & 2 && m.class !== h.class && c(l, "class", null, h.class, a), u & 4 && c(l, "style", m.style, h.style, a), u & 8) {
				let e = n.dynamicProps;
				for (let t = 0; t < e.length; t++) {
					let n = e[t], i = m[n], o = h[n];
					(o !== i || n === "value") && c(l, n, i, o, a, r);
				}
			}
			u & 1 && e.children !== n.children && p(l, n.children);
		} else !s && d == null && A(l, m, h, r, a);
		((g = h.onVnodeUpdated) || f) && Zr(() => {
			g && Ai(g, r, n, e), f && Mn(n, e, r, "updated");
		}, i);
	}, ee = (e, t, n, r, i, a, o) => {
		for (let s = 0; s < t.length; s++) {
			let c = e[s], l = t[s], u = c.el && (c.type === U || !bi(c, l) || c.shapeFlag & 198) ? m(c.el) : n;
			v(c, l, u, null, r, i, a, o, !0);
		}
	}, A = (e, n, r, i, a) => {
		if (n !== r) {
			if (n !== t) for (let t in n) !E(t) && !(t in r) && c(e, t, n[t], null, a, i);
			for (let t in r) {
				if (E(t)) continue;
				let o = r[t], s = n[t];
				o !== s && t !== "value" && c(e, t, s, o, a, i);
			}
			"value" in r && c(e, "value", n.value, r.value, a);
		}
	}, te = (e, t, n, r, i, a, s, c, l) => {
		let d = t.el = e ? e.el : u(""), f = t.anchor = e ? e.anchor : u(""), { patchFlag: p, dynamicChildren: m, slotScopeIds: h } = t;
		h && (c = c ? c.concat(h) : h), e == null ? (o(d, n, r), o(f, n, r), O(t.children || [], n, f, i, a, s, c, l)) : p > 0 && p & 64 && m && e.dynamicChildren && e.dynamicChildren.length === m.length ? (ee(e.dynamicChildren, m, n, i, a, s, c), (t.key != null || i && t === i.subTree) && ri(e, t, !0)) : ae(e, t, n, f, i, a, s, c, l);
	}, ne = (e, t, n, r, i, a, o, s, c) => {
		t.slotScopeIds = s, e == null ? t.shapeFlag & 512 ? i.ctx.activate(t, n, r, o, c) : j(t, n, r, i, a, o, c) : M(e, t, c);
	}, j = (e, t, n, r, i, a, o) => {
		let s = e.component = Ni(e, r, i);
		if ($n(e) && (s.ctx.renderer = _e), Hi(s, !1, o), s.asyncDep) {
			if (i && i.registerDep(s, N, o), !e.el) {
				let r = s.subTree = J(di);
				b(null, r, t, n), e.placeholder = r.el;
			}
		} else N(s, e, t, n, i, a, o);
	}, M = (e, t, n) => {
		let r = t.component = e.component;
		if (Ar(e, t, n)) {
			if (r.asyncDep && !r.asyncResolved) {
				ie(r, t, n);
				return;
			}
			r.next = t, r.update();
		} else t.el = e.el, r.vnode = t;
	}, N = (e, t, n, r, i, a, o) => {
		let s = () => {
			if (e.isMounted) {
				let { next: t, bu: n, u: r, parent: s, vnode: c } = e;
				{
					let n = ai(e);
					if (n) {
						t && (t.el = c.el, ie(e, t, o)), n.asyncDep.then(() => {
							Zr(() => {
								e.isUnmounted || l();
							}, i);
						});
						return;
					}
				}
				let u = t, d;
				ti(e, !1), t ? (t.el = c.el, ie(e, t, o)) : t = c, n && re(n), (d = t.props && t.props.onVnodeBeforeUpdate) && Ai(d, s, t, c), ti(e, !0);
				let f = Dr(e), p = e.subTree;
				e.subTree = f, v(p, f, m(p.el), me(p), e, i, a), t.el = f.el, u === null && Nr(e, f.el), r && Zr(r, i), (d = t.props && t.props.onVnodeUpdated) && Zr(() => Ai(d, s, t, c), i);
			} else {
				let o, { el: s, props: c } = t, { bm: l, m: u, parent: d, root: f, type: p } = e, m = Qn(t);
				if (ti(e, !1), l && re(l), !m && (o = c && c.onVnodeBeforeMount) && Ai(o, d, t), ti(e, !0), s && ye) {
					let t = () => {
						e.subTree = Dr(e), ye(s, e.subTree, e, i, null);
					};
					m && p.__asyncHydrate ? p.__asyncHydrate(s, e, t) : t();
				} else {
					f.ce && f.ce._hasShadowRoot() && f.ce._injectChildStyle(p, e.parent ? e.parent.type : void 0);
					let o = e.subTree = Dr(e);
					v(null, o, n, r, e, i, a), t.el = o.el;
				}
				if (u && Zr(u, i), !m && (o = c && c.onVnodeMounted)) {
					let e = t;
					Zr(() => Ai(o, d, e), i);
				}
				(t.shapeFlag & 256 || d && Qn(d.vnode) && d.vnode.shapeFlag & 256) && e.a && Zr(e.a, i), e.isMounted = !0, t = n = r = null;
			}
		};
		e.scope.on();
		let c = e.effect = new Ee(s);
		e.scope.off();
		let l = e.update = c.run.bind(c), u = e.job = c.runIfDirty.bind(c);
		u.i = e, u.id = e.uid, c.scheduler = () => bn(u), ti(e, !0), l();
	}, ie = (e, t, n) => {
		t.component = e;
		let r = e.vnode.props;
		e.vnode = t, e.next = null, Rr(e, t.props, r, n), Xr(e, t.children, n), Ve(), Cn(e), He();
	}, ae = (e, t, n, r, i, a, o, s, c = !1) => {
		let l = e && e.children, u = e ? e.shapeFlag : 0, d = t.children, { patchFlag: f, shapeFlag: m } = t;
		if (f > 0) {
			if (f & 128) {
				ce(l, d, n, r, i, a, o, s, c);
				return;
			}
			if (f & 256) {
				se(l, d, n, r, i, a, o, s, c);
				return;
			}
		}
		m & 8 ? (u & 16 && pe(l, i, a), d !== l && p(n, d)) : u & 16 ? m & 16 ? ce(l, d, n, r, i, a, o, s, c) : pe(l, i, a, !0) : (u & 8 && p(n, ""), m & 16 && O(d, n, r, i, a, o, s, c));
	}, se = (e, t, r, i, a, o, s, c, l) => {
		e ||= n, t ||= n;
		let u = e.length, d = t.length, f = Math.min(u, d), p = 0;
		for (; p < f; p++) {
			let n = t[p] = l ? Di(t[p]) : Ei(t[p]);
			v(e[p], n, r, null, a, o, s, c, l);
		}
		u > d ? pe(e, a, o, !0, !1, f) : O(t, r, i, a, o, s, c, l, f);
	}, ce = (e, t, r, i, a, o, s, c, l) => {
		let u = 0, d = t.length, f = e.length - 1, p = d - 1;
		for (; u <= f && u <= p;) {
			let n = e[u], i = t[u] = l ? Di(t[u]) : Ei(t[u]);
			if (bi(n, i)) v(n, i, r, null, a, o, s, c, l);
			else break;
			u++;
		}
		for (; u <= f && u <= p;) {
			let n = e[f], i = t[p] = l ? Di(t[p]) : Ei(t[p]);
			if (bi(n, i)) v(n, i, r, null, a, o, s, c, l);
			else break;
			f--, p--;
		}
		if (u > f) {
			if (u <= p) {
				let e = p + 1, n = e < d ? t[e].el : i;
				for (; u <= p;) v(null, t[u] = l ? Di(t[u]) : Ei(t[u]), r, n, a, o, s, c, l), u++;
			}
		} else if (u > p) for (; u <= f;) ue(e[u], a, o, !0), u++;
		else {
			let m = u, h = u, g = /* @__PURE__ */ new Map();
			for (u = h; u <= p; u++) {
				let e = t[u] = l ? Di(t[u]) : Ei(t[u]);
				e.key != null && g.set(e.key, u);
			}
			let _, y = 0, b = p - h + 1, x = !1, S = 0, C = Array(b);
			for (u = 0; u < b; u++) C[u] = 0;
			for (u = m; u <= f; u++) {
				let n = e[u];
				if (y >= b) {
					ue(n, a, o, !0);
					continue;
				}
				let i;
				if (n.key != null) i = g.get(n.key);
				else for (_ = h; _ <= p; _++) if (C[_ - h] === 0 && bi(n, t[_])) {
					i = _;
					break;
				}
				i === void 0 ? ue(n, a, o, !0) : (C[i - h] = u + 1, i >= S ? S = i : x = !0, v(n, t[i], r, null, a, o, s, c, l), y++);
			}
			let w = x ? ii(C) : n;
			for (_ = w.length - 1, u = b - 1; u >= 0; u--) {
				let e = h + u, n = t[e], f = t[e + 1], p = e + 1 < d ? f.el || si(f) : i;
				C[u] === 0 ? v(null, n, r, p, a, o, s, c, l) : x && (_ < 0 || u !== w[_] ? le(n, r, p, 2) : _--);
			}
		}
	}, le = (e, t, n, r, i = null) => {
		let { el: a, type: c, transition: l, children: u, shapeFlag: d } = e;
		if (d & 6) {
			le(e.component.subTree, t, n, r);
			return;
		}
		if (d & 128) {
			e.suspense.move(t, n, r);
			return;
		}
		if (d & 64) {
			c.move(e, t, n, _e);
			return;
		}
		if (c === U) {
			o(a, t, n);
			for (let e = 0; e < u.length; e++) le(u[e], t, n, r);
			o(e.anchor, t, n);
			return;
		}
		if (c === fi) {
			S(e, t, n);
			return;
		}
		if (r !== 2 && d & 1 && l) {
			if (r === 0) l.persisted && !a[Vn] ? o(a, t, n) : (l.beforeEnter(a), o(a, t, n), Zr(() => l.enter(a), i));
			else {
				let { leave: r, delayLeave: i, afterLeave: c } = l, u = () => {
					e.ctx.isUnmounted ? s(a) : o(a, t, n);
				}, d = () => {
					let e = a._isLeaving || !!a[Vn];
					a._isLeaving && a[Vn](!0), l.persisted && !e ? u() : r(a, () => {
						u(), c && c();
					});
				};
				i ? i(a, u, d) : d();
			}
		} else o(a, t, n);
	}, ue = (e, t, n, r = !1, i = !1) => {
		let { type: a, props: o, ref: s, children: c, dynamicChildren: l, shapeFlag: u, patchFlag: d, dirs: f, cacheIndex: p, memo: m } = e;
		if (d === -2 && (i = !1), s != null && (Ve(), Xn(s, null, n, e, !0), He()), p != null && (t.renderCache[p] = void 0), u & 256) {
			t.ctx.deactivate(e);
			return;
		}
		let h = u & 1 && f, g = !Qn(e), _;
		if (g && (_ = o && o.onVnodeBeforeUnmount) && Ai(_, t, e), u & 6) fe(e.component, n, r);
		else {
			if (u & 128) {
				e.suspense.unmount(n, r);
				return;
			}
			h && Mn(e, null, t, "beforeUnmount"), u & 64 ? e.type.remove(e, t, n, _e, r) : l && !l.hasOnce && (a !== U || d > 0 && d & 64) ? pe(l, t, n, !1, !0) : (a === U && d & 384 || !i && u & 16) && pe(c, t, n), r && de(e);
		}
		let v = m != null && p == null;
		(g && (_ = o && o.onVnodeUnmounted) || h || v) && Zr(() => {
			_ && Ai(_, t, e), h && Mn(e, null, t, "unmounted"), v && (e.el = null);
		}, n);
	}, de = (e) => {
		let { type: t, el: n, anchor: r, transition: i } = e;
		if (t === U) {
			P(n, r);
			return;
		}
		if (t === fi) {
			C(e);
			return;
		}
		let a = () => {
			s(n), i && !i.persisted && i.afterLeave && i.afterLeave();
		};
		if (e.shapeFlag & 1 && i && !i.persisted) {
			let { leave: t, delayLeave: r } = i, o = () => t(n, a);
			r ? r(e.el, a, o) : o();
		} else a();
	}, P = (e, t) => {
		let n;
		for (; e !== t;) n = h(e), s(e), e = n;
		s(t);
	}, fe = (e, t, n) => {
		let { bum: r, scope: i, job: a, subTree: o, um: s, m: c, a: l } = e;
		oi(c), oi(l), r && re(r), i.stop(), a && (a.flags |= 8, ue(o, e, t, n)), s && Zr(s, t), Zr(() => {
			e.isUnmounted = !0;
		}, t);
	}, pe = (e, t, n, r = !1, i = !1, a = 0) => {
		for (let o = a; o < e.length; o++) ue(e[o], t, n, r, i);
	}, me = (e) => {
		if (e.shapeFlag & 6) return me(e.component.subTree);
		if (e.shapeFlag & 128) return e.suspense.next();
		let t = h(e.anchor || e.el), n = t && t[zn];
		return n ? h(n) : t;
	}, he = !1, ge = (e, t, n) => {
		let r;
		e == null ? t._vnode && (ue(t._vnode, null, null, !0), r = t._vnode.component) : v(t._vnode || null, e, t, null, null, null, n), t._vnode = e, he ||= (he = !0, Cn(r), wn(), !1);
	}, _e = {
		p: v,
		um: ue,
		m: le,
		r: de,
		mt: j,
		mc: O,
		pc: ae,
		pbc: ee,
		n: me,
		o: e
	}, ve, ye;
	return i && ([ve, ye] = i(_e)), {
		render: ge,
		hydrate: ve,
		createApp: br(ge, ve)
	};
}
function ei({ type: e, props: t }, n) {
	return n === "svg" && e === "foreignObject" || n === "mathml" && e === "annotation-xml" && t && t.encoding && t.encoding.includes("html") ? void 0 : n;
}
function ti({ effect: e, job: t }, n) {
	n ? (e.flags |= 32, t.flags |= 4) : (e.flags &= -33, t.flags &= -5);
}
function ni(e, t) {
	return (!e || e && !e.pendingBranch) && t && !t.persisted;
}
function ri(e, t, n = !1) {
	let r = e.children, i = t.children;
	if (d(r) && d(i)) for (let e = 0; e < r.length; e++) {
		let t = r[e], a = i[e];
		a.shapeFlag & 1 && !a.dynamicChildren && ((a.patchFlag <= 0 || a.patchFlag === 32) && (a = i[e] = Di(i[e]), a.el = t.el), !n && a.patchFlag !== -2 && ri(t, a)), a.type === ui && (a.patchFlag === -1 && (a = i[e] = Di(a)), a.el = t.el), a.type === di && !a.el && (a.el = t.el);
	}
}
function ii(e) {
	let t = e.slice(), n = [0], r, i, a, o, s, c = e.length;
	for (r = 0; r < c; r++) {
		let c = e[r];
		if (c !== 0) {
			if (i = n[n.length - 1], e[i] < c) {
				t[r] = i, n.push(r);
				continue;
			}
			for (a = 0, o = n.length - 1; a < o;) s = a + o >> 1, e[n[s]] < c ? a = s + 1 : o = s;
			c < e[n[a]] && (a > 0 && (t[r] = n[a - 1]), n[a] = r);
		}
	}
	for (a = n.length, o = n[a - 1]; a-- > 0;) n[a] = o, o = t[o];
	return n;
}
function ai(e) {
	let t = e.subTree.component;
	if (t) return t.asyncDep && !t.asyncResolved ? t : ai(t);
}
function oi(e) {
	if (e) for (let t = 0; t < e.length; t++) e[t].flags |= 8;
}
function si(e) {
	if (e.placeholder) return e.placeholder;
	let t = e.component;
	return t ? si(t.subTree) : null;
}
var ci = (e) => e.__isSuspense;
function li(e, t) {
	t && t.pendingBranch ? d(e) ? t.effects.push(...e) : t.effects.push(e) : Sn(e);
}
var U = /* @__PURE__ */ Symbol.for("v-fgt"), ui = /* @__PURE__ */ Symbol.for("v-txt"), di = /* @__PURE__ */ Symbol.for("v-cmt"), fi = /* @__PURE__ */ Symbol.for("v-stc"), pi = [], mi = null;
function W(e = !1) {
	pi.push(mi = e ? null : []);
}
function hi() {
	pi.pop(), mi = pi[pi.length - 1] || null;
}
var gi = 1;
function _i(e, t = !1) {
	gi += e, e < 0 && mi && t && (mi.hasOnce = !0);
}
function vi(e) {
	return e.dynamicChildren = gi > 0 ? mi || n : null, hi(), gi > 0 && mi && mi.push(e), e;
}
function G(e, t, n, r, i, a) {
	return vi(q(e, t, n, r, i, a, !0));
}
function K(e, t, n, r, i) {
	return vi(J(e, t, n, r, i, !0));
}
function yi(e) {
	return e ? e.__v_isVNode === !0 : !1;
}
function bi(e, t) {
	return e.type === t.type && e.key === t.key;
}
var xi = ({ key: e }) => e ?? null, Si = ({ ref: e, ref_key: t, ref_for: n }) => (typeof e == "number" && (e = "" + e), e == null ? null : _(e) || /* @__PURE__ */ Wt(e) || g(e) ? {
	i: Dn,
	r: e,
	k: t,
	f: !!n
} : e);
function q(e, t = null, n = null, r = 0, i = null, a = e === U ? 0 : 1, o = !1, s = !1) {
	let c = {
		__v_isVNode: !0,
		__v_skip: !0,
		type: e,
		props: t,
		key: t && xi(t),
		ref: t && Si(t),
		scopeId: On,
		slotScopeIds: null,
		children: n,
		component: null,
		suspense: null,
		ssContent: null,
		ssFallback: null,
		dirs: null,
		transition: null,
		el: null,
		anchor: null,
		target: null,
		targetStart: null,
		targetAnchor: null,
		staticCount: 0,
		shapeFlag: a,
		patchFlag: r,
		dynamicProps: i,
		dynamicChildren: null,
		appContext: null,
		ctx: Dn
	};
	return s ? (Oi(c, n), a & 128 && e.normalize(c)) : n && (c.shapeFlag |= _(n) ? 8 : 16), gi > 0 && !o && mi && (c.patchFlag > 0 || a & 6) && c.patchFlag !== 32 && mi.push(c), c;
}
var J = Ci;
function Ci(e, t = null, n = null, r = 0, i = null, a = !1) {
	if ((!e || e === lr) && (e = di), yi(e)) {
		let r = Ti(e, t, !0);
		return n && Oi(r, n), gi > 0 && !a && mi && (r.shapeFlag & 6 ? mi[mi.indexOf(e)] = r : mi.push(r)), r.patchFlag = -2, r;
	}
	if (Xi(e) && (e = e.__vccOpts), t) {
		t = wi(t);
		let { class: e, style: n } = t;
		e && !_(e) && (t.class = P(e)), y(n) && (/* @__PURE__ */ Bt(n) && !d(n) && (n = s({}, n)), t.style = se(n));
	}
	let o = _(e) ? 1 : ci(e) ? 128 : Bn(e) ? 64 : y(e) ? 4 : g(e) ? 2 : 0;
	return q(e, t, n, r, i, o, a, !0);
}
function wi(e) {
	return e ? /* @__PURE__ */ Bt(e) || Ir(e) ? s({}, e) : e : null;
}
function Ti(e, t, n = !1, r = !1) {
	let { props: i, ref: a, patchFlag: o, children: s, transition: c } = e, l = t ? ki(i || {}, t) : i, u = {
		__v_isVNode: !0,
		__v_skip: !0,
		type: e.type,
		props: l,
		key: l && xi(l),
		ref: t && t.ref ? n && a ? d(a) ? a.concat(Si(t)) : [a, Si(t)] : Si(t) : a,
		scopeId: e.scopeId,
		slotScopeIds: e.slotScopeIds,
		children: s,
		target: e.target,
		targetStart: e.targetStart,
		targetAnchor: e.targetAnchor,
		staticCount: e.staticCount,
		shapeFlag: e.shapeFlag,
		patchFlag: t && e.type !== U ? o === -1 ? 16 : o | 16 : o,
		dynamicProps: e.dynamicProps,
		dynamicChildren: e.dynamicChildren,
		appContext: e.appContext,
		dirs: e.dirs,
		transition: c,
		component: e.component,
		suspense: e.suspense,
		ssContent: e.ssContent && Ti(e.ssContent),
		ssFallback: e.ssFallback && Ti(e.ssFallback),
		placeholder: e.placeholder,
		el: e.el,
		anchor: e.anchor,
		ctx: e.ctx,
		ce: e.ce
	};
	return c && r && Wn(u, c.clone(u)), u;
}
function Y(e = " ", t = 0) {
	return J(ui, null, e, t);
}
function X(e = "", t = !1) {
	return t ? (W(), K(di, null, e)) : J(di, null, e);
}
function Ei(e) {
	return e == null || typeof e == "boolean" ? J(di) : d(e) ? J(U, null, e.slice()) : yi(e) ? Di(e) : J(ui, null, String(e));
}
function Di(e) {
	return e.el === null && e.patchFlag !== -1 || e.memo ? e : Ti(e);
}
function Oi(e, t) {
	let n = 0, { shapeFlag: r } = e;
	if (t == null) t = null;
	else if (d(t)) n = 16;
	else if (typeof t == "object") {
		if (r & 65) {
			let n = t.default;
			n && (n._c && (n._d = !1), Oi(e, n()), n._c && (n._d = !0));
			return;
		}
		{
			n = 32;
			let r = t._;
			!r && !Ir(t) ? t._ctx = Dn : r === 3 && Dn && (Dn.slots._ === 1 ? t._ = 1 : (t._ = 2, e.patchFlag |= 1024));
		}
	} else if (g(t)) {
		if (r & 65) {
			Oi(e, { default: t });
			return;
		}
		t = {
			default: t,
			_ctx: Dn
		}, n = 32;
	} else t = String(t), r & 64 ? (n = 16, t = [Y(t)]) : n = 8;
	e.children = t, e.shapeFlag |= n;
}
function ki(...e) {
	let t = {};
	for (let n = 0; n < e.length; n++) {
		let r = e[n];
		for (let e in r) if (e === "class") t.class !== r.class && (t.class = P([t.class, r.class]));
		else if (e === "style") t.style = se([t.style, r.style]);
		else if (a(e)) {
			let n = t[e], i = r[e];
			i && n !== i && !(d(n) && n.includes(i)) ? t[e] = n ? [].concat(n, i) : i : i == null && n == null && !o(e) && (t[e] = i);
		} else e !== "" && (t[e] = r[e]);
	}
	return t;
}
function Ai(e, t, n, r = null) {
	cn(e, t, 7, [n, r]);
}
var ji = vr(), Mi = 0;
function Ni(e, n, r) {
	let i = e.type, a = (n ? n.appContext : e.appContext) || ji, o = {
		uid: Mi++,
		vnode: e,
		type: i,
		parent: n,
		appContext: a,
		root: null,
		next: null,
		subTree: null,
		effect: null,
		update: null,
		job: null,
		scope: new Se(!0),
		render: null,
		proxy: null,
		exposed: null,
		exposeProxy: null,
		withProxy: null,
		provides: n ? n.provides : Object.create(a.provides),
		ids: n ? n.ids : [
			"",
			0,
			0
		],
		accessCache: null,
		renderCache: [],
		components: null,
		directives: null,
		propsOptions: Vr(i, a),
		emitsOptions: Tr(i, a),
		emit: null,
		emitted: null,
		propsDefaults: t,
		inheritAttrs: i.inheritAttrs,
		ctx: t,
		data: t,
		props: t,
		attrs: t,
		slots: t,
		refs: t,
		setupState: t,
		setupContext: null,
		suspense: r,
		suspenseId: r ? r.pendingId : 0,
		asyncDep: null,
		asyncResolved: !1,
		isMounted: !1,
		isUnmounted: !1,
		isDeactivated: !1,
		bc: null,
		c: null,
		bm: null,
		m: null,
		bu: null,
		u: null,
		um: null,
		bum: null,
		da: null,
		a: null,
		rtg: null,
		rtc: null,
		ec: null,
		sp: null
	};
	return o.ctx = { _: o }, o.root = n ? n.root : o, o.emit = wr.bind(null, o), e.ce && e.ce(o), o;
}
var Pi = null, Fi = () => Pi || Dn, Ii, Li;
{
	let e = oe(), t = (t, n) => {
		let r;
		return (r = e[t]) || (r = e[t] = []), r.push(n), (e) => {
			r.length > 1 ? r.forEach((t) => t(e)) : r[0](e);
		};
	};
	Ii = t("__VUE_INSTANCE_SETTERS__", (e) => Pi = e), Li = t("__VUE_SSR_SETTERS__", (e) => Vi = e);
}
var Ri = (e) => {
	let t = Pi;
	return Ii(e), e.scope.on(), () => {
		e.scope.off(), Ii(t);
	};
}, zi = () => {
	Pi && Pi.scope.off(), Ii(null);
};
function Bi(e) {
	return e.vnode.shapeFlag & 4;
}
var Vi = !1;
function Hi(e, t = !1, n = !1) {
	t && Li(t);
	let { props: r, children: i } = e.vnode, a = Bi(e);
	Lr(e, r, a, t), Yr(e, i, n || t);
	let o = a ? Ui(e, t) : void 0;
	return t && Li(!1), o;
}
function Ui(e, t) {
	let n = e.type;
	e.accessCache = /* @__PURE__ */ Object.create(null), e.proxy = new Proxy(e.ctx, hr);
	let { setup: r } = n;
	if (r) {
		Ve();
		let n = e.setupContext = r.length > 1 ? qi(e) : null, i = Ri(e), a = sn(r, e, 0, [e.props, n]), o = b(a);
		if (He(), i(), (o || e.sp) && !Qn(e) && qn(e), o) {
			if (a.then(zi, zi), t) return a.then((n) => {
				Li(!0);
				try {
					Wi(e, n, t);
				} finally {
					Li(!1);
				}
			}).catch((t) => {
				ln(t, e, 0);
			});
			e.asyncDep = a;
		} else Wi(e, a, t);
	} else Gi(e, t);
}
function Wi(e, t, n) {
	g(t) ? e.type.__ssrInlineRender ? e.ssrRender = t : e.render = t : y(t) && (e.setupState = Yt(t)), Gi(e, n);
}
function Gi(e, t, n) {
	let i = e.type;
	e.render ||= i.render || r;
}
var Ki = { get(e, t) {
	return Qe(e, "get", ""), e[t];
} };
function qi(e) {
	return {
		attrs: new Proxy(e.attrs, Ki),
		slots: e.slots,
		emit: e.emit,
		expose: (t) => {
			e.exposed = t || {};
		}
	};
}
function Ji(e) {
	return e.exposed ? e.exposeProxy ||= new Proxy(Yt(Vt(e.exposed)), {
		get(t, n) {
			if (n in t) return t[n];
			if (n in pr) return pr[n](e);
		},
		has(e, t) {
			return t in e || t in pr;
		}
	}) : e.proxy;
}
function Yi(e, t = !0) {
	return g(e) ? e.displayName || e.name : e.name || t && e.__name;
}
function Xi(e) {
	return g(e) && "__vccOpts" in e;
}
var Z = (e, t) => /* @__PURE__ */ $t(e, t, Vi), Zi = "3.5.42", Qi = void 0, $i = typeof window < "u" && window.trustedTypes;
if ($i) try {
	Qi = /* @__PURE__ */ $i.createPolicy("vue", { createHTML: (e) => e });
} catch {}
var ea = Qi ? (e) => Qi.createHTML(e) : (e) => e, ta = "http://www.w3.org/2000/svg", na = "http://www.w3.org/1998/Math/MathML", ra = typeof document < "u" ? document : null, ia = ra && /* @__PURE__ */ ra.createElement("template"), aa = {
	insert: (e, t, n) => {
		t.insertBefore(e, n || null);
	},
	remove: (e) => {
		let t = e.parentNode;
		t && t.removeChild(e);
	},
	createElement: (e, t, n, r) => {
		let i = t === "svg" ? ra.createElementNS(ta, e) : t === "mathml" ? ra.createElementNS(na, e) : n ? ra.createElement(e, { is: n }) : ra.createElement(e);
		return e === "select" && r && r.multiple != null && i.setAttribute("multiple", r.multiple), i;
	},
	createText: (e) => ra.createTextNode(e),
	createComment: (e) => ra.createComment(e),
	setText: (e, t) => {
		e.nodeValue = t;
	},
	setElementText: (e, t) => {
		e.textContent = t;
	},
	parentNode: (e) => e.parentNode,
	nextSibling: (e) => e.nextSibling,
	querySelector: (e) => ra.querySelector(e),
	setScopeId(e, t) {
		e.setAttribute(t, "");
	},
	insertStaticContent(e, t, n, r, i, a) {
		let o = n ? n.previousSibling : t.lastChild;
		if (i && (i === a || i.nextSibling)) for (; t.insertBefore(i.cloneNode(!0), n), i !== a && (i = i.nextSibling););
		else {
			ia.innerHTML = ea(r === "svg" ? `<svg>${e}</svg>` : r === "mathml" ? `<math>${e}</math>` : e);
			let i = ia.content;
			if (r === "svg" || r === "mathml") {
				let e = i.firstChild;
				for (; e.firstChild;) i.appendChild(e.firstChild);
				i.removeChild(e);
			}
			t.insertBefore(i, n);
		}
		return [o ? o.nextSibling : t.firstChild, n ? n.previousSibling : t.lastChild];
	}
}, oa = /* @__PURE__ */ Symbol("_vtc");
function sa(e, t, n) {
	let r = e[oa];
	r && (t = (t ? [t, ...r] : [...r]).join(" ")), t == null ? e.removeAttribute("class") : n ? e.setAttribute("class", t) : e.className = t;
}
var ca = /* @__PURE__ */ Symbol("_vod"), la = /* @__PURE__ */ Symbol("_vsh"), ua = {
	name: "show",
	beforeMount(e, { value: t }, { transition: n }) {
		e[ca] = e.style.display === "none" ? "" : e.style.display, n && t ? n.beforeEnter(e) : da(e, t);
	},
	mounted(e, { value: t }, { transition: n }) {
		n && t && n.enter(e);
	},
	updated(e, { value: t, oldValue: n }, { transition: r }) {
		!t != !n && (r ? t ? (r.beforeEnter(e), da(e, !0), r.enter(e)) : r.leave(e, () => {
			da(e, !1);
		}) : da(e, t));
	},
	beforeUnmount(e, { value: t }) {
		da(e, t);
	}
};
function da(e, t) {
	e.style.display = t ? e[ca] : "none", e[la] = !t;
}
var fa = /* @__PURE__ */ Symbol(""), pa = /(?:^|;)\s*display\s*:/;
function ma(e, t, n) {
	let r = e.style, i = _(n), a = !1;
	if (n && !i) {
		if (t) {
			if (_(t)) for (let e of t.split(";")) {
				let t = e.slice(0, e.indexOf(":")).trim();
				n[t] ?? ga(r, t, "");
			}
			else for (let e in t) n[e] ?? ga(r, e, "");
		}
		for (let i in n) {
			i === "display" && (a = !0);
			let o = n[i];
			o == null ? ga(r, i, "") : ba(e, i, !_(t) && t ? t[i] : void 0, o) || ga(r, i, o);
		}
	} else if (i) {
		if (t !== n) {
			let e = r[fa];
			e && (n += ";" + e), r.cssText = n, a = pa.test(n);
		}
	} else t && e.removeAttribute("style");
	ca in e && (e[ca] = a ? r.display : "", e[la] && (r.display = "none"));
}
var ha = /\s*!important$/;
function ga(e, t, n) {
	if (d(n)) n.forEach((n) => ga(e, t, n));
	else if (n ??= "", t.startsWith("--")) ha.test(n) ? e.setProperty(t, n.replace(ha, ""), "important") : e.setProperty(t, n);
	else {
		let r = ya(e, t);
		ha.test(n) ? e.setProperty(A(r), n.replace(ha, ""), "important") : e[r] = n;
	}
}
var _a = [
	"Webkit",
	"Moz",
	"ms"
], va = {};
function ya(e, t) {
	let n = va[t];
	if (n) return n;
	let r = k(t);
	if (r !== "filter" && r in e) return va[t] = r;
	r = te(r);
	for (let n = 0; n < _a.length; n++) {
		let i = _a[n] + r;
		if (i in e) return va[t] = i;
	}
	return t;
}
function ba(e, t, n, r) {
	return e.tagName === "TEXTAREA" && (t === "width" || t === "height") && _(r) && n === r;
}
var xa = "http://www.w3.org/1999/xlink";
function Sa(e, t, n, r, i, a = pe(t)) {
	r && t.startsWith("xlink:") ? n == null ? e.removeAttributeNS(xa, t.slice(6, t.length)) : e.setAttributeNS(xa, t, n) : n == null || a && !me(n) ? e.removeAttribute(t) : e.setAttribute(t, a ? "" : v(n) ? String(n) : n);
}
function Ca(e, t, n, r, i) {
	if (t === "innerHTML" || t === "textContent") {
		n != null && (e[t] = t === "innerHTML" ? ea(n) : n);
		return;
	}
	let a = e.tagName;
	if (t === "value" && a !== "PROGRESS" && !a.includes("-")) {
		let r = a === "OPTION" ? e.getAttribute("value") || "" : e.value, i = n == null ? e.type === "checkbox" ? "on" : "" : String(n);
		(r !== i || !("_value" in e)) && (e.value = i), n ?? e.removeAttribute(t), e._value = n;
		return;
	}
	let o = !1;
	if (n === "" || n == null) {
		let r = typeof e[t];
		r === "boolean" ? n = me(n) : n == null && r === "string" ? (n = "", o = !0) : r === "number" && (n = 0, o = !0);
	}
	try {
		e[t] = n;
	} catch {}
	o && e.removeAttribute(i || t);
}
function wa(e, t, n, r) {
	e.addEventListener(t, n, r);
}
function Ta(e, t, n, r) {
	e.removeEventListener(t, n, r);
}
var Ea = /* @__PURE__ */ Symbol("_vei");
function Da(e, t, n, r, i = null) {
	let a = e[Ea] || (e[Ea] = {}), o = a[t];
	if (r && o) o.value = r;
	else {
		let [n, s] = Aa(t);
		r ? wa(e, n, a[t] = Pa(r, i), s) : o && (Ta(e, n, o, s), a[t] = void 0);
	}
}
var Oa = /(Once|Passive|Capture)$/, ka = /^on:?(?:Once|Passive|Capture)$/;
function Aa(e) {
	let t, n;
	for (; (n = e.match(Oa)) && !ka.test(e);) t ||= {}, e = e.slice(0, e.length - n[1].length), t[n[1].toLowerCase()] = !0;
	return [e[2] === ":" ? e.slice(3) : A(e.slice(2)), t];
}
var ja = 0, Ma = /* @__PURE__ */ Promise.resolve(), Na = () => ja ||= (Ma.then(() => ja = 0), Date.now());
function Pa(e, t) {
	let n = (e) => {
		if (!e._vts) e._vts = Date.now();
		else if (e._vts <= n.attached) return;
		let r = n.value;
		if (d(r)) {
			let n = e.stopImmediatePropagation;
			e.stopImmediatePropagation = () => {
				n.call(e), e._stopped = !0;
			};
			let i = r.slice(), a = [e];
			for (let n = 0; n < i.length && !e._stopped; n++) {
				let e = i[n];
				e && cn(e, t, 5, a);
			}
		} else cn(r, t, 5, [e]);
	};
	return n.value = e, n.attached = Na(), n;
}
var Fa = (e) => e.charCodeAt(0) === 111 && e.charCodeAt(1) === 110 && e.charCodeAt(2) > 96 && e.charCodeAt(2) < 123, Ia = (e, t, n, r, i, s) => {
	let c = i === "svg";
	t === "class" ? sa(e, r, c) : t === "style" ? ma(e, n, r) : a(t) ? o(t) || Da(e, t, n, r, s) : (t[0] === "." ? (t = t.slice(1), 1) : t[0] === "^" ? (t = t.slice(1), 0) : La(e, t, r, c)) ? (Ca(e, t, r), !e.tagName.includes("-") && (t === "value" || t === "checked" || t === "selected") && Sa(e, t, r, c, s, t !== "value")) : e._isVueCE && (Ra(e, t) || e._def.__asyncLoader && (/[A-Z]/.test(t) || !_(r))) ? Ca(e, k(t), r, s, t) : (t === "true-value" ? e._trueValue = r : t === "false-value" && (e._falseValue = r), Sa(e, t, r, c));
};
function La(e, t, n, r) {
	if (r) return !!(t === "innerHTML" || t === "textContent" || t in e && Fa(t) && g(n));
	if (t === "spellcheck" || t === "draggable" || t === "translate" || t === "autocorrect" || t === "sandbox" && e.tagName === "IFRAME" || t === "form" || t === "list" && e.tagName === "INPUT" || t === "type" && e.tagName === "TEXTAREA") return !1;
	if (t === "width" || t === "height") {
		let t = e.tagName;
		if (t === "IMG" || t === "VIDEO" || t === "CANVAS" || t === "SOURCE") return !1;
	}
	return Fa(t) && _(n) ? !1 : t in e;
}
function Ra(e, t) {
	let n = e._def.props;
	if (!n) return !1;
	let r = k(t);
	return Array.isArray(n) ? n.some((e) => k(e) === r) : Object.keys(n).some((e) => k(e) === r);
}
var za = {};
// @__NO_SIDE_EFFECTS__
function Ba(e, t, n) {
	let r = /* @__PURE__ */ Gn(e, t);
	w(r) && (r = s({}, r, t));
	class i extends Ha {
		constructor(e) {
			super(r, e, n);
		}
	}
	return i.def = r, i;
}
var Va = typeof HTMLElement < "u" ? HTMLElement : class {}, Ha = class e extends Va {
	constructor(e, t = {}, n = lo) {
		super(), this._def = e, this._props = t, this._createApp = n, this._isVueCE = !0, this._instance = null, this._app = null, this._nonce = this._def.nonce, this._connected = !1, this._resolved = !1, this._patching = !1, this._dirty = !1, this._numberProps = null, this._styleChildren = /* @__PURE__ */ new WeakSet(), this._styleAnchors = /* @__PURE__ */ new WeakMap(), this._ob = null, this.shadowRoot && n !== lo ? this._root = this.shadowRoot : e.shadowRoot === !1 ? this._root = this : (this.attachShadow(s({}, e.shadowRootOptions, { mode: "open" })), this._root = this.shadowRoot);
	}
	connectedCallback() {
		if (!this.isConnected) return;
		!this.shadowRoot && !this._resolved && this._parseSlots(), this._connected = !0;
		let t = this;
		for (; t &&= t.assignedSlot || t.parentNode || t.host;) if (t instanceof e) {
			this._parent = t;
			break;
		}
		this._instance || (this._resolved ? this._mount(this._def) : t && t._pendingResolve ? this._pendingResolve = t._pendingResolve.then(() => {
			if (this._pendingResolve = void 0, this.isConnected) return this._resolveDef();
		}) : this._resolveDef());
	}
	_setParent(e = this._parent) {
		e && (this._instance.parent = e._instance, this._inheritParentContext(e));
	}
	_inheritParentContext(e = this._parent) {
		e && this._app && Object.setPrototypeOf(this._app._context.provides, e._instance.provides);
	}
	disconnectedCallback() {
		this._connected = !1, vn(() => {
			this._connected || (this._ob &&= (this._ob.disconnect(), null), this._app && this._app.unmount(), this._instance && (this._instance.ce = void 0), this._app = this._instance = null, this._teleportTargets &&= (this._teleportTargets.clear(), void 0));
		});
	}
	_processMutations(e) {
		for (let t of e) this._setAttr(t.attributeName);
	}
	_resolveDef() {
		if (this._pendingResolve) return this._pendingResolve;
		for (let e = 0; e < this.attributes.length; e++) this._setAttr(this.attributes[e].name);
		this._ob = new MutationObserver(this._processMutations.bind(this)), this._ob.observe(this, { attributes: !0 });
		let e = (e, t = !1) => {
			this._resolved = !0, this._pendingResolve = void 0;
			let { props: n, styles: r } = e, i;
			if (n && !d(n)) for (let e in n) {
				let t = n[e];
				(t === Number || t && t.type === Number) && (e in this._props && (this._props[e] = ie(this._props[e])), (i ||= /* @__PURE__ */ Object.create(null))[k(e)] = !0);
			}
			this._numberProps = i, this._resolveProps(e), this.shadowRoot && this._applyStyles(r), this._mount(e);
		}, t = this._def.__asyncLoader;
		if (t) return this._pendingResolve = t().then((t) => {
			t.configureApp = this._def.configureApp, e(this._def = t, !0);
		}), this._pendingResolve;
		e(this._def);
	}
	_mount(e) {
		this._app = this._createApp(e), this._inheritParentContext(), e.configureApp && e.configureApp(this._app), this._app._ceVNode = this._createVNode(), this._app.mount(this._root);
		let t = this._instance && this._instance.exposed;
		if (t) for (let e in t) u(this, e) || Object.defineProperty(this, e, { get: () => B(t[e]) });
	}
	_resolveProps(e) {
		let { props: t } = e, n = d(t) ? t : Object.keys(t || {});
		for (let e of Object.keys(this)) e[0] !== "_" && n.includes(e) && this._setProp(e, this[e]);
		for (let e of n.map(k)) Object.defineProperty(this, e, {
			get() {
				return this._getProp(e);
			},
			set(t) {
				this._setProp(e, t, !0, !this._patching);
			}
		});
	}
	_setAttr(e) {
		if (e.startsWith("data-v-")) return;
		let t = this.hasAttribute(e), n = t ? this.getAttribute(e) : za, r = k(e);
		t && this._numberProps && this._numberProps[r] && (n = ie(n)), this._setProp(r, n, !1, !0);
	}
	_getProp(e) {
		return this._props[e];
	}
	_setProp(e, t, n = !0, r = !1) {
		if (t !== this._props[e] && (this._dirty = !0, t === za ? delete this._props[e] : (this._props[e] = t, e === "key" && this._app && (this._app._ceVNode.key = t)), r && this._instance && this._update(), n)) {
			let n = this._ob;
			n && (this._processMutations(n.takeRecords()), n.disconnect()), t === !0 ? this.setAttribute(A(e), "") : typeof t == "string" || typeof t == "number" ? this.setAttribute(A(e), t + "") : t || this.removeAttribute(A(e)), n && n.observe(this, { attributes: !0 });
		}
	}
	_update() {
		let e = this._createVNode();
		this._app && (e.appContext = this._app._context), co(e, this._root);
	}
	_createVNode() {
		let e = {};
		this.shadowRoot || (e.onVnodeMounted = e.onVnodeUpdated = this._renderSlots.bind(this));
		let t = J(this._def, s(e, this._props));
		return this._instance || (t.ce = (e) => {
			this._instance = e, e.ce = this, e.isCE = !0;
			let t = (e, t) => {
				this.dispatchEvent(new CustomEvent(e, w(t[0]) ? s({ detail: t }, t[0]) : { detail: t }));
			};
			e.emit = (e, ...n) => {
				t(e, n), A(e) !== e && t(A(e), n);
			}, this._setParent();
		}), t;
	}
	_applyStyles(e, t, n) {
		if (!e) return;
		if (t) {
			if (t === this._def || this._styleChildren.has(t)) return;
			this._styleChildren.add(t);
		}
		let r = this._nonce, i = this.shadowRoot, a = n ? this._getStyleAnchor(n) || this._getStyleAnchor(this._def) : this._getRootStyleInsertionAnchor(i), o = null;
		for (let s = e.length - 1; s >= 0; s--) {
			let c = document.createElement("style");
			r && c.setAttribute("nonce", r), c.textContent = e[s], i.insertBefore(c, o || a), o = c, s === 0 && (n || this._styleAnchors.set(this._def, c), t && this._styleAnchors.set(t, c));
		}
	}
	_getStyleAnchor(e) {
		if (!e) return null;
		let t = this._styleAnchors.get(e);
		return t && t.parentNode === this.shadowRoot ? t : (t && this._styleAnchors.delete(e), null);
	}
	_getRootStyleInsertionAnchor(e) {
		for (let t = 0; t < e.childNodes.length; t++) {
			let n = e.childNodes[t];
			if (!(n instanceof HTMLStyleElement)) return n;
		}
		return null;
	}
	_parseSlots() {
		let e = this._slots = {}, t;
		for (; t = this.firstChild;) {
			let n = t.nodeType === 1 && t.getAttribute("slot") || "default";
			(e[n] || (e[n] = [])).push(t), this.removeChild(t);
		}
	}
	_renderSlots() {
		let e = this._getSlots(), t = this._instance.type.__scopeId;
		for (let n = 0; n < e.length; n++) {
			let r = e[n], i = r.getAttribute("name") || "default", a = this._slots[i], o = r.parentNode;
			if (a) for (let e of a) {
				if (t && e.nodeType === 1) {
					let n = t + "-s", r = document.createTreeWalker(e, 1);
					e.setAttribute(n, "");
					let i;
					for (; i = r.nextNode();) i.setAttribute(n, "");
				}
				o.insertBefore(e, r);
			}
			else for (; r.firstChild;) o.insertBefore(r.firstChild, r);
			o.removeChild(r);
		}
	}
	_getSlots() {
		let e = [this];
		this._teleportTargets && e.push(...this._teleportTargets);
		let t = /* @__PURE__ */ new Set();
		for (let n of e) {
			let e = n.querySelectorAll("slot");
			for (let n = 0; n < e.length; n++) t.add(e[n]);
		}
		return Array.from(t);
	}
	_injectChildStyle(e, t) {
		this._applyStyles(e.styles, e, t);
	}
	_beginPatch() {
		this._patching = !0, this._dirty = !1;
	}
	_endPatch() {
		this._patching = !1, this._dirty && this._instance && this._update();
	}
	_hasShadowRoot() {
		return this._def.shadowRoot !== !1;
	}
	_removeChildStyle(e) {}
};
function Ua(e) {
	let t = Fi();
	return t && t.ce || null;
}
var Wa = (e) => {
	let t = e.props["onUpdate:modelValue"] || !1;
	return d(t) ? (e) => re(t, e) : t;
};
function Ga(e) {
	e.target.composing = !0;
}
function Ka(e) {
	let t = e.target;
	t.composing && (t.composing = !1, t.dispatchEvent(new Event("input")));
}
var qa = /* @__PURE__ */ Symbol("_assign"), Ja = /* @__PURE__ */ Symbol("_initialValue");
function Ya(e, t, n) {
	return t && (e = e.trim()), n && (e = N(e)), e;
}
var Xa = {
	created(e, { modifiers: { lazy: t, trim: n, number: r } }, i) {
		e.parentNode && (e.type === "text" ? e[Ja] = e.defaultValue.replace(/[\r\n]/g, "") : e.type === "textarea" && (e[Ja] = e.defaultValue.replace(/\r\n?/g, "\n"))), e[qa] = Wa(i);
		let a = r || i.props && i.props.type === "number";
		wa(e, t ? "change" : "input", (t) => {
			t.target.composing || e[qa](Ya(e.value, n, a));
		}), (n || a) && wa(e, "change", () => {
			e.value = Ya(e.value, n, a);
		}), t || (wa(e, "compositionstart", Ga), wa(e, "compositionend", Ka), wa(e, "change", Ka));
	},
	mounted(e, { value: t, modifiers: { trim: n, number: r } }) {
		let i = t ?? "", a = e[Ja];
		delete e[Ja], a !== void 0 && (e.type === "text" || e.type === "textarea") && e.value !== a ? e[qa](Ya(e.value, n, r)) : e.value = i;
	},
	beforeUpdate(e, { value: t, oldValue: n, modifiers: { lazy: r, trim: i, number: a } }, o) {
		if (e[qa] = Wa(o), e.composing) return;
		let s = (a || e.type === "number") && !/^0\d/.test(e.value) ? N(e.value) : e.value, c = t ?? "";
		if (s === c) return;
		let l = e.getRootNode();
		(l instanceof Document || l instanceof ShadowRoot) && l.activeElement === e && e.type !== "range" && (r && t === n || i && e.value.trim() === c) || (e.value = c);
	}
}, Za = {
	created(e, { value: t }, n) {
		e.checked = _e(t, n.props.value), e[qa] = Wa(n), wa(e, "change", () => {
			e[qa](to(e));
		});
	},
	beforeUpdate(e, { value: t, oldValue: n }, r) {
		e[qa] = Wa(r), t !== n && (e.checked = _e(t, r.props.value));
	}
}, Qa = {
	deep: !0,
	created(e, { value: t, modifiers: { number: n } }, r) {
		e._modelValue = t, wa(e, "change", () => {
			let t = Array.prototype.filter.call(e.options, (e) => e.selected).map((e) => n ? N(to(e)) : to(e)), r = e.multiple, i = r ? p(e._modelValue) ? new Set(t) : t : t[0], a = e._pendingValue = [r, r ? d(i) ? t.slice() : t : i];
			try {
				e[qa](i);
			} finally {
				vn(() => {
					e._pendingValue === a && (e._pendingValue = void 0);
				});
			}
		}), e[qa] = Wa(r);
	},
	mounted(e, { value: t }) {
		eo(e, t);
	},
	beforeUpdate(e, { value: t }, n) {
		e._modelValue = t, e[qa] = Wa(n);
	},
	updated(e, { value: t }) {
		let n = e._pendingValue;
		e._pendingValue = void 0, (!n || n[0] !== e.multiple || !$a(t, n[1], n[0])) && eo(e, t);
	}
};
function $a(e, t, n) {
	if (!n || d(e)) return _e(e, t);
	if (p(e)) {
		if (e.size !== t.length) return !1;
		for (let n of t) if (!e.has(n)) return !1;
		return !0;
	}
	return !1;
}
function eo(e, t) {
	let n = e.multiple, r = d(t);
	if (!n || r || p(t)) {
		for (let i = 0, a = e.options.length; i < a; i++) {
			let a = e.options[i], o = to(a);
			if (n) {
				if (r) {
					let e = typeof o;
					a.selected = e === "string" || e === "number" ? t.some((e) => String(e) === String(o)) : ve(t, o) > -1;
				} else a.selected = t.has(o);
			} else if (_e(to(a), t)) {
				e.selectedIndex !== i && (e.selectedIndex = i);
				return;
			}
		}
		!n && e.selectedIndex !== -1 && (e.selectedIndex = -1);
	}
}
function to(e) {
	return "_value" in e ? e._value : e.value;
}
var no = [
	"ctrl",
	"shift",
	"alt",
	"meta"
], ro = {
	stop: (e) => e.stopPropagation(),
	prevent: (e) => e.preventDefault(),
	self: (e) => e.target !== e.currentTarget,
	ctrl: (e) => !e.ctrlKey,
	shift: (e) => !e.shiftKey,
	alt: (e) => !e.altKey,
	meta: (e) => !e.metaKey,
	left: (e) => "button" in e && e.button !== 0,
	middle: (e) => "button" in e && e.button !== 1,
	right: (e) => "button" in e && e.button !== 2,
	exact: (e, t) => no.some((n) => e[`${n}Key`] && !t.includes(n))
}, io = (e, t) => {
	if (!e) return e;
	let n = e._withMods ||= {}, r = t.join(".");
	return n[r] || (n[r] = ((n, ...r) => {
		for (let e = 0; e < t.length; e++) {
			let r = ro[t[e]];
			if (r && r(n, t)) return;
		}
		return e(n, ...r);
	}));
}, ao = /* @__PURE__ */ s({ patchProp: Ia }, aa), oo;
function so() {
	return oo ||= Qr(ao);
}
var co = ((...e) => {
	so().render(...e);
}), lo = ((...e) => {
	let t = so().createApp(...e), { mount: n } = t;
	return t.mount = (e) => {
		let r = fo(e);
		if (!r) return;
		let i = t._component;
		!g(i) && !i.render && !i.template && (i.template = r.innerHTML), r.nodeType === 1 && (r.textContent = "");
		let a = n(r, !1, uo(r));
		return r instanceof Element && (r.removeAttribute("v-cloak"), r.setAttribute("data-v-app", "")), a;
	}, t;
});
function uo(e) {
	if (e instanceof SVGElement) return "svg";
	if (typeof MathMLElement == "function" && e instanceof MathMLElement) return "mathml";
}
function fo(e) {
	return _(e) ? document.querySelector(e) : e;
}
//#endregion
//#region src/tabs.ts
var po = [
	{
		path: "allgemein",
		de: "Allgemeine Informationen",
		en: "General information"
	},
	{
		path: "stromtarif",
		de: "Stromtarif",
		en: "Electricity tariff"
	},
	{
		path: "tarifvergleich",
		de: "Tarifvergleich",
		en: "Tariff comparison"
	},
	{
		path: "netzdienliches-laden",
		de: "Netzdienliches Laden",
		en: "Grid-serving charging"
	},
	{
		path: "ersparnis",
		de: "Amortisation",
		en: "Amortization"
	}
];
function mo(e, t) {
	let n = e.split(/[?#]/, 1)[0].replace(/\/+$/, "");
	return (n.startsWith(`${t}/`) ? n.slice(t.length) : n === t ? "" : n).replace(/^\//, "") || po[0].path;
}
var ho = {
	de: {
		navigation: "Dashboard-Bereiche",
		menu: "Seitenleiste öffnen",
		introduction: "Gerätewerte, Ladeeinstellungen und Ersparnis Ihres SAX-Power-Speichers.",
		loading: "Home Assistant wird geladen …",
		missingEntry: "Diesem Dashboard ist noch kein SAX-Power-Gerät zugeordnet. Bitte laden Sie die Integration neu.",
		notFound: "Bereich nicht gefunden",
		notFoundDescription: "Dieser Dashboard-Bereich ist nicht verfügbar. Wählen Sie einen der oben angezeigten Bereiche.",
		returnToOverview: "Zur Übersicht"
	},
	en: {
		navigation: "Dashboard sections",
		menu: "Open sidebar",
		introduction: "Device values, charging settings and savings for your SAX Power battery.",
		loading: "Loading Home Assistant …",
		missingEntry: "No SAX Power device is assigned to this dashboard yet. Please reload the integration.",
		notFound: "Section not found",
		notFoundDescription: "This dashboard section is unavailable. Choose one of the sections above.",
		returnToOverview: "Back to overview"
	}
};
//#endregion
//#region src/savings.ts
function Q(e) {
	if (typeof e != "number" && typeof e != "string" || typeof e == "string" && !e.trim()) return null;
	let t = Number(e);
	return Number.isFinite(t) ? t : null;
}
function go(e) {
	return {
		comma_decimal: "en-US",
		decimal_comma: "de-DE",
		space_comma: "fr-FR"
	}[e?.locale?.number_format ?? ""] ?? e?.locale?.language ?? e?.language ?? "en";
}
function _o(e, t, n = 2) {
	let r = Q(e);
	return r === null ? null : new Intl.NumberFormat(go(t), {
		minimumFractionDigits: n,
		maximumFractionDigits: n,
		useGrouping: t?.locale?.number_format !== "none"
	}).format(r);
}
function vo(e, t, n = {
	dateStyle: "medium",
	timeStyle: "short"
}) {
	if (typeof e != "string" || !e) return null;
	let r = new Date(e);
	return Number.isFinite(r.getTime()) ? new Intl.DateTimeFormat(t?.locale?.language ?? t?.language ?? "en", {
		timeZone: t?.config?.time_zone,
		hour12: t?.locale?.time_format === "am_pm" || t?.locale?.time_format !== "twenty_four" && void 0,
		...n
	}).format(r) : null;
}
function yo(e, t) {
	let n = (e) => /^\d{4}-\d{2}-\d{2}$/.test(e) && Number(e.slice(0, 4)) > 0 && Number.isFinite(Date.parse(`${e}T00:00:00Z`)) && (/* @__PURE__ */ new Date(`${e}T00:00:00Z`)).toISOString().slice(0, 10) === e;
	return n(e) && n(t) && e <= t;
}
function bo(e) {
	let t = [
		"sun",
		"mon",
		"tue",
		"wed",
		"thu",
		"fri",
		"sat"
	], n = e?.locale?.first_weekday;
	if (n && n !== "language") {
		let e = n.slice(0, 3);
		if (t.includes(e)) return e;
	}
	if (n === "language") {
		let n = new Intl.Locale(e?.locale?.language ?? e?.language ?? "en"), r = n.getWeekInfo?.().firstDay ?? n.weekInfo?.firstDay;
		if (r !== void 0) return t[r % 7];
	}
	return "mon";
}
function xo(e, t, n) {
	let r = /* @__PURE__ */ Gt(null), i = /* @__PURE__ */ z(!1), a = /* @__PURE__ */ z(null), o, s = 0, c = !1;
	async function l() {
		let l = ++s, u = e(), d = t();
		if (r.value = null, a.value = null, i.value = !1, d && n()) {
			if (!u?.callWS || !u.connection?.connected) {
				a.value = "unavailable";
				return;
			}
			i.value = !0;
			try {
				let e = await u.callWS({
					type: "sax_power/dashboard/statistics",
					entry_id: d,
					first_weekday: bo(u),
					...o
				});
				!c && l === s && (r.value = e);
			} catch {
				!c && l === s && (a.value = "failed");
			} finally {
				!c && l === s && (i.value = !1);
			}
		}
	}
	function u(e, t) {
		if (!yo(e, t)) {
			a.value = "invalid";
			return;
		}
		o = {
			start_date: e,
			end_date: t
		}, l();
	}
	return V([
		() => e()?.connection,
		t,
		n,
		() => bo(e()),
		() => e()?.config?.time_zone,
		() => !!e()?.callWS
	], ([e, t], c, u) => {
		t !== c?.[1] && (o = void 0);
		let d = !1, f, p = 0, m = (e) => {
			try {
				Promise.resolve(e()).catch(() => {});
			} catch {}
		}, h = () => {
			++s, ++p, f && m(f), f = void 0, r.value = null, i.value = !1, a.value = n() ? "unavailable" : null;
		}, g = () => {
			if (d) return;
			let t = ++p;
			f && m(f), f = void 0, l(), e?.connected && n() && e.subscribeMessage(() => {
				!d && t === p && l();
			}, {
				type: "subscribe_events",
				event_type: "recorder_5min_statistics_generated"
			}, { resubscribe: !1 }).then((e) => {
				d || t !== p ? m(e) : f = e;
			}).catch(() => {});
		};
		e?.addEventListener("ready", g), e?.addEventListener("disconnected", h), e?.addEventListener("reconnect-error", h), g(), u(() => {
			d = !0, h(), e?.removeEventListener("ready", g), e?.removeEventListener("disconnected", h), e?.removeEventListener("reconnect-error", h);
		});
	}, { immediate: !0 }), we(() => {
		c = !0, ++s;
	}), {
		data: r,
		loading: i,
		error: a,
		refresh: l,
		select: u
	};
}
//#endregion
//#region src/ha.ts
var So = {
	de: {
		unavailable: "Nicht verfügbar",
		unknown: "Unbekannt",
		disconnected: "Keine Verbindung zu Home Assistant.",
		loadFailed: "Die SAX Power Entitäten konnten nicht geladen werden.",
		forbidden: "Diese Entität kann derzeit nicht bedient werden.",
		invalid: "Bitte einen gültigen Wert im erlaubten Bereich eingeben.",
		timedSocOrder: "Das Netzladeziel muss mindestens so hoch wie der Ladestart sein.",
		failed: "Die Änderung ist fehlgeschlagen. Bitte den aktuellen Zustand prüfen und erneut versuchen.",
		bridgePvRequired: "Öffne unter „Preise & Zeiten“ die Bearbeitung und ergänze die Solarprognose. Die bisherige Ladeweise bleibt erhalten.",
		bridgeTariffRequired: "Richte zuerst einen zeitvariablen Tarif mit gültigen Preisen ein. Die bisherige Ladeweise bleibt erhalten.",
		on: "Ein",
		off: "Aus"
	},
	en: {
		unavailable: "Unavailable",
		unknown: "Unknown",
		disconnected: "Disconnected from Home Assistant.",
		loadFailed: "The SAX Power entities could not be loaded.",
		forbidden: "This entity cannot be controlled at the moment.",
		invalid: "Please enter a valid value within the allowed range.",
		timedSocOrder: "The grid charge target must be at least as high as the start threshold.",
		failed: "The change failed. Please check the current state and try again.",
		bridgePvRequired: "Open Edit under Prices & times and add the solar forecast. The previous charging method is preserved.",
		bridgeTariffRequired: "First set up a time-of-use tariff with valid prices. The previous charging method is preserved.",
		on: "On",
		off: "Off"
	}
}, Co = Symbol("sax-dashboard");
function wo(e) {
	return typeof e != "string" || e.length !== 5 && e.length !== 8 || !/^([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(e) ? null : e.length === 5 ? `${e}:00` : e;
}
function To(e, t, n, r, i) {
	let a = So[r];
	if (!i || !n || n.state === "unavailable") return a.unavailable;
	if (n.state === "unknown") return a.unknown;
	if (e?.formatEntityState) return e.formatEntityState(n);
	if (t.states[n.state]) return t.states[n.state];
	if (n.attributes.device_class === "date") {
		let t = /* @__PURE__ */ new Date(`${n.state}T00:00:00Z`);
		if (/^\d{4}-\d{2}-\d{2}$/.test(n.state) && !Number.isNaN(t.getTime()) && t.toISOString().slice(0, 10) === n.state) try {
			return new Intl.DateTimeFormat(e?.locale?.language ?? e?.language ?? r, {
				dateStyle: "medium",
				timeZone: "UTC"
			}).format(t);
		} catch {
			return n.state;
		}
		return n.state;
	}
	if (n.attributes.device_class === "timestamp") {
		let t = new Date(n.state);
		if (!Number.isNaN(t.getTime())) try {
			return new Intl.DateTimeFormat(e?.locale?.language ?? e?.language ?? r, {
				dateStyle: "medium",
				timeStyle: "short",
				timeZone: e?.config?.time_zone,
				hour12: e?.locale?.time_format === "am_pm" || e?.locale?.time_format !== "twenty_four" && void 0
			}).format(t);
		} catch {
			return n.state;
		}
	}
	if ((t.domain === "switch" || t.domain === "binary_sensor") && (n.state === "on" || n.state === "off")) return a[n.state];
	let o = n.state.trim() === "" ? NaN : Number(n.state);
	if (Number.isFinite(o)) {
		let t = {
			comma_decimal: "en-US",
			decimal_comma: "de-DE",
			space_comma: "fr-FR"
		}[e?.locale?.number_format ?? ""] ?? e?.locale?.language ?? e?.language ?? r, i;
		try {
			i = new Intl.NumberFormat(t, {
				maximumFractionDigits: 20,
				useGrouping: e?.locale?.number_format !== "none"
			}).format(o);
		} catch {
			i = String(o);
		}
		let a = n.attributes.unit_of_measurement;
		return typeof a == "string" && a ? `${i} ${a}` : i;
	}
	return n.state;
}
function Eo(e, t) {
	let n = e.state?.attributes ?? {};
	switch (e.metadata.domain) {
		case "switch": return typeof t == "boolean" ? {
			service: t ? "turn_on" : "turn_off",
			data: {}
		} : null;
		case "number": {
			if (typeof t != "number" && typeof t != "string" || typeof t == "string" && t.trim() === "") return null;
			let e = Number(t), { min: r, max: i, step: a } = n;
			if (!Number.isFinite(e) || typeof r != "number" || !Number.isFinite(r) || typeof i != "number" || !Number.isFinite(i) || typeof a != "number" || !Number.isFinite(a) || a <= 0 || r > i || e < r || typeof n.min_positive == "number" && e > 0 && e < n.min_positive || e > i) return null;
			let o = (e - r) / a;
			return !Number.isFinite(o) || Math.abs(o - Math.round(o)) > 1e-7 ? null : {
				service: "set_value",
				data: { value: e }
			};
		}
		case "time": {
			let e = wo(t);
			return e ? {
				service: "set_value",
				data: { time: e }
			} : null;
		}
		case "select": return typeof t == "string" && Array.isArray(n.options) && n.options.includes(t) ? {
			service: "select_option",
			data: { option: t }
		} : null;
		default: return null;
	}
}
function Do(e, t) {
	let n = Z(() => e()?.language.toLowerCase().startsWith("de") ? "de" : "en"), r = /* @__PURE__ */ Gt(null), i = /* @__PURE__ */ z(!1), a = /* @__PURE__ */ z(!1), o = /* @__PURE__ */ z(null), s = Z(() => o.value ? So[n.value][o.value] : null), c = /* @__PURE__ */ Gt([]), l = /* @__PURE__ */ Nt(/* @__PURE__ */ new Map()), u = /* @__PURE__ */ Nt(/* @__PURE__ */ new Map()), d = (e, n) => JSON.stringify([
		t(),
		e,
		n
	]), f = 0;
	function p(e = !0) {
		e && (f += 1), i.value = !1, r.value = null, c.value = [];
		for (let [e, t] of l) t.pending ? t.error = null : l.delete(e);
	}
	let m = V([
		() => e()?.connection,
		t,
		() => e()?.language
	], ([n, r, s], u, d) => {
		if (p(n !== u?.[0] || r !== u?.[1]), o.value = null, a.value = n?.connected ?? !1, !n || !r) return;
		let f = !1, m, h = 0;
		function g(e) {
			try {
				Promise.resolve(e()).catch(() => {});
			} catch {}
		}
		function _(e = !0) {
			h += 1, p(e), m && g(m), m = void 0;
		}
		function v() {
			if (f || !n || !n.connected) return;
			_(!1), a.value = !0, o.value = null;
			let e = h;
			n.subscribeMessage((t) => {
				if (f || e !== h || !a.value) return;
				c.value = t.entities;
				let n = new Set(t.entities.map((e) => e.entity_id));
				for (let e of l.keys()) !n.has(e) && !l.get(e)?.pending && l.delete(e);
				i.value = !0, o.value = null;
			}, {
				type: "sax_power/dashboard/subscribe",
				entry_id: r,
				language: s || "en"
			}, { resubscribe: !1 }).then((t) => {
				f || e !== h ? g(t) : m = t;
			}).catch(() => {
				!f && e === h && (p(), o.value = "loadFailed");
			});
		}
		function y() {
			f || (a.value = !1, _(), o.value = "disconnected");
		}
		n.addEventListener("ready", v), n.addEventListener("disconnected", y), n.addEventListener("reconnect-error", y), n.connected ? v() : o.value = "disconnected", d(() => {
			f = !0, n.removeEventListener("ready", v), n.removeEventListener("disconnected", y), n.removeEventListener("reconnect-error", y), _(e()?.connection !== n || t() !== r);
		});
	}, {
		immediate: !0,
		flush: "sync"
	});
	we(() => {
		m(), p(), a.value = !1;
	});
	function h(t, r) {
		let i = c.value.find((e) => e.domain === t && e.key === r);
		if (!i) return null;
		let o = e(), s = o?.states[i.entity_id], f = a.value && !!s && s.state !== "unknown" && s.state !== "unavailable", p = u.get(d(t, r)) ?? l.get(i.entity_id);
		return {
			metadata: i,
			state: s,
			available: f,
			name: i.name ?? (typeof s?.attributes.friendly_name == "string" ? s.attributes.friendly_name : i.key),
			displayValue: To(o, i, s, n.value, a.value),
			canControl: f && i.can_control && !!o?.callService,
			pending: p?.pending ?? !1,
			error: p?.error ? So[n.value][p.error] : null
		};
	}
	async function g(t, n, r) {
		let a = h(t, n);
		if (!a || a.pending) return !1;
		let o = /* @__PURE__ */ Nt({
			pending: !1,
			error: null
		});
		l.set(a.metadata.entity_id, o);
		let s = e();
		if (!a.canControl || !s?.callService || !i.value) return o.error = "forbidden", !1;
		let c = Eo(a, r);
		if (!c) return o.error = "invalid", !1;
		if (t === "number" && (n === "timed_charge_max_soc" || n === "timed_charge_min_soc")) {
			let e = n === "timed_charge_max_soc", t = h("number", e ? "timed_charge_min_soc" : "timed_charge_max_soc"), r = t?.available ? Q(t.state?.state) : null, i = Number(c.data.value);
			if (r !== null && (e ? i < r : i > r)) return o.error = "timedSocOrder", !1;
		}
		o.pending = !0;
		let p = d(t, n);
		u.set(p, o);
		let m = f, g = () => m === f && l.get(a.metadata.entity_id) === o && h(t, n)?.metadata.entity_id === a.metadata.entity_id;
		try {
			return await s.callService(t, c.service, c.data, { entity_id: a.metadata.entity_id }, !1), g();
		} catch (e) {
			return g() && (o.error = "failed", e && typeof e == "object" && "translation_domain" in e && e.translation_domain === "sax_power" && "translation_key" in e && (t === "number" && e.translation_key === "timed_charge_soc_order" ? o.error = "timedSocOrder" : t === "switch" && n === "bridge_charge_enabled" && (e.translation_key === "bridge_pv_start_required" ? o.error = "bridgePvRequired" : e.translation_key === "bridge_tariff_required" && (o.error = "bridgeTariffRequired")))), !1;
		} finally {
			o.pending = !1, u.get(p) === o && u.delete(p);
		}
	}
	async function _(t, n, r) {
		let a = [`${t}_start`, `${t}_end`], o = a.map((e) => h("time", e));
		if (o.some((e) => e?.pending)) return !1;
		let s = /* @__PURE__ */ Nt({
			pending: !1,
			error: null
		});
		for (let e of o) e && l.set(e.metadata.entity_id, s);
		let c = o[0]?.metadata.device_id, p = e();
		if (!i.value || !p?.callService || !c || o.some((e) => !e?.canControl || e.metadata.device_id !== c)) return s.error = "forbidden", !1;
		let m = wo(n), g = wo(r);
		if (!m || !g) return s.error = "invalid", !1;
		let _ = o.map((e) => e.metadata.entity_id), v = a.map((e) => d("time", e));
		s.pending = !0;
		for (let e of v) u.set(e, s);
		let y = f, b = () => y === f && _.every((e, t) => {
			let n = h("time", a[t]);
			return l.get(e) === s && n?.metadata.entity_id === e && n.metadata.device_id === c;
		});
		try {
			return await p.callService("sax_power", `set_${t}_window`, {
				device_id: c,
				start: m,
				end: g
			}, void 0, !1), b();
		} catch {
			return b() && (s.error = "failed"), !1;
		} finally {
			s.pending = !1;
			for (let e of v) u.get(e) === s && u.delete(e);
		}
	}
	async function v(t) {
		let n = /* @__PURE__ */ new Set([
			"max_soc",
			"timed_charge_min_soc",
			"timed_charge_max_soc",
			"bridge_charge_min_energy_kwh",
			"bridge_charge_soc_buffer",
			"price_charge_max_price",
			"price_charge_hours",
			"price_charge_neutral_price"
		]), r = Object.keys(t);
		if (!r.length || r.some((e) => !n.has(e))) return !1;
		let a = r.map((e) => h("number", e));
		if (a.some((e) => e?.pending)) return !1;
		let o = /* @__PURE__ */ Nt({
			pending: !1,
			error: null
		});
		for (let e of a) e && l.set(e.metadata.entity_id, o);
		let s = a[0]?.metadata.device_id, c = e();
		if (!i.value || !c?.callService || !s || a.some((e) => !e?.canControl || e.metadata.device_id !== s)) return o.error = "forbidden", !1;
		let p = {}, m = t.max_soc === void 0 ? Q(h("number", "max_soc")?.state?.state) : Q(t.max_soc);
		for (let e = 0; e < r.length; e++) {
			let n = r[e], i = a[e], s = Eo(n === "timed_charge_max_soc" && m !== null ? {
				...i,
				state: {
					...i.state,
					attributes: {
						...i.state.attributes,
						max: m
					}
				}
			} : i, t[n]);
			if (!s) return o.error = "invalid", !1;
			p[n] = Number(s.data.value);
		}
		if (p.timed_charge_min_soc !== void 0 || p.timed_charge_max_soc !== void 0) {
			let e = p.timed_charge_min_soc ?? Q(h("number", "timed_charge_min_soc")?.state?.state), t = p.timed_charge_max_soc ?? Q(h("number", "timed_charge_max_soc")?.state?.state);
			if (e === null || t === null) return o.error = "invalid", !1;
			if (t < e) return o.error = "timedSocOrder", !1;
		}
		let g = a.map((e) => e.metadata.entity_id), _ = r.map((e) => d("number", e));
		o.pending = !0;
		for (let e of _) u.set(e, o);
		let v = f, y = () => v === f && g.every((e, t) => {
			let n = h("number", r[t]);
			return l.get(e) === o && n?.metadata.entity_id === e && n.metadata.device_id === s;
		});
		try {
			return await c.callService("sax_power", "set_charging_settings", {
				device_id: s,
				...p
			}, void 0, !1), y();
		} catch (e) {
			if (y()) {
				let t = e, n = t?.translation_domain === "sax_power" && t.translation_key === "invalid_charging_setting" && typeof t.translation_placeholders?.field == "string" ? t.translation_placeholders.field : null;
				if (n && r.includes(n)) {
					for (let e = 0; e < r.length; e++) l.set(g[e], /* @__PURE__ */ Nt({
						pending: !1,
						error: r[e] === n ? "invalid" : null
					}));
					return !1;
				}
				o.error = e && typeof e == "object" && "translation_domain" in e && e.translation_domain === "sax_power" && "translation_key" in e && e.translation_key === "timed_charge_soc_order" ? "timedSocOrder" : "failed";
			}
			return !1;
		} finally {
			o.pending = !1;
			for (let e of _) u.get(e) === o && u.delete(e);
		}
	}
	let y = 0, b = null, x = null;
	async function S(n) {
		let o = e(), s = t();
		if (!a.value) throw { code: "disconnected" };
		if (!i.value || !o?.callWS || !s) throw { code: "forbidden" };
		let c = o.callWS.bind(o), l = f;
		if (!n && b?.generation === l) return b.promise;
		let u = ++y, d = c({
			type: `sax_power/dashboard/tariff/${n ? "tariff_type" in n ? "configure" : "save" : "get"}`,
			entry_id: s,
			...n
		});
		function p(e) {
			if (l !== f || !a.value) throw { code: "disconnected" };
			if (!e || typeof e.revision != "string") throw { code: "failed" };
			return e;
		}
		function m() {
			return b?.promise === g && b.refreshAutomation && l === f && a.value && i.value;
		}
		async function h(e) {
			for (; m();) b.refreshAutomation = !1, y++, e = p(await c({
				type: "sax_power/dashboard/tariff/get",
				entry_id: s
			}));
			return e;
		}
		let g;
		return g = (async () => {
			try {
				let e;
				try {
					e = p(await d);
				} catch (e) {
					if (n && m()) try {
						let e;
						do
							e = await h(e);
						while (m());
						e && (y++, r.value = p(e));
					} catch {}
					throw e;
				}
				if (!n && u !== y) return b?.generation === l ? b.promise : x?.generation === l && x.sequence !== u ? x.promise : r.value ?? e;
				if (n) {
					for (; m();) e = p(await h(e));
					y++;
				}
				return r.value = e, e;
			} finally {
				b?.promise === g && (b = null), x?.promise === g && (x = null);
			}
		})(), n ? b = {
			generation: l,
			promise: g,
			refreshAutomation: !1
		} : x = {
			generation: l,
			sequence: u,
			promise: g
		}, g;
	}
	V([
		() => h("switch", "timed_charge_enabled")?.metadata.entity_id,
		() => h("switch", "timed_charge_enabled")?.state?.state,
		() => h("switch", "price_charge_enabled")?.metadata.entity_id,
		() => h("switch", "price_charge_enabled")?.state?.state
	], () => {
		a.value && i.value && (b?.generation === f ? b.refreshAutomation = !0 : r.value && S().catch(() => {}));
	}, { flush: "sync" });
	async function C(n) {
		let r = e(), o = t();
		if (!a.value) throw { code: "disconnected" };
		if (!i.value || !r?.callWS || !o) throw { code: "forbidden" };
		let s = f, c = await r.callWS({
			type: "sax_power/dashboard/tariff/series",
			entry_id: o,
			day: n
		});
		if (s !== f || !a.value) throw { code: "disconnected" };
		if (!c || !Array.isArray(c.slots) || typeof c.start != "string") throw { code: "failed" };
		return c;
	}
	async function w(n) {
		let r = e(), o = t();
		if (!a.value) throw { code: "disconnected" };
		if (!i.value || !r?.callWS || !o) throw { code: "forbidden" };
		let s = f, c = await r.callWS({
			type: `sax_power/dashboard/grid_serving/${n ? "save" : "get"}`,
			entry_id: o,
			...n
		});
		if (s !== f || !a.value) throw { code: "disconnected" };
		if (!c || typeof c.revision != "string" || typeof c.can_edit != "boolean" || c.pv_sensor !== null && typeof c.pv_sensor != "string") throw { code: "failed" };
		return c;
	}
	return {
		language: n,
		ready: /* @__PURE__ */ Ft(i),
		connected: /* @__PURE__ */ Ft(a),
		error: s,
		entity: h,
		perform: g,
		performChargingSettings: v,
		clearControlError: (e, t) => {
			let n = h(e, t), r = n && l.get(n.metadata.entity_id);
			r && !r.pending && (r.error = null);
		},
		performTimeWindow: _,
		tariff: Z(() => r.value),
		loadTariff: () => S(),
		saveTariff: (e) => S(e),
		configureTariff: (e) => S(e),
		loadTariffSeries: C,
		loadGridServingForecast: () => w(),
		saveGridServingForecast: (e) => w(e)
	};
}
//#endregion
//#region src/components/EditorActions.vue?vue&type=style&index=0&inline&lang.css
var Oo = ".editor-actions{flex-wrap:nowrap;align-items:center;gap:8px;max-width:100%;display:flex}.editor-actions>button{white-space:nowrap;flex:none}.editor-actions>button:first-child:not(:only-child){background:var(--primary-color,#03a9f4);color:var(--text-primary-color,#fff)}", ko = (e, t) => {
	let n = e.__vccOpts || e;
	for (let [e, r] of t) n[e] = r;
	return n;
}, Ao = {}, jo = { class: "editor-actions" };
function Mo(e, t) {
	return W(), G("div", jo, [ur(e.$slots, "default")]);
}
var No = /*#__PURE__*/ ko(Ao, [["render", Mo], ["styles", [Oo]]]), Po = ["aria-busy"], Fo = { class: "entity-control__name" }, Io = [
	"checked",
	"indeterminate",
	"disabled"
], Lo = { class: "entity-control__description" }, Ro = { key: 0 }, zo = { class: "entity-control__input" }, Bo = [
	"checked",
	"disabled",
	"aria-describedby"
], Vo = [
	"value",
	"disabled",
	"aria-describedby"
], Ho = {
	key: 0,
	value: "",
	disabled: ""
}, Uo = ["value"], Wo = [
	"value",
	"type",
	"min",
	"max",
	"step",
	"disabled",
	"aria-describedby",
	"aria-invalid"
], Go = ["disabled"], Ko = ["disabled"], qo = {
	key: 0,
	class: "entity-control__error",
	role: "alert"
}, Jo = {
	key: 1,
	role: "status"
}, Yo = ["aria-labelledby", "aria-describedby"], Xo = ["id"], Zo = ["id"], Qo = ["disabled"], $o = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "EntityControl",
	props: {
		domain: { type: String },
		entityKey: { type: String },
		label: { type: String },
		confirmSwitch: { type: Boolean },
		hideConfirmedLabel: { type: Boolean },
		monthTile: { type: Boolean },
		timeUnit: { type: Boolean }
	},
	setup(e) {
		let t = e, n = Pn(Co), r = Z(() => n?.entity(t.domain, t.entityKey)), i = Kn(), a = `sax-control-${i}`, o = `sax-status-${i}`, s = `sax-value-${i}`, c = /* @__PURE__ */ z(""), l = /* @__PURE__ */ z(), u = /* @__PURE__ */ z(), d = /* @__PURE__ */ Gt(null), f = Z(() => r.value?.state?.state ?? ""), p = Z(() => r.value?.state?.attributes ?? {}), m = Z(() => {
			let e = p.value.options;
			return Array.isArray(e) ? e.filter((e) => typeof e == "string") : [];
		}), h = Z(() => n?.language.value ?? "en"), g = Z(() => t.domain === "switch" ? o : `${s} ${o}`), _ = Z(() => {
			let e = r.value?.displayValue;
			return t.timeUnit && t.domain === "time" && h.value === "de" && r.value?.available && /^(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(f.value) ? `${e} Uhr` : e;
		}), v = Z(() => h.value === "de" ? {
			apply: "Übernehmen",
			confirmed: "Bestätigter Wert",
			disconnected: "Keine Verbindung zu Home Assistant",
			unavailable: "Nicht verfügbar",
			readOnly: "Keine Berechtigung zum Ändern",
			pending: "Änderung wird an Home Assistant gesendet …",
			cancel: "Abbrechen",
			confirmationTitle: d.value?.desired ? "Speicher einschalten?" : "Speicher ausschalten?",
			confirmationQuestion: d.value?.desired ? "Möchten Sie den Speicher wirklich einschalten?" : "Möchten Sie den Speicher wirklich ausschalten?"
		} : {
			apply: "Apply",
			confirmed: "Confirmed value",
			disconnected: "Disconnected from Home Assistant",
			unavailable: "Unavailable",
			readOnly: "You do not have permission to change this setting",
			pending: "Sending change to Home Assistant …",
			cancel: "Cancel",
			confirmationTitle: d.value?.desired ? "Turn on the battery?" : "Turn off the battery?",
			confirmationQuestion: d.value?.desired ? "Do you really want to turn on the battery?" : "Do you really want to turn off the battery?"
		}), y = Z(() => !r.value?.canControl || r.value.pending || t.monthTile && f.value !== "on" && f.value !== "off"), b = Z(() => n?.connected.value ? !r.value?.available || t.monthTile && f.value !== "on" && f.value !== "off" ? v.value.unavailable : r.value.metadata.can_control ? r.value.pending ? v.value.pending : "" : v.value.readOnly : v.value.disconnected);
		function x(e) {
			return r.value?.available ? t.domain === "time" ? S(e) : e : "";
		}
		function S(e) {
			return /^(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(e) ? e.slice(0, 5) : "";
		}
		function C(e) {
			let n = e.target;
			c.value = t.domain === "time" ? S(n.value) : n.value, t.domain === "time" && (n.value = c.value);
		}
		V([() => r.value?.metadata.entity_id, () => f.value], ([, e]) => {
			c.value = x(e);
		}, { immediate: !0 });
		function w(e) {
			let t = p.value[e];
			return typeof t == "number" && Number.isFinite(t) ? t : void 0;
		}
		function T(e) {
			return r.value?.metadata.states[e] ?? e;
		}
		function E() {
			r.value?.pending || (c.value = x(f.value), u.value && (u.value.value = c.value), n?.clearControlError(t.domain, t.entityKey));
		}
		async function D() {
			y.value || !n || t.domain !== "number" && t.domain !== "time" || await n.perform(t.domain, t.entityKey, t.domain === "time" && c.value ? `${c.value}:00` : c.value);
		}
		function O() {
			d.value = null, l.value?.open && l.value.close();
		}
		function k() {
			l.value?.open || (d.value = null);
		}
		V([
			() => r.value?.metadata.entity_id,
			f,
			y,
			() => t.domain,
			() => t.entityKey,
			() => t.confirmSwitch
		], O, { flush: "sync" }), cr(O);
		async function ee() {
			let e = d.value;
			O(), e && !y.value && n && e.entityId === r.value?.metadata.entity_id && e.sourceState === f.value && e.domain === t.domain && e.key === t.entityKey && await n.perform(t.domain, t.entityKey, e.desired);
		}
		async function A(e) {
			let i = e.target, a = i.checked;
			if (i.checked = f.value === "on", !y.value && n) {
				if (t.confirmSwitch && r.value) {
					let e = {
						entityId: r.value.metadata.entity_id,
						domain: t.domain,
						key: t.entityKey,
						sourceState: f.value,
						desired: a
					};
					d.value = e, await vn(), d.value === e && !y.value && l.value?.showModal();
					return;
				}
				await n.perform(t.domain, t.entityKey, a);
			}
		}
		async function te(e) {
			let r = e.target, i = r.value;
			r.value = f.value, !y.value && n && await n.perform(t.domain, t.entityKey, i);
		}
		return (t, n) => r.value ? (W(), G("form", {
			key: 0,
			class: P(["entity-control", {
				"entity-control--month": e.monthTile,
				"entity-control--selected": e.monthTile && r.value.available && f.value === "on"
			}]),
			"aria-busy": r.value.pending,
			onSubmit: io(D, ["prevent"])
		}, [
			e.monthTile && e.domain === "switch" ? (W(), G("label", {
				key: 0,
				for: a,
				class: "entity-control__switch-target entity-control__month-target"
			}, [q("span", Fo, F(e.label ?? r.value.name), 1), q("input", {
				id: a,
				type: "checkbox",
				role: "switch",
				checked: r.value.available && f.value === "on",
				indeterminate: !r.value.available || f.value !== "on" && f.value !== "off",
				disabled: y.value,
				"aria-describedby": o,
				onChange: A
			}, null, 40, Io)])) : (W(), G(U, { key: 1 }, [q("div", Lo, [q("label", {
				for: a,
				class: "entity-control__name"
			}, F(e.label ?? r.value.name), 1), e.domain === "switch" ? X("", !0) : (W(), G("p", {
				key: 0,
				id: s,
				class: "entity-control__value"
			}, [e.hideConfirmedLabel ? X("", !0) : (W(), G("span", Ro, F(v.value.confirmed) + ":", 1)), Y(" " + F(_.value), 1)]))]), q("div", zo, [e.domain === "switch" ? (W(), G("label", {
				key: 0,
				for: a,
				class: "entity-control__switch-target"
			}, [q("input", {
				id: a,
				type: "checkbox",
				role: "switch",
				checked: f.value === "on",
				disabled: y.value,
				"aria-describedby": g.value,
				onChange: A
			}, null, 40, Bo)])) : e.domain === "select" ? (W(), G("select", {
				key: 1,
				id: a,
				value: r.value.available ? f.value : "",
				disabled: y.value,
				"aria-describedby": g.value,
				onChange: te
			}, [r.value.available ? X("", !0) : (W(), G("option", Ho, F(v.value.unavailable), 1)), (W(!0), G(U, null, H(m.value, (e) => (W(), G("option", {
				key: e,
				value: e
			}, F(T(e)), 9, Uo))), 128))], 40, Vo)) : (W(), G(U, { key: 2 }, [q("input", {
				ref_key: "draftInput",
				ref: u,
				id: a,
				value: c.value,
				type: e.domain === "number" ? "number" : "time",
				min: e.domain === "number" ? w("min") : void 0,
				max: e.domain === "number" ? w("max") : void 0,
				step: e.domain === "number" ? w("step") : 60,
				disabled: y.value,
				"aria-describedby": g.value,
				"aria-invalid": !!r.value.error,
				required: "",
				onInput: C,
				onInvalid: io(D, ["prevent"])
			}, null, 40, Wo), J(No, null, {
				default: An(() => [q("button", {
					type: "submit",
					disabled: y.value || e.domain === "time" && c.value === ""
				}, F(v.value.apply), 9, Go), q("button", {
					type: "button",
					disabled: r.value.pending,
					onClick: E
				}, F(v.value.cancel), 9, Ko)]),
				_: 1
			})], 64))])], 64)),
			q("div", {
				id: o,
				class: "entity-control__feedback"
			}, [r.value.error ? (W(), G("p", qo, F(r.value.error), 1)) : b.value ? (W(), G("p", Jo, F(b.value), 1)) : X("", !0)]),
			e.confirmSwitch ? (W(), G("dialog", {
				key: 2,
				ref_key: "dialog",
				ref: l,
				class: "entity-control__confirmation",
				"aria-labelledby": `${B(i)}-confirmation-title`,
				"aria-describedby": `${B(i)}-confirmation-question`,
				onCancel: io(O, ["prevent"]),
				onClose: k
			}, [
				q("h3", { id: `${B(i)}-confirmation-title` }, F(v.value.confirmationTitle), 9, Xo),
				q("p", { id: `${B(i)}-confirmation-question` }, F(v.value.confirmationQuestion), 9, Zo),
				J(No, { class: "entity-control__confirmation-actions" }, {
					default: An(() => [q("button", {
						type: "button",
						disabled: y.value || !d.value,
						onClick: ee
					}, F(v.value.apply), 9, Qo), q("button", {
						type: "button",
						autofocus: "",
						onClick: O
					}, F(v.value.cancel), 1)]),
					_: 1
				})
			], 40, Yo)) : X("", !0)
		], 42, Po)) : X("", !0);
	}
}), [["styles", [".entity-control{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));color:var(--primary-text-color,#212121);box-shadow:var(--ha-card-box-shadow,none);flex-wrap:wrap;align-items:center;gap:12px 24px;padding:20px;display:flex}.entity-control__description{overflow-wrap:anywhere;flex:200px;min-width:0}.entity-control__name{font-weight:500;line-height:1.5;display:block}.entity-control__value{color:var(--secondary-text-color,#666);margin:4px 0 0;font-size:.9em;line-height:1.5}.entity-control__input{flex-wrap:wrap;align-items:center;gap:8px;max-width:100%;display:flex}.entity-control__switch-target{cursor:pointer;justify-content:center;align-items:center;min-width:44px;min-height:44px;display:flex}.entity-control__switch-target:has(:disabled){cursor:not-allowed}.entity-control input,.entity-control select,.entity-control button{border:1px solid var(--divider-color,#767676);max-width:100%;min-height:44px;color:inherit;background:var(--card-background-color,#fff);font:inherit;border-radius:6px;padding:8px 12px}.entity-control input[type=number]{width:120px}.entity-control input[type=checkbox]{width:22px;height:22px;min-height:22px;accent-color:var(--primary-color,#03a9f4);cursor:pointer;flex-shrink:0;margin:0;padding:0}.entity-control button{border-color:var(--primary-color,#03a9f4);color:var(--primary-text-color,#212121);cursor:pointer}.entity-control :disabled{cursor:not-allowed;opacity:.6}.entity-control input:focus-visible,.entity-control select:focus-visible,.entity-control button:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.entity-control__feedback{color:var(--secondary-text-color,#666);flex-basis:100%;line-height:1.5}.entity-control__feedback:empty{display:none}.entity-control__feedback p{margin:0}.entity-control__error{color:var(--error-color,#b71c1c)}.entity-control__confirmation{border:1px solid var(--divider-color,#767676);background:var(--card-background-color,#fff);width:min(440px,100vw - 32px);max-height:calc(100vh - 32px);color:var(--primary-text-color,#212121);border-radius:12px;padding:24px;overflow:auto}.entity-control__confirmation::backdrop{background:#0000008c}.entity-control__confirmation h3{margin:0;font-size:20px;line-height:1.4}.entity-control__confirmation p{margin:16px 0 24px;line-height:1.6}.entity-control__confirmation-actions{justify-content:flex-end}@container sax-content (width>=860px){.entity-control{gap:8px 12px;padding:14px}.entity-control__description{flex-basis:140px}.entity-control__value{margin-top:2px;font-size:14px}.entity-control input[type=number]{width:104px}}"]]]), es = [
	"role",
	"aria-labelledby",
	"aria-valuemin",
	"aria-valuemax",
	"aria-valuenow",
	"aria-valuetext"
], ts = {
	viewBox: "0 0 240 124",
	"aria-hidden": "true"
}, ns = ["stroke-dasharray", "stroke-dashoffset"], rs = ["transform"], is = {
	class: "entity-gauge__scale",
	"aria-hidden": "true"
}, as = { class: "entity-gauge__value" }, os = {
	key: 0,
	class: "entity-gauge__range"
}, ss = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "EntityGauge",
	props: {
		entityKey: { type: String },
		maximum: { type: Number },
		segments: { type: Array }
	},
	setup(e) {
		let t = e, n = Pn(Co), r = Z(() => n?.entity("sensor", t.entityKey)), i = `sax-gauge-${Kn()}`, a = Z(() => {
			let e = r.value?.state?.state.trim();
			if (!r.value?.available || !e) return null;
			let t = Number(e);
			return Number.isFinite(t) ? t : null;
		}), o = Z(() => a.value === null ? null : Math.max(0, Math.min(t.maximum, a.value))), s = Z(() => a.value === null ? null : [...t.segments].reverse().find((e) => a.value >= e.from)?.label ?? t.segments[0]?.label), c = Z(() => r.value?.available && a.value === null ? n?.language.value === "de" ? "Unbekannt" : "Unknown" : r.value?.displayValue), l = Z(() => t.segments.map((e, n) => ({
			...e,
			offset: -(e.from / t.maximum) * 100,
			length: ((t.segments[n + 1]?.from ?? t.maximum) - e.from) / t.maximum * 100
		})));
		return (t, n) => r.value ? (W(), G("section", {
			key: 0,
			class: "entity-gauge",
			"aria-labelledby": i
		}, [q("h2", { id: i }, F(r.value.name), 1), q("div", {
			class: "entity-gauge__meter",
			role: o.value === null ? void 0 : "meter",
			"aria-labelledby": o.value === null ? void 0 : i,
			"aria-valuemin": o.value === null ? void 0 : 0,
			"aria-valuemax": o.value === null ? void 0 : e.maximum,
			"aria-valuenow": o.value ?? void 0,
			"aria-valuetext": o.value === null ? void 0 : `${c.value} · ${s.value}`
		}, [
			(W(), G("svg", ts, [n[1] ||= q("path", {
				class: "entity-gauge__track",
				d: "M20 110 A100 100 0 0 1 220 110"
			}, null, -1), o.value === null ? X("", !0) : (W(), G(U, { key: 0 }, [
				(W(!0), G(U, null, H(l.value, (e) => (W(), G("path", {
					key: e.from,
					class: P(["entity-gauge__segment", `entity-gauge__segment--${e.color}`]),
					d: "M20 110 A100 100 0 0 1 220 110",
					pathLength: "100",
					"stroke-dasharray": `${e.length} 100`,
					"stroke-dashoffset": e.offset
				}, null, 10, ns))), 128)),
				q("line", {
					class: "entity-gauge__needle",
					x1: "120",
					y1: "110",
					x2: "120",
					y2: "33",
					transform: `rotate(${o.value / e.maximum * 180 - 90} 120 110)`
				}, null, 8, rs),
				n[0] ||= q("circle", {
					class: "entity-gauge__pivot",
					cx: "120",
					cy: "110",
					r: "5"
				}, null, -1)
			], 64))])),
			q("div", is, [n[2] ||= q("span", null, "0", -1), q("span", null, F(e.maximum), 1)]),
			q("p", as, F(c.value), 1),
			s.value ? (W(), G("p", os, F(s.value), 1)) : X("", !0)
		], 8, es)])) : X("", !0);
	}
}), [["styles", [".entity-gauge{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);text-align:center;padding:24px}.entity-gauge h2{overflow-wrap:anywhere;margin:0 0 20px;font-size:16px;font-weight:500;line-height:1.5}.entity-gauge__meter{max-width:260px;margin:0 auto}.entity-gauge svg{fill:none;width:100%;display:block}.entity-gauge__track,.entity-gauge__segment{stroke-width:15px;stroke-linecap:butt}.entity-gauge__track{stroke:var(--divider-color,#e0e0e0)}.entity-gauge__segment--red{stroke:var(--error-color,#db4437)}.entity-gauge__segment--yellow{stroke:var(--warning-color,#f4b400)}.entity-gauge__segment--green{stroke:var(--success-color,#0f9d58)}.entity-gauge__needle{stroke:var(--primary-text-color,#212121);stroke-width:3px;stroke-linecap:round}.entity-gauge__pivot{stroke:none;fill:var(--primary-text-color,#212121)}.entity-gauge__scale{color:var(--secondary-text-color,#666);justify-content:space-between;padding:2px 7px;font-size:12px;display:flex}.entity-gauge__value{overflow-wrap:anywhere;margin:10px 0 0;font-size:28px;font-weight:500;line-height:1.4}.entity-gauge__range{color:var(--secondary-text-color,#666);margin:4px 0 0;font-size:14px;line-height:1.5}@container sax-content (width>=860px){.entity-gauge{padding:16px}.entity-gauge h2{margin-bottom:8px}.entity-gauge__meter{max-width:180px}.entity-gauge__value{margin-top:6px;font-size:24px}.entity-gauge__range{margin-top:2px}}"]]]), cs = {
	key: 0,
	class: "entity-value"
}, ls = { class: "entity-value__name" }, us = { class: "entity-value__state" }, ds = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "EntityValue",
	props: {
		domain: { type: null },
		entityKey: { type: String }
	},
	setup(e) {
		let t = e, n = Pn(Co), r = Z(() => n?.entity(t.domain, t.entityKey));
		return (e, t) => r.value ? (W(), G("div", cs, [q("span", ls, F(r.value.name), 1), q("span", us, F(r.value.displayValue), 1)])) : X("", !0);
	}
}), [["styles", [".entity-value{color:var(--primary-text-color,#212121);overflow-wrap:anywhere;flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:8px 20px;line-height:1.5;display:flex}.entity-value__name{color:var(--secondary-text-color,#666)}.entity-value__state{font-weight:500}"]]]), fs = { class: "general-view" }, ps = {
	key: 0,
	class: "general-view__status",
	role: "status"
}, ms = {
	key: 1,
	class: "general-view__status",
	role: "status"
}, hs = {
	key: 2,
	class: "general-view__gauges"
}, gs = ["aria-labelledby"], _s = ["id"], vs = { class: "general-view__rows" }, ys = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "GeneralView",
	setup(e) {
		let t = Pn(Co), n = Kn(), r = Z(() => t?.language.value === "de" ? {
			power: "Leistung",
			device: "Gerät",
			low: "Niedrig",
			medium: "Mittel",
			high: "Hoch",
			inRange: "Im Bereich",
			loading: "Die Entitäten werden geladen …",
			empty: "Für diese Ansicht sind keine Entitäten verfügbar."
		} : {
			power: "Power",
			device: "Device",
			low: "Low",
			medium: "Medium",
			high: "High",
			inRange: "In range",
			loading: "Loading entities …",
			empty: "No entities are available for this view."
		}), i = [{
			title: "power",
			entities: [
				["number", "max_soc"],
				["sensor", "charge_power"],
				["sensor", "discharge_power"],
				["sensor", "smartmeter_power"]
			]
		}, {
			title: "device",
			entities: [
				["sensor", "battery_capacity"],
				["sensor", "energy_charged"],
				["sensor", "energy_discharged"],
				["sensor", "sun_version_master"],
				["sensor", "sun_version_gateway"],
				["sensor", "sun_serial_number"],
				["sensor", "storage_event_text"],
				["sensor", "ic_control_mode_text"],
				["binary_sensor", "cell_calibration_active"],
				["sensor", "next_cell_calibration"],
				["switch", "storage_switch"]
			]
		}], a = Z(() => i.map((e) => ({
			...e,
			entities: e.entities.filter(([e, n]) => t?.entity(e, n))
		})).filter((e) => e.entities.length)), o = Z(() => !!(t?.entity("sensor", "soc") || t?.entity("sensor", "storage_max_cell_temp"))), s = Z(() => o.value || a.value.length > 0);
		return (e, i) => (W(), G("div", fs, [
			!B(t)?.ready.value && !B(t)?.error.value ? (W(), G("p", ps, F(r.value.loading), 1)) : B(t)?.ready.value && !s.value ? (W(), G("p", ms, F(r.value.empty), 1)) : X("", !0),
			o.value ? (W(), G("div", hs, [J(ss, {
				"entity-key": "soc",
				maximum: 100,
				segments: [
					{
						from: 0,
						color: "red",
						label: r.value.low
					},
					{
						from: 20,
						color: "yellow",
						label: r.value.medium
					},
					{
						from: 50,
						color: "green",
						label: r.value.high
					}
				]
			}, null, 8, ["segments"]), J(ss, {
				"entity-key": "storage_max_cell_temp",
				maximum: 40,
				segments: [
					{
						from: 0,
						color: "red",
						label: r.value.low
					},
					{
						from: 5,
						color: "green",
						label: r.value.inRange
					},
					{
						from: 32,
						color: "red",
						label: r.value.high
					}
				]
			}, null, 8, ["segments"])])) : X("", !0),
			(W(!0), G(U, null, H(a.value, (e) => (W(), G("section", {
				key: e.title,
				class: P(["general-view__card", `general-view__card--${e.title}`]),
				"aria-labelledby": `${B(n)}-${e.title}`
			}, [q("h2", { id: `${B(n)}-${e.title}` }, F(r.value[e.title]), 9, _s), q("div", vs, [(W(!0), G(U, null, H(e.entities, ([e, t]) => (W(), G(U, { key: `${e}.${t}` }, [e === "number" || e === "switch" ? (W(), K($o, {
				key: 0,
				domain: e,
				"entity-key": t,
				"confirm-switch": e === "switch" && t === "storage_switch"
			}, null, 8, [
				"domain",
				"entity-key",
				"confirm-switch"
			])) : (W(), K(ds, {
				key: 1,
				domain: e,
				"entity-key": t
			}, null, 8, ["domain", "entity-key"]))], 64))), 128))])], 10, gs))), 128))
		]));
	}
}), [["styles", [".general-view{gap:20px;min-width:0;margin-top:24px;display:grid}.general-view__gauges{grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr));gap:20px;display:grid}.general-view__card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.general-view__card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.general-view__rows{gap:16px;display:grid}.general-view__rows .entity-control{border:0;border-bottom:1px solid var(--divider-color,#e0e0e0);box-shadow:none;border-radius:0;padding:0 0 16px}.general-view__rows .entity-control:last-child{border-bottom:0;padding-bottom:0}.general-view__status{color:var(--secondary-text-color,#666);margin:0;line-height:1.6}@container sax-content (width>=860px){.general-view{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;gap:16px;margin-top:16px}.general-view__gauges{grid-column:1;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.general-view__gauges:has(>:only-child){grid-template-columns:minmax(0,1fr)}.general-view__card{padding:18px}.general-view__card--power{grid-column:1}.general-view__card--device{grid-area:1/2/span 2}:is(.general-view:not(:has(.general-view__gauges)) .general-view__card--device,.general-view:not(:has(.general-view__card--power)) .general-view__card--device){grid-row:1}:is(.general-view:has(>:only-child),.general-view:not(:has(.general-view__card--device))){grid-template-columns:minmax(0,1fr)}.general-view__card:only-child{grid-area:auto}.general-view__card h2{margin-bottom:12px;font-size:16px}.general-view__rows{gap:10px}.general-view__rows .entity-control{padding:0 0 10px}.general-view__rows .entity-control:last-child{padding-bottom:0}.general-view__status{grid-column:1/-1}}@media (max-width:600px){.general-view,.general-view__gauges{gap:16px}.general-view__card{padding:20px}}"]]]), bs = ["aria-busy"], xs = { class: "month-selection__header" }, Ss = {
	class: "month-selection__overview",
	"aria-live": "polite",
	"aria-atomic": "true"
}, Cs = { class: "month-selection__summary" }, ws = { class: "month-selection__count" }, Ts = ["aria-expanded"], Es = { class: "month-selection__feedback" }, Ds = {
	key: 0,
	role: "status"
}, Os = {
	key: 1,
	role: "status"
}, ks = {
	key: 2,
	role: "status"
}, As = {
	key: 3,
	role: "status"
}, js = {
	key: 0,
	class: "month-selection__hint"
}, Ms = { class: "month-selection__quarters" }, Ns = { class: "month-selection__options" }, Ps = {
	key: 1,
	class: "month-selection__missing"
}, Fs = { class: "month-selection__missing-target" }, Is = ["aria-describedby"], Ls = ["id"], Rs = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "MonthSelection",
	props: {
		entityKeys: { type: Array },
		alwaysExpanded: { type: Boolean }
	},
	setup(e) {
		let t = e, n = Pn(Co), r = /* @__PURE__ */ z(!1), i = Z(() => t.alwaysExpanded || r.value), a = `sax-months-${Kn()}`, o = Z(() => n?.language.value ?? "en"), s = Z(() => o.value === "de" ? {
			edit: "Ändern",
			close: "Schließen",
			allYear: "Ganzjährig",
			none: "Keine Monate ausgewählt · Ganzjährig inaktiv",
			incomplete: "Auswahl nicht vollständig bekannt",
			unknown: "Status unklar",
			unavailable: "Nicht verfügbar",
			hint: "Monate einzeln auswählen. Jede Änderung wird direkt übernommen.",
			pending: "Änderung wird an Home Assistant gesendet …",
			readOnly: "Keine Berechtigung zum Ändern",
			disconnected: "Keine Verbindung zu Home Assistant"
		} : {
			edit: "Edit",
			close: "Close",
			allYear: "All year",
			none: "No months selected · Inactive all year",
			incomplete: "Selection is not fully known",
			unknown: "Status unknown",
			unavailable: "Unavailable",
			hint: "Select months individually. Each change is applied immediately.",
			pending: "Sending change to Home Assistant …",
			readOnly: "You do not have permission to change this setting",
			disconnected: "Disconnected from Home Assistant"
		}), c = Z(() => {
			let e = new Intl.DateTimeFormat(o.value, {
				month: "long",
				timeZone: "UTC"
			});
			return Array.from({ length: 12 }, (r, i) => {
				let a = t.entityKeys.find((e) => e.endsWith(`_month_${i + 1}`)), o = a ? n?.entity("switch", a) : null, s = o?.state?.state, c = !(!o?.available || s !== "on" && s !== "off");
				return {
					index: i,
					key: a,
					entity: o,
					name: o?.metadata.name ?? e.format(new Date(Date.UTC(2024, i, 1))),
					known: c,
					selected: c && s === "on"
				};
			});
		}), l = Z(() => Array.from({ length: 4 }, (e, t) => ({
			index: t,
			name: o.value === "de" ? `${t + 1}. Quartal` : `Q${t + 1}`,
			months: c.value.slice(t * 3, t * 3 + 3)
		}))), u = Z(() => c.value.filter((e) => e.selected).length), d = Z(() => c.value.filter((e) => !e.known)), f = Z(() => {
			if (u.value === 12) return s.value.allYear;
			if (!u.value) return d.value.length ? s.value.incomplete : s.value.none;
			let e = [], t, n;
			function r() {
				t && n && e.push(t.index === n.index ? t.name : `${t.name}–${n.name}`), t = void 0, n = void 0;
			}
			for (let e of c.value) e.selected ? (t ??= e, n = e) : r();
			return r(), e.join(", ");
		}), p = Z(() => {
			let e = u.value, t = d.value.length;
			return t ? o.value === "de" ? `${e} ausgewählt · ${t} unklar` : `${e} selected · ${t} unknown` : o.value === "de" ? `${e} von 12 Monaten ausgewählt` : `${e} of 12 months selected`;
		}), m = Z(() => c.value.some((e) => e.entity?.pending)), h = Z(() => c.value.flatMap((e) => e.entity?.error ? [`${e.name}: ${e.entity.error}`] : [])), g = Z(() => c.value.filter((e) => e.known && !e.entity?.metadata.can_control));
		return (t, o) => (W(), G("div", {
			class: "month-selection",
			"aria-busy": m.value
		}, [
			q("div", xs, [q("div", Ss, [q("p", Cs, F(f.value), 1), q("p", ws, F(p.value), 1)]), e.alwaysExpanded ? X("", !0) : (W(), G("button", {
				key: 0,
				type: "button",
				class: "month-selection__toggle",
				"aria-expanded": r.value,
				"aria-controls": a,
				onClick: o[0] ||= (e) => r.value = !r.value
			}, [Y(F(r.value ? s.value.close : s.value.edit) + " ", 1), (W(), G("svg", {
				viewBox: "0 0 24 24",
				width: "18",
				height: "18",
				"aria-hidden": "true",
				class: P({ "month-selection__chevron--expanded": r.value })
			}, [...o[1] ||= [q("path", { d: "m6 9 6 6 6-6" }, null, -1)]], 2))], 8, Ts))]),
			q("div", Es, [
				i.value ? X("", !0) : (W(), G(U, { key: 0 }, [(W(!0), G(U, null, H(h.value, (e) => (W(), G("p", {
					key: e,
					class: "month-selection__error",
					role: "alert"
				}, F(e), 1))), 128)), m.value ? (W(), G("p", Ds, F(s.value.pending), 1)) : X("", !0)], 64)),
				B(n)?.connected.value ? X("", !0) : (W(), G("p", Os, F(s.value.disconnected), 1)),
				d.value.length ? (W(), G("p", ks, F(s.value.unknown) + ": " + F(d.value.map((e) => e.name).join(", ")), 1)) : X("", !0),
				g.value.length ? (W(), G("p", As, F(s.value.readOnly) + ": " + F(g.value.map((e) => e.name).join(", ")), 1)) : X("", !0)
			]),
			jn(q("div", {
				id: a,
				class: "month-selection__details"
			}, [e.alwaysExpanded ? X("", !0) : (W(), G("p", js, F(s.value.hint), 1)), q("div", Ms, [(W(!0), G(U, null, H(l.value, (e) => (W(), G("fieldset", {
				key: e.index,
				class: "month-selection__quarter"
			}, [q("legend", null, F(e.name), 1), q("div", Ns, [(W(!0), G(U, null, H(e.months, (e) => (W(), G(U, { key: e.index }, [e.entity && e.key ? (W(), K($o, {
				key: 0,
				domain: "switch",
				"entity-key": e.key,
				"month-tile": ""
			}, null, 8, ["entity-key"])) : (W(), G("div", Ps, [q("label", Fs, [q("span", null, F(e.name), 1), q("input", {
				type: "checkbox",
				role: "switch",
				disabled: "",
				indeterminate: !0,
				"aria-describedby": `${a}-${e.index}-missing`
			}, null, 8, Is)]), q("p", { id: `${a}-${e.index}-missing` }, F(s.value.unavailable), 9, Ls)]))], 64))), 128))])]))), 128))])], 512), [[ua, i.value]])
		], 8, bs));
	}
}), [["styles", [".month-selection{min-width:0}.month-selection__header{flex-wrap:wrap;justify-content:space-between;align-items:center;gap:16px;display:flex}.month-selection__overview{overflow-wrap:anywhere;flex:180px;min-width:0}.month-selection__summary{margin:0;font-size:16px;font-weight:500;line-height:1.5}.month-selection__count,.month-selection__hint{color:var(--secondary-text-color,#666);margin:4px 0 0;font-size:14px;line-height:1.5}.month-selection__toggle{border:1px solid var(--divider-color,#e0e0e0);background:var(--card-background-color,#fff);min-height:44px;color:var(--primary-text-color,#212121);font:inherit;cursor:pointer;border-radius:8px;flex-shrink:0;justify-content:center;align-items:center;gap:8px;padding:8px 12px;font-size:14px;display:inline-flex}.month-selection__toggle:hover{background:var(--secondary-background-color,#f5f5f5)}:is(.month-selection__toggle:focus-visible,.month-selection .entity-control__month-target:has(input:focus-visible)){outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.month-selection__toggle svg{fill:none;stroke:currentColor;stroke-width:2px;stroke-linecap:round;stroke-linejoin:round}.month-selection__chevron--expanded{transform:rotate(180deg)}.month-selection__details{border-top:1px solid var(--divider-color,#e0e0e0);margin-top:16px;padding-top:16px}.month-selection__hint{margin:0 0 16px}.month-selection__quarters{grid-template-columns:minmax(0,1fr);gap:16px;display:grid}.month-selection__quarter{border:0;min-width:0;margin:0;padding:0}.month-selection__quarter legend{color:var(--secondary-text-color,#666);margin-bottom:8px;padding:0;font-size:13px;font-weight:500}.month-selection__options{grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;display:grid}.month-selection .entity-control.entity-control--month,.month-selection__missing{border:1px solid var(--divider-color,#e0e0e0);background:var(--card-background-color,#fff);border-radius:8px;flex-flow:column;align-items:stretch;gap:0;min-width:0;padding:0;display:flex}.month-selection .entity-control.entity-control--selected{border-color:color-mix(in srgb, var(--primary-color,#03a9f4) 55%, var(--divider-color,#e0e0e0));background:color-mix(in srgb, var(--primary-color,#03a9f4) 12%, var(--card-background-color,#fff))}.month-selection .entity-control__month-target,.month-selection__missing-target{cursor:pointer;border-radius:7px;flex-direction:column-reverse;flex:auto;justify-content:center;align-items:center;gap:8px;min-height:44px;padding:10px 6px;display:flex}.month-selection__missing-target{cursor:not-allowed}.month-selection .entity-control__month-target:has(:disabled){cursor:not-allowed}.month-selection .entity-control__name,.month-selection__missing-target span{text-align:center;overflow-wrap:anywhere;min-width:0;max-width:100%;font-size:14px;font-weight:500;line-height:1.4}.month-selection__missing input[type=checkbox]{width:22px;height:22px;min-height:22px;accent-color:var(--primary-color,#03a9f4);flex-shrink:0;margin:0;padding:0}.month-selection .entity-control__feedback,.month-selection__missing p{overflow-wrap:anywhere;min-width:0;color:var(--secondary-text-color,#666);flex:none;margin:0;padding:0 12px 10px;font-size:13px;line-height:1.5}.month-selection__feedback{color:var(--secondary-text-color,#666);overflow-wrap:anywhere;gap:8px;margin-top:12px;font-size:14px;line-height:1.5;display:grid}.month-selection__feedback:empty{display:none}.month-selection__feedback p{margin:0}.month-selection__error{color:var(--error-color,#b71c1c)}@container sax-content (width>=600px){.month-selection__quarters{grid-template-columns:repeat(2,minmax(0,1fr))}}"]]]);
//#endregion
//#region src/time.ts
function zs(e) {
	let t = e.trim(), n = /^\d{4}$/.test(t) ? `${t.slice(0, 2)}:${t.slice(2)}` : t;
	return $(n) === null ? e : n;
}
function $(e) {
	if (!/^([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(e)) return null;
	let [t, n, r = 0] = e.split(":").map(Number);
	return t * 3600 + n * 60 + r;
}
//#endregion
//#region src/components/TimeWindowControl.vue?vue&type=script&setup=true&lang.ts
var Bs = ["aria-busy"], Vs = { class: "time-window-control__inputs" }, Hs = ["for"], Us = [
	"id",
	"name",
	"value",
	"disabled",
	"aria-invalid",
	"aria-describedby",
	"onInput",
	"onChange",
	"onBlur"
], Ws = ["disabled"], Gs = ["disabled"], Ks = ["id"], qs = ["id"], Js = ["aria-label"], Ys = [
	"disabled",
	"aria-label",
	"aria-valuenow",
	"aria-valuetext",
	"aria-describedby",
	"onKeydown",
	"onPointerdown"
], Xs = {
	class: "time-window-control__marker-label",
	"aria-hidden": "true"
}, Zs = { class: "time-window-control__duration" }, Qs = ["id"], $s = ["id"], ec = {
	key: 0,
	class: "time-window-control__error",
	role: "alert"
}, tc = {
	key: 1,
	role: "status"
}, nc = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "TimeWindowControl",
	props: { kind: { type: String } },
	setup(e) {
		let t = e, n = Pn(Co), r = Z(() => n?.entity("time", `${t.kind}_start`)), i = Z(() => n?.entity("time", `${t.kind}_end`)), a = `sax-window-${Kn()}`, o = Z(() => n?.language.value ?? "en"), s = Z(() => o.value === "de" ? {
			start: "Start",
			end: "Ende",
			unit: "Uhr",
			apply: "Übernehmen",
			cancel: "Abbrechen",
			confirmed: "Bestätigt",
			draft: "Entwurf",
			duration: "Dauer",
			nextDay: "Ende am Folgetag",
			empty: "Leeres Zeitfenster",
			hour: "Std.",
			minute: "Min.",
			second: "Sek.",
			pending: "Änderung wird an Home Assistant gesendet …",
			awaiting: "Übermittelt · Bestätigung durch Home Assistant ausstehend",
			unavailable: "Zeitfenster nicht verfügbar",
			missingValue: "Nicht verfügbar",
			incompatible: "Zeitfenster kann derzeit nicht gemeinsam geändert werden.",
			readOnly: "Keine Berechtigung zum Ändern",
			disconnected: "Keine Verbindung zu Home Assistant",
			changed: "Zeitfenster durch Home Assistant aktualisiert. Der Entwurf wurde verworfen.",
			invalid: "Bitte eine vollständige, gültige Uhrzeit eingeben (z. B. 12:30).",
			timeHint: "Uhrzeiten im 24-Stunden-Format eingeben: 12:30 oder 1230.",
			help: "Marken ziehen oder Uhrzeit eingeben. Pfeiltasten ändern um eine Minute, Bild auf und Bild ab um 15 Minuten. Pos1 und Ende wählen Tagesanfang und Tagesende.",
			startMarker: "Startmarke",
			endMarker: "Endmarke",
			timeline: "Zeitfenster auf einer 24-Stunden-Leiste"
		} : {
			start: "Start",
			end: "End",
			unit: "",
			apply: "Apply",
			cancel: "Cancel",
			confirmed: "Confirmed",
			draft: "Draft",
			duration: "Duration",
			nextDay: "Ends the next day",
			empty: "Empty time window",
			hour: "hr",
			minute: "min",
			second: "sec",
			pending: "Sending change to Home Assistant …",
			awaiting: "Sent · awaiting confirmation from Home Assistant",
			unavailable: "Time window unavailable",
			missingValue: "Unavailable",
			incompatible: "This time window cannot currently be changed as a pair.",
			readOnly: "You do not have permission to change this setting",
			disconnected: "Disconnected from Home Assistant",
			changed: "Time window updated by Home Assistant. The draft was discarded.",
			invalid: "Enter a complete, valid time (e.g. 12:30).",
			timeHint: "Enter times in 24-hour format: 12:30 or 1230.",
			help: "Drag the markers or enter a time. Arrow keys change by one minute; Page Up and Page Down by 15 minutes. Home and End select the beginning and end of the day.",
			startMarker: "Start marker",
			endMarker: "End marker",
			timeline: "Time window on a 24-hour timeline"
		}), c = /* @__PURE__ */ z(""), l = /* @__PURE__ */ z(""), u = /* @__PURE__ */ z(!1), d = /* @__PURE__ */ z(), f = /* @__PURE__ */ z(), p = /* @__PURE__ */ z(null), m = /* @__PURE__ */ z(!1), h = /* @__PURE__ */ z(!1), g = /* @__PURE__ */ z(!1), _ = 0, v = null;
		function y(e) {
			let t = (e) => String(e).padStart(2, "0");
			return `${t(Math.floor(e / 3600))}:${t(Math.floor(e / 60) % 60)}:${t(e % 60)}`;
		}
		function b(e) {
			let t = $(e);
			if (t === null) return "—";
			let n = y(t);
			return t % 60 ? n : n.slice(0, 5);
		}
		function x(e) {
			return $(e) === null ? "" : e.slice(0, 5);
		}
		let S = Z(() => r.value?.state?.state ?? ""), C = Z(() => i.value?.state?.state ?? ""), w = Z(() => !!r.value?.available && !!i.value?.available && $(S.value) !== null && $(C.value) !== null), T = Z(() => typeof r.value?.metadata.device_id == "string" && r.value.metadata.device_id.length > 0 && r.value.metadata.device_id === i.value?.metadata.device_id), E = Z(() => w.value ? `${b(S.value)} – ${b(C.value)}${s.value.unit ? ` ${s.value.unit}` : ""}` : [r.value, i.value].map((e) => e?.available && $(e.state?.state ?? "") !== null ? `${b(e.state.state)}${s.value.unit ? ` ${s.value.unit}` : ""}` : s.value.missingValue).join(" – ")), D = Z(() => $(c.value) !== null && $(l.value) !== null), O = Z(() => u.value && ($(c.value) !== $(S.value) || $(l.value) !== $(C.value))), k = Z(() => m.value || !!r.value?.pending || !!i.value?.pending), ee = Z(() => !n?.ready.value || !n.connected.value || !w.value || !T.value || !r.value?.canControl || !i.value?.canControl || k.value), A = Z(() => p.value ? `${N.value.find((e) => e.key === p.value).name}: ${s.value.invalid}` : r.value?.error || i.value?.error), te = Z(() => n?.connected.value ? w.value ? T.value ? !r.value?.canControl || !i.value?.canControl ? s.value.readOnly : k.value ? s.value.pending : h.value ? s.value.awaiting : g.value ? s.value.changed : "" : s.value.incompatible : s.value.unavailable : s.value.disconnected), ne = Z(() => u.value || !w.value ? c.value : S.value), j = Z(() => u.value || !w.value ? l.value : C.value), re = Z(() => {
			let e = $(ne.value), t = $(j.value);
			if (e === null || t === null) return "—";
			let n = (t - e + 86400) % 86400;
			if (!n) return s.value.empty;
			let r = Math.floor(n / 3600), i = Math.floor(n / 60) % 60, a = n % 60;
			return [
				r && `${r} ${s.value.hour}`,
				i && `${i} ${s.value.minute}`,
				a && `${a} ${s.value.second}`,
				t < e && s.value.nextDay
			].filter(Boolean).join(" · ");
		}), M = Z(() => {
			let e = $(ne.value), t = $(j.value);
			return e === null || t === null || e === t ? [] : (t > e ? [[e, t]] : [[e, 86400], [0, t]]).filter(([e, t]) => e !== t).map(([e, t]) => ({
				left: `${e / 864}%`,
				width: `${(t - e) / 864}%`
			}));
		}), N = Z(() => [{
			key: "start",
			value: c.value,
			name: r.value?.name || s.value.start,
			shortName: s.value.start,
			marker: s.value.startMarker
		}, {
			key: "end",
			value: l.value,
			name: i.value?.name || s.value.end,
			shortName: s.value.end,
			marker: s.value.endMarker
		}]);
		function ie() {
			let e = v;
			v = null, e?.target.hasPointerCapture?.(e.pointerId) && e.target.releasePointerCapture(e.pointerId);
		}
		V([
			() => r.value?.metadata.entity_id,
			() => i.value?.metadata.entity_id,
			S,
			C,
			w,
			T,
			() => r.value?.metadata.device_id,
			() => i.value?.metadata.device_id,
			() => t.kind
		], (e, t) => {
			let n = typeof t?.[2] == "string" ? t[2] : "", r = typeof t?.[3] == "string" ? t[3] : "", i = u.value && ($(c.value) !== $(n) || $(l.value) !== $(r)), a = k.value || h.value;
			_ += 1, ie(), m.value = !1, h.value = !1, u.value = !1, p.value = null, g.value = !!t?.length && i && !a && w.value, c.value = w.value ? x(S.value) : "", l.value = w.value ? x(C.value) : "";
		}, {
			immediate: !0,
			flush: "sync"
		}), V(ee, (e) => {
			e && ie();
		}, { flush: "sync" }), cr(ie);
		function ae(e, t) {
			ee.value || (e === "start" ? c.value = t : l.value = t, p.value === e && (p.value = null), u.value = !0, h.value = !1, g.value = !1);
		}
		function oe(e, t) {
			let n = t.target;
			ae(e, n.value);
		}
		function ce(e) {
			let t = zs(e);
			return $(t) === null ? e : x(t);
		}
		function le(e) {
			let t = ["start", "end"].map((e) => ({
				boundary: e,
				input: f.value?.querySelector(`[name="${e}"]`)
			}));
			for (let { boundary: n, input: r } of t) {
				if (!r) continue;
				let t = n === "start" ? c.value : l.value, i = !e || n === e ? ce(r.value) : r.value;
				(r.value !== t || i !== t) && ae(n, i), r.value = i;
			}
		}
		function ue(e) {
			ee.value || le(e);
		}
		function de(e, t) {
			if (ee.value) return;
			let n = $(e === "start" ? c.value : l.value);
			if (n === null) return;
			let r = {
				ArrowRight: 60,
				ArrowUp: 60,
				ArrowLeft: -60,
				ArrowDown: -60,
				PageUp: 900,
				PageDown: -900
			};
			(t.key in r || t.key === "Home" || t.key === "End") && (t.preventDefault(), ae(e, x(y(t.key === "Home" ? 0 : t.key === "End" ? 86340 : Math.max(0, Math.min(86340, Math.floor(n / 60) * 60 + r[t.key]))))));
		}
		function fe(e) {
			if (!v || v.pointerId !== e.pointerId || ee.value || !d.value) return;
			let t = d.value.getBoundingClientRect();
			if (t.width <= 0 || !v.moved && e.clientX === v.originX) return;
			let n = Math.max(0, Math.min(1439, Math.round(v.originSeconds / 60 + (e.clientX - v.originX) / t.width * 1440)));
			v.moved = !0, ae(v.boundary, y(n * 60).slice(0, 5));
		}
		function pe(e, t) {
			if (ee.value || !D.value || t.button !== 0 || t.isPrimary === !1) return;
			let n = t.currentTarget;
			n.focus(), v = {
				boundary: e,
				pointerId: t.pointerId,
				target: n,
				moved: !1,
				originX: t.clientX,
				originSeconds: $(e === "start" ? c.value : l.value)
			}, n.setPointerCapture?.(t.pointerId), t.preventDefault();
		}
		function me(e) {
			v?.pointerId === e.pointerId && (v.moved && fe(e), ie());
		}
		function he() {
			if (!k.value) {
				ie(), u.value = !1, p.value = null, g.value = !1, c.value = w.value ? x(S.value) : "", l.value = w.value ? x(C.value) : "";
				for (let e of N.value) {
					let r = f.value?.querySelector(`[name="${e.key}"]`);
					r && (r.value = e.value), n?.clearControlError("time", `${t.kind}_${e.key}`);
				}
			}
		}
		async function ge() {
			if (!n || ee.value) return;
			if (le(), p.value = $(c.value) === null ? "start" : $(l.value) === null ? "end" : null, p.value) {
				f.value?.querySelector(`[name="${p.value}"]`)?.focus();
				return;
			}
			if (!O.value) return;
			let e = _;
			m.value = !0, g.value = !1;
			let r = await n.performTimeWindow(t.kind, `${c.value}:00`, `${l.value}:00`);
			e === _ && (m.value = !1, h.value = r && O.value);
		}
		return (e, t) => r.value || i.value ? (W(), G("form", {
			key: 0,
			ref_key: "form",
			ref: f,
			class: "time-window-control",
			"aria-busy": k.value,
			onSubmit: io(ge, ["prevent"])
		}, [
			q("div", Vs, [(W(!0), G(U, null, H(N.value, (e) => (W(), G("label", {
				key: e.key,
				for: `${a}-${e.key}`,
				class: "time-window-control__field"
			}, [q("span", null, [Y(F(e.name), 1), s.value.unit ? (W(), G(U, { key: 0 }, [Y(" (" + F(s.value.unit) + ")", 1)], 64)) : X("", !0)]), q("input", {
				id: `${a}-${e.key}`,
				name: e.key,
				type: "text",
				inputmode: "numeric",
				autocomplete: "off",
				placeholder: "HH:MM",
				value: e.value,
				disabled: ee.value,
				"aria-invalid": p.value === e.key,
				"aria-describedby": `${a}-time-hint ${a}-confirmed ${a}-status`,
				onInput: (t) => oe(e.key, t),
				onChange: (t) => ue(e.key),
				onBlur: (t) => ue(e.key)
			}, null, 40, Us)], 8, Hs))), 128)), J(No, null, {
				default: An(() => [q("button", {
					class: "time-window-control__apply",
					type: "submit",
					disabled: ee.value
				}, F(s.value.apply), 9, Ws), q("button", {
					class: "time-window-control__cancel",
					type: "button",
					disabled: k.value,
					onClick: he
				}, F(s.value.cancel), 9, Gs)]),
				_: 1
			})]),
			q("p", {
				id: `${a}-time-hint`,
				class: "time-window-control__hint"
			}, F(s.value.timeHint), 9, Ks),
			q("p", {
				id: `${a}-confirmed`,
				class: "time-window-control__confirmed"
			}, F(s.value.confirmed) + ": " + F(E.value), 9, qs),
			q("div", {
				class: "time-window-control__timeline",
				"aria-label": s.value.timeline,
				role: "group"
			}, [q("div", {
				ref_key: "rail",
				ref: d,
				class: P(["time-window-control__rail", { "time-window-control__rail--draft": O.value }])
			}, [(W(!0), G(U, null, H(M.value, (e, t) => (W(), G("span", {
				key: t,
				class: "time-window-control__segment",
				style: se(e)
			}, null, 4))), 128))], 2), (W(!0), G(U, null, H(N.value, (e) => (W(), G("button", {
				key: e.key,
				type: "button",
				role: "slider",
				class: P(["time-window-control__handle", `time-window-control__handle--${e.key}`]),
				style: se({ left: `${(B($)(e.value) ?? 0) / 864}%` }),
				disabled: ee.value || !D.value,
				"aria-label": e.marker,
				"aria-valuemin": "0",
				"aria-valuemax": "86340",
				"aria-valuenow": B($)(e.value) ?? 0,
				"aria-valuetext": `${b(e.value)}${s.value.unit ? ` ${s.value.unit}` : ""}`,
				"aria-describedby": `${a}-help ${a}-confirmed`,
				"aria-orientation": "horizontal",
				onKeydown: (t) => de(e.key, t),
				onPointerdown: (t) => pe(e.key, t),
				onPointermove: fe,
				onPointerup: me,
				onPointercancel: ie,
				onLostpointercapture: ie
			}, [q("span", Xs, F(e.shortName), 1), t[0] ||= q("span", {
				class: "time-window-control__marker-dot",
				"aria-hidden": "true"
			}, null, -1)], 46, Ys))), 128))], 8, Js),
			t[1] ||= q("div", {
				class: "time-window-control__ticks",
				"aria-hidden": "true"
			}, [
				q("span", null, "00"),
				q("span", null, "06"),
				q("span", null, "12"),
				q("span", null, "18"),
				q("span", null, "24")
			], -1),
			q("p", Zs, [q("span", null, F(O.value ? s.value.draft : s.value.duration) + ":", 1), Y(" " + F(re.value), 1)]),
			q("p", {
				id: `${a}-help`,
				class: "time-window-control__sr-only"
			}, F(s.value.help), 9, Qs),
			q("div", {
				id: `${a}-status`,
				class: "time-window-control__feedback"
			}, [A.value ? (W(), G("p", ec, F(A.value), 1)) : te.value ? (W(), G("p", tc, F(te.value), 1)) : X("", !0)], 8, $s)
		], 40, Bs)) : X("", !0);
	}
}), [["styles", [".time-window-control{min-width:0;color:var(--primary-text-color,#212121)}.time-window-control__inputs{flex-wrap:wrap;align-items:end;gap:10px;display:flex}.time-window-control__field{flex:136px;gap:5px;min-width:0;font-size:14px;display:grid}.time-window-control__field input,.time-window-control__apply,.time-window-control__cancel{box-sizing:border-box;border:1px solid var(--divider-color,#767676);min-width:0;max-width:100%;min-height:44px;color:inherit;background:var(--card-background-color,#fff);font:inherit;border-radius:6px;padding:8px 10px;font-size:16px}.time-window-control__field input{width:100%}.time-window-control__field input[aria-invalid=true]{border-color:var(--error-color,#db4437)}.time-window-control__apply,.time-window-control__cancel{border-color:var(--primary-color,#03a9f4);cursor:pointer;flex:none;padding-inline:7px}.time-window-control__hint,.time-window-control__confirmed,.time-window-control__duration{color:var(--secondary-text-color,#666);overflow-wrap:anywhere;margin:9px 0 0;font-size:14px;line-height:1.5}.time-window-control__timeline{height:94px;margin:6px 22px 0;position:relative}.time-window-control__rail{background:var(--divider-color,#ddd);border-radius:3px;height:6px;position:absolute;top:44px;left:0;right:0;overflow:hidden}.time-window-control__segment{background:var(--primary-color,#03a9f4);height:100%;position:absolute}.time-window-control__rail--draft .time-window-control__segment{background-image:repeating-linear-gradient(135deg,#0000 0 5px,#ffffff3d 5px 8px)}.time-window-control__handle{width:44px;height:44px;min-height:0;color:inherit;font:inherit;cursor:ew-resize;touch-action:none;background:0 0;border:0;border-radius:6px;padding:0;display:block;position:absolute;transform:translate(-50%)}.time-window-control__handle--start{top:0}.time-window-control__handle--end{top:50px}.time-window-control__marker-label{white-space:nowrap;width:max-content;font-size:12px;line-height:16px;position:absolute;left:50%;transform:translate(-50%)}.time-window-control__handle--start .time-window-control__marker-label{top:0}.time-window-control__handle--end .time-window-control__marker-label{bottom:0}.time-window-control__marker-dot{box-sizing:border-box;border:2px solid var(--primary-color,#03a9f4);background:var(--card-background-color,#fff);border-radius:50%;width:18px;height:18px;position:absolute;left:13px}.time-window-control__handle--start .time-window-control__marker-dot{bottom:3px}.time-window-control__handle--end .time-window-control__marker-dot{top:3px}.time-window-control__marker-dot:after{content:\"\";background:var(--primary-color,#03a9f4);width:2px;height:6px;position:absolute;left:6px}.time-window-control__handle--start .time-window-control__marker-dot:after{top:14px}.time-window-control__handle--end .time-window-control__marker-dot:after{bottom:14px}.time-window-control__ticks{height:18px;color:var(--secondary-text-color,#666);margin:0 22px;font-size:12px;position:relative}.time-window-control__ticks span{white-space:nowrap;position:absolute;left:0}.time-window-control__ticks span:nth-child(2){left:25%;transform:translate(-50%)}.time-window-control__ticks span:nth-child(3){left:50%;transform:translate(-50%)}.time-window-control__ticks span:nth-child(4){left:75%;transform:translate(-50%)}.time-window-control__ticks span:last-child{left:auto;right:0}.time-window-control :disabled{opacity:.6;cursor:not-allowed}.time-window-control input:focus-visible,.time-window-control button:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.time-window-control__feedback{color:var(--secondary-text-color,#666);overflow-wrap:anywhere;margin-top:6px;font-size:14px;line-height:1.5}.time-window-control__feedback:empty{display:none}.time-window-control__feedback p{margin:0}.time-window-control__error{color:var(--error-color,#b71c1c)}.time-window-control__sr-only{clip-path:inset(50%);white-space:nowrap;border:0;width:1px;height:1px;margin:-1px;padding:0;position:absolute;overflow:hidden}"]]]), rc = { class: "charging-view" }, ic = {
	key: 0,
	class: "charging-view__status",
	role: "status"
}, ac = {
	key: 1,
	class: "charging-view__status",
	role: "status"
}, oc = {
	key: 3,
	class: "charging-view__cards"
}, sc = ["aria-labelledby"], cc = ["id"], lc = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "ChargingLayout",
	props: {
		switchKey: { type: String },
		cards: { type: Array }
	},
	setup(e) {
		let t = e, n = Pn(Co), r = Kn(), i = Z(() => n?.language.value ?? "en"), a = Z(() => t.cards.map((e) => {
			let r = e.entities.filter(([e, t]) => n?.entity(e, t)), i = e.layout === "months" && (r.length || n?.entity("switch", t.switchKey)) ? e.entities : r;
			return {
				...e,
				showTimeWindow: !!(e.timeWindow && i.some(([e]) => e === "time")),
				entities: i.filter(([t]) => !e.timeWindow || t !== "time")
			};
		}).filter((e) => e.entities.length || e.showTimeWindow)), o = Z(() => !!n?.entity("switch", t.switchKey)), s = Z(() => i.value === "de" ? {
			loading: "Die Entitäten werden geladen …",
			empty: "Für diese Ansicht sind keine Entitäten verfügbar."
		} : {
			loading: "Loading entities …",
			empty: "No entities are available for this view."
		});
		return (t, c) => (W(), G("div", rc, [
			!B(n)?.ready.value && !B(n)?.error.value ? (W(), G("p", ic, F(s.value.loading), 1)) : B(n)?.ready.value && !o.value && !a.value.length ? (W(), G("p", ac, F(s.value.empty), 1)) : X("", !0),
			o.value ? (W(), K($o, {
				key: 2,
				domain: "switch",
				"entity-key": e.switchKey
			}, null, 8, ["entity-key"])) : X("", !0),
			a.value.length ? (W(), G("div", oc, [(W(!0), G(U, null, H(a.value, (e) => (W(), G("section", {
				key: e.key,
				class: "charging-view__card",
				"aria-labelledby": `${B(r)}-${e.key}`
			}, [
				q("h2", { id: `${B(r)}-${e.key}` }, F(e.title[i.value]), 9, cc),
				e.showTimeWindow && e.timeWindow ? (W(), K(nc, {
					key: 0,
					kind: e.timeWindow
				}, null, 8, ["kind"])) : X("", !0),
				ur(t.$slots, `${e.key}-settings`),
				e.entities.length ? (W(), G("div", {
					key: 1,
					class: P(["charging-view__rows", {
						"charging-view__rows--columns": e.layout === "columns",
						"charging-view__rows--months": e.layout === "months"
					}])
				}, [e.layout === "months" ? (W(), K(Rs, {
					key: 0,
					"entity-keys": e.entities.map(([, e]) => e)
				}, null, 8, ["entity-keys"])) : (W(!0), G(U, { key: 1 }, H(e.entities, ([e, t]) => (W(), G(U, { key: `${e}.${t}` }, [e === "switch" || e === "number" || e === "time" || e === "select" ? (W(), K($o, {
					key: 0,
					domain: e,
					"entity-key": t
				}, null, 8, ["domain", "entity-key"])) : (W(), K(ds, {
					key: 1,
					domain: e,
					"entity-key": t
				}, null, 8, ["domain", "entity-key"]))], 64))), 128))], 2)) : X("", !0)
			], 8, sc))), 128))])) : X("", !0)
		]));
	}
}), [["styles", [".charging-view{gap:20px;min-width:0;margin-top:24px;display:grid}.charging-view__cards{align-content:start;gap:20px;min-width:0;display:grid}.charging-view__card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.charging-view__card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.charging-view__rows{gap:16px;display:grid}.charging-view__card>.time-window-control+.charging-view__rows{border-top:1px solid var(--divider-color,#e0e0e0);margin-top:20px;padding-top:16px}.charging-view__rows>.entity-control{border:0;border-bottom:1px solid var(--divider-color,#e0e0e0);box-shadow:none;border-radius:0;padding:0 0 16px}.charging-view__rows>.entity-control:last-child{border-bottom:0;padding-bottom:0}.charging-view__status{color:var(--secondary-text-color,#666);margin:0;line-height:1.6}@media (max-width:600px){.charging-view,.charging-view__cards{gap:16px}.charging-view__card{padding:20px}}@container sax-content (width>=860px){.charging-view{gap:14px;margin-top:16px}.charging-view__cards{align-items:start;gap:16px}.charging-view__card{padding:18px}.charging-view__card h2{margin-bottom:12px;font-size:16px}.charging-view__rows{gap:12px}.charging-view__rows>.entity-control{gap:8px 12px;padding-bottom:12px}.charging-view__rows>.entity-control:last-child{padding-bottom:0}.charging-view__rows>.entity-control .entity-control__description{flex-basis:120px}.charging-view__rows--columns{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;column-gap:24px}.charging-view__rows--columns>:last-child:nth-child(odd){grid-column:1/-1}.charging-view__rows--columns .entity-value{min-height:44px;padding-block:8px}}"]]]), uc = { class: "sensor-picker" }, dc = [
	"value",
	"disabled",
	"name",
	"aria-invalid",
	"aria-describedby"
], fc = { value: "" }, pc = ["value"], mc = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "SensorPicker",
	props: {
		hass: { type: Object },
		modelValue: { type: [String, null] },
		label: { type: String },
		disabled: { type: Boolean },
		name: { type: String },
		invalid: { type: Boolean },
		describedBy: { type: String }
	},
	emits: ["update:modelValue"],
	setup(e, { emit: t }) {
		let n = e, r = t, i = Z(() => {
			let e = Object.values(n.hass?.states ?? {}).filter((e) => e.entity_id.startsWith("sensor.")).map((e) => ({
				id: e.entity_id,
				name: typeof e.attributes.friendly_name == "string" ? e.attributes.friendly_name : e.entity_id
			}));
			return n.modelValue && !e.some((e) => e.id === n.modelValue) && e.push({
				id: n.modelValue,
				name: n.modelValue
			}), e.sort((e, t) => e.name.localeCompare(t.name));
		});
		return (t, n) => (W(), G("label", uc, [Y(F(e.label), 1), q("select", {
			value: e.modelValue ?? "",
			disabled: e.disabled,
			name: e.name,
			"aria-invalid": e.invalid || void 0,
			"aria-describedby": e.describedBy,
			onChange: n[0] ||= (e) => r("update:modelValue", e.target.value || null)
		}, [q("option", fc, F(e.hass?.language?.startsWith("de") ? "Nicht konfiguriert" : "Not configured"), 1), (W(!0), G(U, null, H(i.value, (e) => (W(), G("option", {
			key: e.id,
			value: e.id
		}, F(e.name), 9, pc))), 128))], 40, dc)]));
	}
}), [["styles", [".sensor-picker{flex-direction:column;gap:6px;min-width:0;font-size:14px;display:flex}.sensor-picker select{width:100%;min-width:0;max-width:100%;min-height:44px;font:inherit;color:var(--primary-text-color,#222);background:var(--card-background-color,#fff);border:1px solid var(--divider-color,#ccc);border-radius:6px;padding:10px}"]]]), hc = ["aria-labelledby", "aria-busy"], gc = { class: "grid-serving-source__header" }, _c = ["id"], vc = {
	key: 0,
	class: "grid-serving-source__confirmed"
}, yc = ["disabled"], bc = ["id"], xc = { key: 0 }, Sc = { key: 1 }, Cc = {
	key: 2,
	role: "status"
}, wc = {
	key: 3,
	role: "status"
}, Tc = ["id"], Ec = ["disabled"], Dc = ["disabled"], Oc = ["disabled"], kc = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "GridServingForecastSource",
	props: { hass: { type: Object } },
	setup(e) {
		let t = e, n = Pn(Co), r = `grid-serving-source-${Kn()}`, i = /* @__PURE__ */ z(), a = /* @__PURE__ */ z(), o = /* @__PURE__ */ z(null), s = /* @__PURE__ */ z(null), c = /* @__PURE__ */ z(""), l = /* @__PURE__ */ z(!1), u = /* @__PURE__ */ z(null), d = /* @__PURE__ */ z(null), f = /* @__PURE__ */ z(!1), p = !1, m = !1;
		cr(() => {
			p = !0;
		});
		let h = Z(() => n?.connected.value ?? !1), g = Z(() => n?.language.value === "de" ? {
			title: "Solarprognose für die Ladepause",
			hint: "Wähle einen Energiesensor für den heute noch erwarteten Solarertrag (Wh, kWh oder MWh). Liegt der Wert unter der Mindest-PV-Prognose, greift die Ladepause nicht. Bei einer Mindest-PV-Prognose von 0 kWh wird diese Bedingung nicht geprüft.",
			source: "PV-Sensor (heute verbleibend)",
			none: "Keine Quelle ausgewählt",
			missing: "Ohne Quelle greift die Ladepause bei einer Mindest-PV-Prognose über 0 kWh nicht.",
			readonly: "Nur Administratoren können die Quelle ändern.",
			edit: "Bearbeiten",
			save: "Übernehmen",
			cancel: "Abbrechen",
			loading: "Auswahl wird geladen …",
			saving: "Auswahl wird gespeichert …",
			saved: "Quelle gespeichert. Die Ladepause wird anhand der neuen Prognose geprüft.",
			reload: "Aktuelle Auswahl laden",
			conflict: "Die Quelle wurde zwischenzeitlich geändert. Dein Entwurf bleibt erhalten. Lade die aktuelle Auswahl, bevor du erneut bearbeitest.",
			disconnected: "Keine Verbindung zu Home Assistant. Dein Entwurf bleibt erhalten.",
			invalid_sensor: "Dieser Sensor ist nicht mehr verfügbar. Wähle einen vorhandenen Energiesensor.",
			invalid_unit: "Wähle einen Energiesensor in Wh, kWh oder MWh. Ein Leistungssensor in W oder kW ist ungeeignet.",
			forbidden: "Du bist nicht berechtigt, diese Quelle zu bearbeiten.",
			failed: "Die Auswahl konnte nicht übernommen werden. Dein Entwurf bleibt erhalten. Bitte erneut versuchen."
		} : {
			title: "Solar forecast for the charging pause",
			hint: "Choose an energy sensor for the solar yield still expected today (Wh, kWh or MWh). Below the minimum PV forecast, the charging pause does not apply. A minimum of 0 kWh skips this condition.",
			source: "PV sensor (remaining today)",
			none: "No source selected",
			missing: "Without a source, the charging pause does not apply when the minimum PV forecast is above 0 kWh.",
			readonly: "Only administrators can change the source.",
			edit: "Edit",
			save: "Apply",
			cancel: "Cancel",
			loading: "Loading selection …",
			saving: "Saving selection …",
			saved: "Source saved. The charging pause is checked against the new forecast.",
			reload: "Load current selection",
			conflict: "The source changed elsewhere. Your draft is preserved. Load the current selection before editing again.",
			disconnected: "Disconnected from Home Assistant. Your draft is preserved.",
			invalid_sensor: "This sensor is no longer available. Select an existing energy sensor.",
			invalid_unit: "Choose an energy sensor in Wh, kWh or MWh. Power sensors in W or kW are not suitable.",
			forbidden: "You do not have permission to edit this source.",
			failed: "The selection could not be saved. Your draft is preserved. Please try again."
		}), _ = Z(() => d.value ? g.value[d.value] ?? g.value.failed : null), v = Z(() => {
			let e = o.value?.pv_sensor;
			if (!e) return g.value.none;
			let n = t.hass?.states[e]?.attributes.friendly_name;
			return typeof n == "string" ? n : e;
		}), y = Z(() => t.hass ? {
			...t.hass,
			states: Object.fromEntries(Object.entries(t.hass.states).filter(([, e]) => e.entity_id !== n?.entity("sensor", "grid_serving_forecast")?.metadata.entity_id && [
				"wh",
				"kwh",
				"mwh"
			].includes(String(e.attributes.unit_of_measurement ?? "").trim().toLowerCase())))
		} : void 0);
		function b(e) {
			d.value = e && typeof e == "object" && "code" in e ? String(e.code) : "failed", d.value === "forbidden" && o.value && (o.value = {
				...o.value,
				can_edit: !1
			});
		}
		async function x(e = !1) {
			if (n && !u.value && h.value) {
				u.value = "loading", d.value = null, e && (f.value = !1);
				try {
					let t = await n.loadGridServingForecast();
					if (p || m) return;
					o.value?.revision !== t.revision && (f.value = !1), o.value = t, !e && l.value && t.revision !== c.value && (d.value = "conflict"), e && t.can_edit ? (s.value = t.pv_sensor, c.value = t.revision, l.value = !0) : e && (l.value = !1);
				} catch (e) {
					p || b(e);
				} finally {
					p || (u.value = null, m ? (m = !1, x(e)) : e && l.value ? (await vn(), i.value?.querySelector("select")?.focus()) : f.value && !l.value && (await vn(), a.value?.focus()));
				}
			}
		}
		async function S() {
			if (n && !u.value && l.value && o.value?.can_edit && d.value !== "conflict") {
				if (!h.value) {
					d.value = "disconnected";
					return;
				}
				u.value = "saving", d.value = null, f.value = !1;
				try {
					let e = await n.saveGridServingForecast({
						pv_sensor: s.value,
						revision: c.value
					});
					if (p || m && n.entity("sensor", "grid_serving_forecast")?.state?.attributes.source_entity_id !== e.pv_sensor) return;
					o.value = e, l.value = !1, f.value = !0;
				} catch (e) {
					p || b(e);
				} finally {
					p || (u.value = null, m ? (m = !1, x()) : f.value && (await vn(), a.value?.focus()));
				}
			}
		}
		async function C() {
			u.value || (l.value = !1, d.value = null, await vn(), a.value?.focus());
		}
		function w() {
			u.value ? m = !0 : x();
		}
		return V([h, () => n?.ready.value], ([e, t]) => {
			e && t && (!l.value || u.value) && w();
		}, { immediate: !0 }), V(() => n?.entity("sensor", "grid_serving_forecast")?.state?.attributes.source_entity_id, (e, t) => {
			e !== t && n?.ready.value && w();
		}), (e, t) => (W(), G("section", {
			ref_key: "section",
			ref: i,
			class: "grid-serving-source",
			"aria-labelledby": `${r}-title`,
			"aria-busy": !!u.value
		}, [
			q("div", gc, [q("div", null, [q("h3", { id: `${r}-title` }, F(g.value.title), 9, _c), o.value ? (W(), G("p", vc, F(v.value), 1)) : X("", !0)]), o.value?.can_edit && !l.value ? (W(), G("button", {
				key: 0,
				ref_key: "editButton",
				ref: a,
				type: "button",
				disabled: !!u.value || !h.value,
				onClick: t[0] ||= (e) => x(!0)
			}, F(g.value.edit), 9, yc)) : X("", !0)]),
			q("p", { id: `${r}-hint` }, F(g.value.hint), 9, bc),
			o.value && !o.value.pv_sensor && !l.value ? (W(), G("p", xc, F(g.value.missing), 1)) : X("", !0),
			o.value && !o.value.can_edit ? (W(), G("p", Sc, F(g.value.readonly), 1)) : X("", !0),
			u.value ? (W(), G("p", Cc, F(u.value === "loading" ? g.value.loading : g.value.saving), 1)) : X("", !0),
			f.value ? (W(), G("p", wc, F(g.value.saved), 1)) : X("", !0),
			_.value ? (W(), G("p", {
				key: 4,
				id: `${r}-error`,
				class: "grid-serving-source__error",
				role: "alert"
			}, F(_.value), 9, Tc)) : X("", !0),
			d.value === "conflict" || !o.value && _.value ? (W(), G("button", {
				key: 5,
				type: "button",
				disabled: !!u.value || !h.value,
				onClick: t[1] ||= (e) => x(l.value)
			}, F(g.value.reload), 9, Ec)) : X("", !0),
			l.value ? (W(), G("form", {
				key: 6,
				onSubmit: io(S, ["prevent"])
			}, [J(mc, {
				hass: y.value,
				modelValue: s.value,
				"onUpdate:modelValue": t[2] ||= (e) => s.value = e,
				label: g.value.source,
				name: "grid_serving_pv_sensor",
				disabled: !!u.value || !h.value || !o.value?.can_edit,
				invalid: d.value === "invalid_sensor" || d.value === "invalid_unit",
				"described-by": `${r}-hint${_.value ? ` ${r}-error` : ""}`
			}, null, 8, [
				"hass",
				"modelValue",
				"label",
				"disabled",
				"invalid",
				"described-by"
			]), J(No, null, {
				default: An(() => [q("button", {
					type: "submit",
					disabled: !!u.value || !h.value || !o.value?.can_edit || d.value === "conflict"
				}, F(g.value.save), 9, Dc), q("button", {
					type: "button",
					disabled: !!u.value,
					onClick: C
				}, F(g.value.cancel), 9, Oc)]),
				_: 1
			})], 32)) : X("", !0)
		], 8, hc));
	}
}), [["styles", [".grid-serving-source{border-block:1px solid var(--divider-color,#ddd);gap:12px;min-width:0;margin-block:20px;padding-block:16px;display:grid}.grid-serving-source__header{justify-content:space-between;align-items:start;gap:12px;display:flex}.grid-serving-source__header>div{min-width:0}.grid-serving-source h3{margin:0 0 6px;font-size:16px;font-weight:500}.grid-serving-source p{color:var(--secondary-text-color,#666);overflow-wrap:anywhere;margin:0;font-size:14px;line-height:1.6}.grid-serving-source .grid-serving-source__confirmed{color:var(--primary-text-color,#222)}.grid-serving-source .grid-serving-source__error{color:var(--error-color,#b00020)}.grid-serving-source form{gap:12px;display:grid}.grid-serving-source button{border:1px solid var(--divider-color,#ccc);min-height:44px;color:var(--primary-color,#0077a3);background:var(--card-background-color,#fff);font:inherit;cursor:pointer;border-radius:6px;padding:8px 10px}.grid-serving-source button:disabled{opacity:.5;cursor:default}.grid-serving-source button:focus-visible{outline:2px solid var(--primary-color,#0077a3);outline-offset:2px}"]]]), Ac = /* @__PURE__ */ Gn({
	__name: "GridServingView",
	props: { hass: { type: Object } },
	setup(e) {
		let t = [{
			key: "pause",
			layout: "columns",
			timeWindow: "grid_serving",
			title: {
				de: "Ladepause",
				en: "Charging pause"
			},
			entities: [
				["time", "grid_serving_start"],
				["time", "grid_serving_end"],
				["sensor", "grid_serving_forecast"],
				["number", "grid_serving_forecast_threshold"],
				["sensor", "grid_serving_pause_status"]
			]
		}, {
			key: "months",
			layout: "months",
			title: {
				de: "Aktive Monate",
				en: "Active months"
			},
			entities: Array.from({ length: 12 }, (e, t) => ["switch", `grid_serving_month_${t + 1}`])
		}];
		return (n, r) => (W(), K(lc, {
			"switch-key": "grid_serving_enabled",
			cards: t
		}, {
			"pause-settings": An(() => [J(kc, { hass: e.hass }, null, 8, ["hass"])]),
			_: 1
		}));
	}
}), jc = ["aria-labelledby"], Mc = ["id"], Nc = { key: 0 }, Pc = { key: 1 }, Fc = { key: 3 }, Ic = { key: 4 }, Lc = {
	key: 5,
	class: "charge-plan__target"
}, Rc = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "ChargePlan",
	props: {
		hass: { type: Object },
		automatic: { type: Boolean }
	},
	setup(e) {
		let t = e, n = Pn(Co), r = Kn(), i = Z(() => n?.language.value === "de"), a = Z(() => n?.entity("sensor", "bridge_charge_plan")), o = Z(() => n?.entity("switch", "bridge_charge_enabled")), s = Z(() => a.value?.state?.attributes ?? {}), c = Z(() => {
			let e = n?.tariff.value?.fixed_time_charging;
			return !e?.enabled || !e.start || $(e.start) === null ? null : e.start.endsWith(":00") && e.start.length === 8 ? e.start.slice(0, 5) : e.start;
		}), l = Z(() => c.value ? i.value ? `Feste Startzeit ${c.value} Uhr` : `Scheduled start ${c.value}` : null), u = Z(() => n?.entity("sensor", "discharge_forecast")), d = Z(() => {
			if (!o.value?.available || o.value.state?.state !== "on" || m.value) return null;
			switch (o.value?.state?.attributes.configuration_error) {
				case "bridge_pv_start_required": return i.value ? "Unter „Preise & Zeiten“ eine PV-Prognosequelle auswählen." : "Select a solar forecast source under “Prices & times”.";
				case "bridge_tariff_required": return i.value ? "Unter „Preise & Zeiten“ einen zeitvariablen Tarif einrichten." : "Configure a time-of-use tariff under “Prices & times”.";
				default: return null;
			}
		}), f = Z(() => i.value ? {
			title: "Ladeplanung",
			noCharge: "Keine Ladung nötig",
			chargeNeeded: "Ladung voraussichtlich nötig",
			charging: "Ladung läuft",
			demandUnknown: "Ladebedarf offen",
			conflict: "Reichweite und Ladeplan weichen ab",
			unavailable: "Planstatus unbekannt",
			postChargeWaiting: "Nach Ladeende wird der Bedarf mit neuen Verbrauchsdaten geprüft.",
			incomplete: "Ladezeiten noch unvollständig.",
			waiting: "Gültige Planungsdaten fehlen.",
			paused: "Netzladung pausiert.",
			complete: "Netzladung beendet.",
			completionPending: "Netzladung beendet. Fehlmenge ohne aktuelle Batteriedaten noch unbekannt.",
			unconfirmed: "Ladefluss noch unbestätigt.",
			noWindow: "Kein nutzbares Ladefenster im Niedertarif.",
			charge: "Netzladung",
			partial: "Teilladung",
			lowTariff: "im Niedertarif",
			firstTariff: "im ersten nutzbaren Niedertarif",
			emptyBattery: "Akku bei 0 %."
		} : {
			title: "Charging plan",
			noCharge: "No charging needed",
			chargeNeeded: "Charging likely needed",
			charging: "Charging in progress",
			demandUnknown: "Charging need unknown",
			conflict: "Battery forecast and plan disagree",
			unavailable: "Plan status unavailable",
			postChargeWaiting: "Demand after charging is assessed from fresh consumption readings.",
			incomplete: "Charging times are incomplete.",
			waiting: "Valid planning data is missing.",
			paused: "Grid charging paused.",
			complete: "Grid charging ended.",
			completionPending: "Grid charging ended. The shortfall is unknown until new battery readings arrive.",
			unconfirmed: "Charging power not yet confirmed.",
			noWindow: "No usable low-tariff charging window.",
			charge: "Grid charge",
			partial: "Partial charge",
			lowTariff: "at low tariff",
			firstTariff: "in the first available low-tariff window",
			emptyBattery: "Battery at 0%."
		}), p = Z(() => a.value?.available ? a.value.state?.state : "unavailable"), m = Z(() => ["charging", "off"].includes(p.value ?? "") && s.value.charging_active === !0), h = Z(() => {
			let e = n?.tariff.value;
			if (!t.automatic || e?.tariff_type !== "time_of_use" || e.fixed_time_charging?.enabled || p.value !== "off" || !o.value?.available || o.value.state?.state !== "off") return null;
			let r = n?.entity("number", "timed_charge_min_soc"), a = r?.available ? Q(r.state?.state) : null;
			if (a === null || !Number.isInteger(a) || a < 0 || a > 100) return null;
			let c = b(s.value.empty_battery_start);
			return c ? i.value ? `Akku bei 0 % – Ladestart zum Niedertarifbeginn am ${c} Uhr` : `Battery at 0% – charging planned for the start of low tariff on ${c}` : s.value.empty_battery_start_due === !0 ? i.value ? "Akku bei 0 % – Netzladung im Niedertarif freigegeben" : "Battery at 0% – grid charging permitted during this low-tariff period" : a === 0 ? i.value ? "Start im Niedertarif bei 0 % Akkustand" : "Starts during low-tariff hours at 0% battery charge" : i.value ? `Start im Niedertarif bei unter ${a} % Akkustand` : `Low-tariff charging below ${a}% battery charge`;
		}), g = Z(() => i.value ? {
			pv_start_missing: "Die PV-Prognose bestätigt noch keine 30 Minuten mit genug Solarstrom für den Verbrauch. Quelle unter „Preise & Zeiten“ prüfen.",
			consumption_missing: "Für die Prognose ist mindestens eine Minute Verbrauchsmessung nötig.",
			measurements_missing: "Aktuelle Batteriemesswerte fehlen.",
			calibration: "Batteriekalibrierung hat Vorrang.",
			pv_surplus: "PV-Überschuss vorhanden.",
			manual_charge: "Manuelle Ladung hat Vorrang.",
			soc_limit: "SOC-Grenze erreicht."
		} : {
			pv_start_missing: "The forecast has yet to show 30 minutes of solar power covering consumption. Check the source under “Prices & times”.",
			consumption_missing: "The forecast needs at least one minute of consumption readings.",
			measurements_missing: "Current battery readings are missing.",
			calibration: "Battery calibration takes priority.",
			pv_surplus: "Surplus solar power available.",
			manual_charge: "Manual charging takes priority.",
			soc_limit: "Battery charge limit reached."
		}), _ = Z(() => {
			let e = s.value.reason;
			return d.value && e === "pv_start_missing" ? null : typeof e == "string" && Object.hasOwn(g.value, e) ? g.value[e] : null;
		});
		function v(e, n, r, i = 1) {
			let a = Q(e);
			return a !== null && a >= n && a <= r ? _o(a, t.hass, i) : null;
		}
		function y(e) {
			if (typeof e != "string" || !/^\d{4}-\d{2}-\d{2}T.+(?:Z|[+-]\d{2}:\d{2})$/.test(e)) return null;
			let t = Date.parse(e);
			return Number.isFinite(t) ? t : null;
		}
		function b(e, n, r = "short") {
			if (y(e) === null) return null;
			if (n) {
				let i = { dateStyle: "medium" };
				if (vo(e, t.hass, i) === vo(n, t.hass, i)) return vo(e, t.hass, { timeStyle: r });
			}
			return vo(e, t.hass, {
				dateStyle: "medium",
				timeStyle: r
			});
		}
		let x = Z(() => new Intl.DateTimeFormat("en", {
			timeZone: t.hass?.config?.time_zone,
			timeZoneName: "shortOffset"
		}));
		function S(e, t) {
			let n = (e) => x.value.formatToParts(e).find((e) => e.type === "timeZoneName")?.value;
			return n(e) === n(t) ? Math.floor(e / 6e4) === Math.floor(t / 6e4) ? "medium" : "short" : "long";
		}
		function C(e, t, n = !1) {
			let r = b(t), a = v(e.observation_minutes, 1, 15, 0), o = v(e.average_discharge_w, Number.MIN_VALUE, Infinity, 0);
			if (!r || !a || !o && !n) return null;
			let s = i.value ? o ? `durchschnittlich ${o} W über ${a} min` : `${a} min Verbrauchsmessung` : o ? `average ${o} W over ${a} min` : `${a} min of consumption readings`;
			return {
				at: t,
				description: i.value ? `Ohne Netzladung reicht der Speicher ${n ? "laut Plan" : "voraussichtlich"} bis ${r} Uhr (${s}).` : `${n ? "The plan estimates the battery will last" : "The battery should last"} until ${r} without grid charging (${s}).`
			};
		}
		let w = Z(() => {
			if (!a.value?.available || !D.value || !("post_charge_status" in s.value)) return null;
			let e = s.value.post_charge_status;
			return e === "needed" || e === "not_needed" ? e : "unknown";
		}), T = Z(() => {
			let e = s.value.post_charge_forecast_attributes;
			return e && typeof e == "object" && !Array.isArray(e) ? e : null;
		}), E = Z(() => {
			if (m.value) return null;
			if (w.value !== null) {
				let e = T.value;
				return e && w.value !== "unknown" ? C(e, e.discharge_at) : null;
			}
			if (M.value || h.value && s.value.empty_battery_start_due === !0 || !u.value?.available) return null;
			let e = u.value.state;
			return C(e?.attributes ?? {}, e?.state);
		}), D = Z(() => [
			"waiting_for_data",
			"complete",
			"insufficient"
		].includes(p.value ?? "") && b(s.value.completed_at) !== null), O = Z(() => {
			if (m.value) return "charging";
			if (c.value) return "fixed-time";
			if (h.value) return "fixed-target";
			if (w.value !== null) return w.value === "not_needed" ? "not-needed" : w.value;
			let e = Q(s.value.shortfall_kwh), t = s.value.completed_at != null, n = D.value && b(s.value.completion_evaluated_at) !== null && e !== null && e >= 0;
			if (t && !n) return "unknown";
			switch (p.value) {
				case "not_needed": {
					let e = y(s.value.pv_start), t = y(E.value?.at);
					return t !== null && e !== null && e - t >= 6e4 ? "conflict" : "not-needed";
				}
				case "complete": return n && e <= .001 ? "not-needed" : "unknown";
				case "planned":
				case "charging":
				case "insufficient": return "needed";
				case "paused": {
					let t = Q(s.value.target_soc);
					return e !== null && e > 0 || b(s.value.charge_start) && b(s.value.charge_end) && t !== null && t > 0 && t <= 100 ? "needed" : "unknown";
				}
				default: return "unknown";
			}
		}), k = Z(() => {
			switch (O.value) {
				case "charging": return f.value.charging;
				case "fixed-time": return l.value;
				case "fixed-target": return h.value;
				case "not-needed": return f.value.noCharge;
				case "conflict": return f.value.conflict;
				case "needed": return f.value.chargeNeeded;
				default: return p.value === "off" ? null : [
					"paused",
					"complete",
					"insufficient",
					"waiting_for_data"
				].includes(p.value ?? "") ? f.value.demandUnknown : f.value.unavailable;
			}
		});
		function ee(e) {
			let t = Math.ceil(e / 60), n = Math.floor(t / 60), r = t % 60, a = [];
			return n && a.push(`${v(n, 1, Infinity, 0)} ${i.value ? n === 1 ? "Stunde" : "Stunden" : n === 1 ? "hour" : "hours"}`), (r || !n) && a.push(`${r} ${i.value ? r === 1 ? "Minute" : "Minuten" : r === 1 ? "minute" : "minutes"}`), a.join(" ");
		}
		function A(e) {
			return v(e, 0, 100, +!Number.isInteger(Q(e)));
		}
		function te(e) {
			let n = Q(e);
			return n === null || n <= 0 ? null : n < .01 ? `${i.value ? "weniger als" : "less than"} ${_o(.01, t.hass, 2)} kWh` : `${_o(n, t.hass, 2)} kWh`;
		}
		let ne = Z(() => {
			let e = s.value, t = v(e.charging_power_w, Number.MIN_VALUE, Infinity, 0), n = A(e.charging_target_soc), r = A(e.charging_max_soc), a = Q(e.charging_remaining_seconds), o = a !== null && a >= 0 ? ee(a) : null, c = i.value;
			return [
				t && (c ? `${t} W Ladeleistung` : `${t} W charging power`),
				a === 0 ? c ? "Restdauer unter 1 Minute" : "less than 1 minute remaining" : o ? c ? `noch etwa ${o}` : `about ${o} remaining` : c ? "Restdauer unbekannt" : "remaining time unknown",
				n && (c ? `Ladeziel ${n} %` : `target ${n}%`),
				r && Q(e.charging_max_soc) !== Q(e.charging_target_soc) ? c ? `Netzladegrenze ${r} %` : `grid charging limit ${r}%` : null
			].filter(Boolean).join(" · ");
		}), j = Z(() => {
			if (!D.value) return null;
			switch (s.value.data_gap_reason) {
				case "pv_start_missing": return i.value ? "Während der Ladung fehlte zeitweise die PV-Prognose." : "The solar forecast was temporarily unavailable during charging.";
				case "measurements_missing": return i.value ? "Während der Ladung fehlten zeitweise Batteriemesswerte." : "Battery readings were temporarily unavailable during charging.";
				default: return null;
			}
		}), re = Z(() => {
			let e = b(s.value.completion_evaluated_at);
			return !D.value || !e ? null : i.value ? `Letzte Ladung bewertet am ${e} Uhr.` : `Last charge assessed on ${e}.`;
		}), M = Z(() => (h.value || !D.value && ["planned", "insufficient"].includes(p.value ?? "")) && b(s.value.empty_battery_start)), N = Z(() => E.value ? E.value : D.value || M.value || ![
			"planned",
			"charging",
			"insufficient",
			"not_needed"
		].includes(p.value ?? "") ? null : C(s.value, s.value.discharge_at, !0));
		function ie(e, t) {
			let n = b(e, t);
			if (!n) return null;
			let r = y(t);
			return r !== null && Math.floor(y(e) / 6e4) === Math.floor(r / 6e4) ? i.value ? "Ab dann deckt PV voraussichtlich den Verbrauch." : "Solar power should cover consumption from then on." : i.value ? `PV deckt den Verbrauch voraussichtlich ab ${n} Uhr.` : `Solar power should cover consumption from ${n}.`;
		}
		function ae(e) {
			let t = te(s.value.shortfall_kwh), n = v(s.value.soc_buffer, 1, 100, 0);
			if (i.value) {
				let r = `Bis zum PV-Start${e ? ` (${e} Uhr)` : ""}`, i = n ? " für Verbrauch und SOC-Puffer" : "";
				return t ? `${r} fehlen voraussichtlich ${t}${i}.` : `${r} reicht die Energie voraussichtlich nicht${i}.`;
			}
			let r = `before solar power takes over${e ? ` at ${e}` : ""}`, a = n ? " for consumption and the battery reserve" : "";
			return t ? `Expected shortfall of ${t}${a} ${r}.` : `Available energy is unlikely to be sufficient${a} ${r}.`;
		}
		let oe = Z(() => {
			let e = s.value;
			if (m.value) {
				let t = p.value === "charging" && (Q(e.shortfall_kwh) ?? 0) > 0;
				return [ne.value, t && ae()].filter(Boolean).join(". ");
			}
			let t = N.value, n = [t?.description];
			if (w.value !== null) n.push(w.value === "unknown" ? p.value === "waiting_for_data" ? f.value.completionPending : f.value.postChargeWaiting : ie(T.value?.pv_start, t?.at));
			else if (D.value) p.value === "waiting_for_data" ? n.push(f.value.completionPending) : (n.push(f.value.complete), p.value === "insufficient" && n.push(ae()));
			else switch (p.value) {
				case "planned":
				case "charging":
				case "insufficient": {
					let r = p.value === "insufficient" || p.value === "charging" && (Q(e.shortfall_kwh) ?? 0) > 0;
					p.value === "charging" && n.push(f.value.unconfirmed);
					let a = y(e.charge_start), o = y(e.charge_end), s = a !== null && o !== null && a < o;
					if (s) {
						let s = S(a, o), c = b(e.charge_start, t?.at, s), l = b(e.charge_end, e.charge_start, s), u = r ? f.value.partial : f.value.charge;
						M.value && n.push(f.value.emptyBattery);
						let d = M.value ? f.value.firstTariff : f.value.lowTariff, p = a === y(t?.at) && s === "short";
						if (i.value) {
							let e = p ? "ab dann" : `von ${c}`;
							n.push(`${u} ${d} ${e} bis ${l}${s === "long" ? "" : " Uhr"} geplant.`);
						} else n.push(`${u} planned ${d} from ${p ? "then" : c} to ${l}.`);
					} else r && e.reason === "no_usable_window" ? n.push(f.value.noWindow) : r || n.push(f.value.incomplete);
					let c = s ? e.charge_end : t?.at;
					r ? n.push(ae(b(e.pv_start, c))) : n.push(ie(e.pv_start, c));
					break;
				}
				case "not_needed":
					n.push(ie(e.pv_start, t?.at));
					break;
				case "waiting_for_data":
					n.push(_.value ?? (d.value ? null : f.value.waiting));
					break;
				case "paused":
					n.push(f.value.paused, _.value);
					break;
				case "complete": n.push(f.value.complete);
			}
			let r = y(w.value === "needed" ? T.value?.pv_start : e.pv_start), a = y(t?.at);
			return O.value === "needed" && (p.value === "planned" || w.value === "needed") && v(e.soc_buffer, 1, 100, 0) && r !== null && a !== null && a >= r && n.push(i.value ? "Der Ladebedarf berücksichtigt den SOC-Puffer." : "Charging demand includes the battery reserve."), n.filter(Boolean).join(" ");
		}), se = Z(() => {
			if (D.value || ![
				"planned",
				"charging",
				"insufficient",
				"paused"
			].includes(p.value ?? "")) return null;
			let e = te(s.value.charge_energy_kwh), t = !m.value && p.value !== "paused" ? A(s.value.target_soc) : null;
			return [e && (i.value ? `Geplante Lademenge ${e}` : `Planned charge ${e}`), t && (i.value ? `Ladeziel ${t} %` : `Target ${t}%`)].filter(Boolean).join(" · ");
		});
		return (e, t) => (a.value || o.value || E.value || c.value) && (k.value || oe.value || d.value) ? (W(), G("section", {
			key: 0,
			class: "charge-plan",
			"aria-labelledby": `${B(r)}-charge-plan`
		}, [q("h2", { id: `${B(r)}-charge-plan` }, [Y(F(k.value ? `${f.value.title}: ` : f.value.title), 1), k.value ? (W(), G("span", {
			key: 0,
			class: P(["charge-plan__demand", `charge-plan__demand--${O.value}`]),
			"aria-live": "polite"
		}, F(k.value), 3)) : X("", !0)], 8, Mc), !c.value || m.value ? (W(), G(U, { key: 0 }, [
			m.value && l.value ? (W(), G("p", Nc, F(l.value), 1)) : X("", !0),
			d.value && !c.value ? (W(), G("p", Pc, F(d.value), 1)) : X("", !0),
			oe.value ? (W(), G("p", {
				key: 2,
				class: P(["charge-plan__description", { "charge-plan__forecast": E.value }])
			}, F(oe.value), 3)) : X("", !0),
			j.value ? (W(), G("p", Fc, F(j.value), 1)) : X("", !0),
			re.value ? (W(), G("p", Ic, F(re.value), 1)) : X("", !0),
			se.value ? (W(), G("p", Lc, F(se.value), 1)) : X("", !0)
		], 64)) : X("", !0)], 8, jc)) : X("", !0);
	}
}), [["styles", [".charge-plan{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.charge-plan h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.charge-plan__demand--not-needed{color:color-mix(in srgb, var(--success-color,#008f35) 70%, var(--primary-text-color,#212121))}.charge-plan__demand--needed,.charge-plan__demand--fixed-time,.charge-plan__demand--charging{color:color-mix(in srgb, var(--info-color,#1475e8) 70%, var(--primary-text-color,#212121))}.charge-plan__demand--unknown,.charge-plan__demand--conflict{color:color-mix(in srgb, var(--warning-color,#ef6c00) 70%, var(--primary-text-color,#212121))}.charge-plan p{overflow-wrap:anywhere;line-height:1.6}.charge-plan p:last-child{margin-bottom:0}.charge-plan__target{color:var(--secondary-text-color,#666)}@media (max-width:600px){.charge-plan{padding:20px}}@container sax-content (width>=860px){.charge-plan{padding:18px}.charge-plan h2{margin-bottom:12px;font-size:16px}}"]]]), zc = ["aria-labelledby"], Bc = { class: "tariff-plan__header" }, Vc = ["id"], Hc = [
	"disabled",
	"aria-expanded",
	"aria-controls"
], Uc = ["disabled"], Wc = {
	key: 0,
	role: "status"
}, Gc = {
	key: 1,
	class: "tariff-plan__introduction"
}, Kc = {
	key: 2,
	class: "tariff-plan__price-highlights"
}, qc = {
	key: 0,
	class: "tariff-plan__low-status"
}, Jc = {
	key: 3,
	class: "tariff-plan__compact-summary"
}, Yc = {
	key: 0,
	class: "tariff-plan__periods"
}, Xc = { key: 0 }, Zc = { key: 1 }, Qc = { class: "tariff-plan__period-price" }, $c = {
	key: 0,
	class: "tariff-plan__badge"
}, el = { key: 1 }, tl = { class: "tariff-plan__base-row" }, nl = { class: "tariff-plan__period-price" }, rl = {
	key: 0,
	class: "tariff-plan__badge"
}, il = { class: "tariff-plan__feed-row" }, al = {
	key: 2,
	class: "tariff-plan__period-status"
}, ol = {
	key: 3,
	class: "tariff-plan__pending-status"
}, sl = {
	key: 4,
	class: "tariff-plan__low-unavailable"
}, cl = { class: "tariff-plan__impact" }, ll = {
	key: 4,
	role: "status"
}, ul = ["id"], dl = ["id", "aria-busy"], fl = { key: 0 }, pl = ["disabled"], ml = { class: "tariff-plan__hint" }, hl = { class: "tariff-plan__step" }, gl = ["aria-describedby"], _l = ["id"], vl = { class: "tariff-plan__step" }, yl = { class: "tariff-plan__hint" }, bl = ["id"], xl = {
	key: 0,
	class: "tariff-plan__empty"
}, Sl = { class: "tariff-plan__window-name" }, Cl = [
	"onUpdate:modelValue",
	"name",
	"aria-invalid",
	"aria-describedby",
	"onInput",
	"onChange",
	"aria-label"
], wl = [
	"onUpdate:modelValue",
	"name",
	"aria-invalid",
	"aria-describedby",
	"onInput",
	"onChange",
	"aria-label"
], Tl = ["onUpdate:modelValue", "aria-label"], El = ["aria-label", "onClick"], Dl = {
	key: 2,
	class: "tariff-plan__hint"
}, Ol = { class: "tariff-plan__step" }, kl = ["aria-describedby"], Al = ["id"], jl = ["open"], Ml = { class: "tariff-plan__hint" }, Nl = { class: "tariff-plan__impact" }, Pl = { class: "tariff-plan__actions" }, Fl = ["disabled"], Il = ["disabled"], Ll = ["disabled"], Rl = {
	key: 7,
	class: "tariff-plan__overview"
}, zl = { class: "tariff-plan__current-price" }, Bl = {
	key: 0,
	class: "tariff-plan__low-status"
}, Vl = {
	key: 1,
	class: "tariff-plan__low-unavailable"
}, Hl = { key: 8 }, Ul = {
	key: 9,
	class: "tariff-plan__details tariff-plan__all-prices"
}, Wl = ["aria-label"], Gl = { class: "tariff-plan__table" }, Kl = { scope: "col" }, ql = { scope: "col" }, Jl = { scope: "col" }, Yl = { scope: "col" }, Xl = { colspan: "2" }, Zl = { key: 0 }, Ql = { key: 0 }, $l = { class: "tariff-plan__details" }, eu = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "TariffPlan",
	props: {
		hass: { type: Object },
		compact: { type: Boolean }
	},
	emits: ["saved", "editing"],
	setup(e, { emit: t }) {
		let n = e, r = t, i = Pn(Co), a = Kn(), o = Z(() => i?.tariff.value?.fixed_time_charging?.enabled === !0), s = Z(() => i?.language.value === "de" ? {
			tariff: n.compact ? "Preise & Zeiten" : "Dein Stromtarif",
			introduction: "Trage die Preise aus deinem Stromvertrag ein. Sie gelten jeden Tag zu denselben Zeiten.",
			currentPrice: "Strompreis jetzt",
			baseSection: "Normaler Strompreis",
			windowsSection: "Zeiten mit anderem Preis",
			windowsHint: "Zum Beispiel ein günstiger Nachtpreis von 22:00 bis 06:00 Uhr. Nur die Zeiten eintragen, in denen ein anderer Preis als der Standardpreis gilt.",
			noWindows: "Noch keine anderen Preiszeiten: Der Standardpreis gilt den ganzen Tag.",
			feedSection: "Vergütung für Solarstrom",
			feedHint: "Wie viel erhältst du für eine eingespeiste kWh? Dieser Wert wird für die Ersparnisberechnung verwendet. Ohne Vergütung 0 eintragen.",
			impact: "Das bewirkt dein Tarif",
			impactHint: "Die Automatik nutzt die günstigsten Zeiten für die feste und verbrauchsbasierte Netzladung. Ladestand, Netzladeziel und aktive Monate gelten zusätzlich.",
			saveHint: "Übernehmen speichert Preise und mögliche Ladezeiten. Es schaltet die Netzladung nicht ein.",
			pvDetails: "Zusätzlich: Solarprognose für die Ladeplanung",
			pvHint: "Nur für verbrauchsbasierte Ladeplanung erforderlich. Wähle die eingerichtete PV-Prognosequelle, damit die Planung den Bedarf bis zum Solarstart berechnen kann.",
			allPrices: "Alle Preise ansehen",
			compactImpact: "Die Netzladung nutzt die günstigsten Tarifzeiten.",
			fixedTimeImpact: "Die Netzladung beginnt täglich zur festgelegten Uhrzeit, unabhängig vom Strompreis. Netzladeziel und aktive Monate gelten weiterhin.",
			everyDay: "Täglich",
			remaining: "zu allen übrigen Zeiten",
			overnightLabel: "über Nacht",
			technicalReason: "Technischer Hinweis",
			awaitingTariff: "Die aktuellen Ladezeiten werden aktualisiert.",
			pv: "PV-Start-Sensor (optional)",
			pvRequired: "PV-Start-Sensor (erforderlich)",
			gross: "Alle Preise in ct/kWh inklusive Steuern, ohne monatliche Grundgebühr. Beispiel: 30 eingeben für 30 ct/kWh.",
			edit: "Bearbeiten",
			save: "Übernehmen",
			cancel: "Abbrechen",
			saving: "Wird gespeichert …",
			loading: "Wird geladen …",
			add: "+ Zeitfenster hinzufügen",
			remove: "Entfernen",
			window: "Zeitfenster",
			baseHint: "Gilt den ganzen Tag, außer zu den unten eingetragenen Zeiten.",
			overnight: "Endet ein Fenster vor seiner Startzeit, gilt es über Mitternacht. Fenster dürfen sich nicht überschneiden.",
			details: "Wie werden günstige Ladezeiten ausgewählt?",
			first: "Trage zuerst deinen normalen Strompreis ein. Ergänze danach abweichende Preiszeiten und die Einspeisevergütung.",
			priceError: "Bitte Preise mit höchstens zwei Nachkommastellen eingeben: Standardpreis und Zeitfenster von −200 bis 500 ct/kWh, Einspeisevergütung von 0 bis 200 ct/kWh.",
			timeHint: "Uhrzeiten im 24-Stunden-Format eingeben: 12:30 oder 1230.",
			startError: "Bitte eine vollständige Startzeit eingeben (z. B. 12:30).",
			endError: "Bitte eine vollständige Endzeit eingeben (z. B. 14:30).",
			equalTimeError: "Start und Ende müssen verschieden sein.",
			overlap: "Die Zeitfenster überschneiden sich. Bitte die Zeiten prüfen.",
			disconnected: "Keine Verbindung zu Home Assistant. Dein Entwurf bleibt erhalten.",
			forbidden: "Tarife können nur mit einem Administratorkonto und bei aktivem zeitvariablen Tarif bearbeitet werden.",
			conflict: "Der Tarif wurde inzwischen geändert. Dein Entwurf bleibt erhalten. Lade den gespeicherten Tarif, bevor du erneut bearbeitest.",
			reload: "Gespeicherten Tarif laden (Entwurf verwerfen)",
			bridgePvRequired: "Die PV-Start-Quelle wird für die aktive verbrauchsbasierte Ladung benötigt. Wähle eine Quelle oder schalte diese Ladeplanung zuerst aus.",
			pvMissing: "Der gewählte PV-Start-Sensor wurde nicht gefunden. Wähle einen vorhandenen Sensor oder entferne die Auswahl, wenn die Quelle optional ist.",
			failed: "Der Tarif konnte nicht geladen oder gespeichert werden. Bitte erneut versuchen.",
			invalid: "Der Tarif wurde nicht gespeichert. Bitte Preise und Zeitfenster prüfen.",
			saved: "Tarif gespeichert.",
			from: "Von",
			to: "Bis",
			price: "Arbeitspreis",
			status: "Status",
			now: "jetzt",
			base: "Standardpreis",
			low: "günstig",
			lowTariffPrice: "Günstigster Tagespreis",
			lowUntil: "Günstige Zeit bis",
			notLow: "Aktuell außerhalb der günstigsten Zeiten.",
			rule: "Der niedrigste täglich vorkommende Strompreis heißt Niedertarif. Alle Zeiten mit diesem Preis sind mögliche Ladezeiten. Auch der Standardpreis zählt, wenn er in Lücken zwischen den Zeitfenstern gilt. Die feste und verbrauchsbasierte Netzladung verwenden ausschließlich diese günstigsten Zeiten.",
			configure: "Bisherige separate Netzladezeiten sind bei diesem Tarif unwirksam.",
			noLowTariff: "Günstige Ladezeiten sind derzeit nicht verfügbar. Die SOC-Ladung bleibt gesperrt, bis gültige Tarifdaten vorliegen. Prüfe die Preise über Bearbeiten, wenn dieser Hinweis bestehen bleibt.",
			feed: "Einspeisevergütung",
			next: "Nächster Preiswechsel",
			unavailable: "Nicht verfügbar",
			noPrice: "Derzeit ist kein aktueller Strompreis verfügbar."
		} : {
			tariff: n.compact ? "Prices & times" : "Your electricity tariff",
			introduction: "Enter the prices from your electricity contract. They apply at the same times every day.",
			currentPrice: "Electricity price now",
			baseSection: "Regular electricity price",
			windowsSection: "Times with a different price",
			windowsHint: "For example, a cheaper night rate from 22:00 to 06:00. Only add times when a different price applies instead of the standard price.",
			noWindows: "No other price periods yet: the standard price applies all day.",
			feedSection: "Payment for solar electricity",
			feedHint: "How much do you receive for each exported kWh? This value is used to calculate savings. Enter 0 if you receive no payment.",
			impact: "What your tariff does",
			impactHint: "Automation uses the cheapest times for fixed-target and consumption-based grid charging. Battery level, charging target and active months also apply.",
			saveHint: "Apply saves the prices and possible charging times. It does not turn on grid charging.",
			pvDetails: "Additional setup: solar forecast for charging planning",
			pvHint: "Only required for consumption-based charging planning. Select your configured PV forecast source so planning can calculate the energy needed until solar production starts.",
			allPrices: "View all prices",
			compactImpact: "Grid charging uses the cheapest tariff periods.",
			fixedTimeImpact: "Grid charging starts daily at the configured time, regardless of the electricity price. The grid charging target and active months still apply.",
			everyDay: "Every day",
			remaining: "at all remaining times",
			overnightLabel: "overnight",
			technicalReason: "Technical details",
			awaitingTariff: "Current charging times are being updated.",
			pv: "PV start sensor (optional)",
			pvRequired: "PV start sensor (required)",
			gross: "All prices in ct/kWh including tax, excluding the monthly standing charge. Example: enter 30 for 30 ct/kWh.",
			edit: "Edit",
			save: "Apply",
			cancel: "Cancel",
			saving: "Saving …",
			loading: "Loading …",
			add: "+ Add time window",
			remove: "Remove",
			window: "Time window",
			baseHint: "Applies all day, except during the times entered below.",
			overnight: "A window ending before its start continues past midnight. Windows must not overlap.",
			details: "How are the cheapest charging times selected?",
			first: "Start with your regular electricity price. Then add any different price periods and your feed-in payment.",
			priceError: "Enter prices with up to two decimal places: standard price and windows from −200 to 500 ct/kWh, feed-in remuneration from 0 to 200 ct/kWh.",
			timeHint: "Enter times in 24-hour format: 12:30 or 1230.",
			startError: "Enter a complete start time (e.g. 12:30).",
			endError: "Enter a complete end time (e.g. 14:30).",
			equalTimeError: "Start and end must differ.",
			overlap: "The time windows overlap. Please check the times.",
			disconnected: "Disconnected from Home Assistant. Your draft is preserved.",
			forbidden: "Editing tariffs requires an administrator account and an active time-of-use tariff.",
			conflict: "The tariff has changed elsewhere. Your draft is preserved. Load the saved tariff before editing again.",
			reload: "Load saved tariff (discard draft)",
			bridgePvRequired: "The active consumption-based charging plan requires a PV start source. Choose a source or turn off this charging plan first.",
			pvMissing: "The selected PV start sensor was not found. Choose an existing sensor or clear the selection if this source is optional.",
			failed: "The tariff could not be loaded or saved. Please try again.",
			invalid: "The tariff was not saved. Please check prices and time windows.",
			saved: "Tariff saved.",
			from: "From",
			to: "To",
			price: "Import price",
			status: "Status",
			now: "now",
			base: "Standard price",
			low: "cheapest",
			lowTariffPrice: "Cheapest daily price",
			lowUntil: "Cheapest period until",
			notLow: "Currently outside the cheapest times.",
			rule: "The lowest price level that actually occurs each day is called the low tariff. Every period at this price is a possible charging time. The standard price also counts when it applies in gaps between windows. Fixed-target and consumption-based grid charging only use these cheapest times.",
			configure: "Previously configured separate grid charging times have no effect for this tariff.",
			noLowTariff: "The cheapest charging times are currently unavailable. SOC charging remains blocked until valid tariff data is available. Check the prices using Edit if this message persists.",
			feed: "Feed-in remuneration",
			next: "Next price change",
			unavailable: "Unavailable",
			noPrice: "The current electricity price is unavailable."
		}), c = Z(() => i?.entity("sensor", "economics_current_import_price")), l = (e) => {
			let t = Q(e), r = _o(t === null ? null : t * 100, n.hass, 2);
			return r === null ? s.value.unavailable : `${r} ct/kWh`;
		}, u = Z(() => {
			let e = _o(c.value?.state?.state, n.hass, 2);
			return e === null ? s.value.unavailable : `${e} ct/kWh`;
		}), d = (e) => vo(e, n.hass) ?? s.value.unavailable, f = /* @__PURE__ */ z(null), p = /* @__PURE__ */ z({});
		V(() => c.value?.state?.attributes, (e) => {
			e && (p.value = e);
		}, { immediate: !0 });
		let m = Z(() => c.value?.state?.attributes ?? (i?.connected.value ? {} : p.value)), h = /* @__PURE__ */ z(null);
		function g(e) {
			if (!e.tariff_type) return null;
			let t = (e) => {
				let t = Q(e);
				return t === null ? null : Math.round(t * 1e8) / 1e8;
			}, n = (e) => typeof e == "string" && e.length === 5 ? `${e}:00` : e, r = Array.isArray(e.windows) ? e.windows.map((e) => !e || typeof e != "object" ? null : {
				start: n(e.start),
				end: n(e.end),
				price: t(e.price_eur_kwh)
			}).sort((e, t) => JSON.stringify(e).localeCompare(JSON.stringify(t))) : null;
			return JSON.stringify({
				type: e.tariff_type,
				base: t(e.base_price_eur_kwh),
				feed: t(e.feed_in_price_eur_kwh),
				windows: r
			});
		}
		function _() {
			let e = f.value, t = g(m.value);
			e && t && (t === g({
				tariff_type: e.tariff_type,
				base_price_eur_kwh: e.base_price_ct_kwh === null ? null : e.base_price_ct_kwh / 100,
				feed_in_price_eur_kwh: e.feed_in_price_ct_kwh === null ? null : e.feed_in_price_ct_kwh / 100,
				windows: e.windows.map((e) => ({
					...e,
					price_eur_kwh: e.price_ct_kwh / 100
				}))
			}) || t !== h.value) && (f.value = null);
		}
		V(m, _);
		let v = !1;
		cr(() => {
			v = !0;
		}), V([() => i?.ready.value, () => m.value.tariff_type], ([e, t]) => {
			e && !t && !i?.tariff.value && i?.loadTariff().catch(() => {});
		}, { immediate: !0 });
		let y = Z(() => {
			let e = f.value ?? (n.compact || !m.value.tariff_type ? i?.tariff.value : null);
			if (!e) return m.value;
			let t = {
				...m.value,
				tariff_type: e.tariff_type,
				base_price_eur_kwh: e.base_price_ct_kwh === null ? null : e.base_price_ct_kwh / 100,
				feed_in_price_eur_kwh: e.feed_in_price_ct_kwh === null ? null : e.feed_in_price_ct_kwh / 100,
				windows: e.windows.map((e) => ({
					...e,
					price_eur_kwh: e.price_ct_kwh / 100
				})),
				active_window: null,
				low_tariff_price_eur_kwh: null
			};
			return g(t) === g(m.value) ? m.value : t;
		}), b = Z(() => g(y.value) === g(m.value)), x = Z(() => y.value.tariff_type === "time_of_use"), S = Z(() => Array.isArray(y.value.windows) ? y.value.windows.filter((e) => !!e && typeof e == "object" && typeof e.start == "string" && typeof e.end == "string") : []), C = Z(() => y.value.unavailable_reason), w = Z(() => c.value?.available === !0 && Q(c.value.state?.state) !== null && C.value == null && !f.value), T = Z(() => w.value && Q(y.value.low_tariff_price_eur_kwh) !== null && typeof y.value.low_tariff_active == "boolean" && (y.value.low_tariff_active === !1 || E.value !== null) && typeof y.value.base_price_is_low_tariff == "boolean" && Array.isArray(y.value.windows) && S.value.length === y.value.windows.length && S.value.every((e) => typeof e.low_tariff == "boolean" && Q(e.price_eur_kwh) !== null)), E = Z(() => vo(y.value.low_tariff_valid_until, n.hass)), D = Z(() => T.value && y.value.low_tariff_active === !0 && E.value !== null), O = (e) => T.value && e.low_tariff === !0, k = Z(() => T.value && y.value.base_price_is_low_tariff === !0), ee = (e, t) => [e ? s.value.now : "", t ? s.value.low : ""].filter(Boolean).join(" · "), A = Z(() => {
			let e = y.value.active_window;
			return e && typeof e == "object" ? e : null;
		}), te = (e) => w.value && Q(e.price_eur_kwh) !== null && A.value?.start === e.start && A.value?.end === e.end, ne = Z(() => w.value && A.value === null && Q(y.value.base_price_eur_kwh) !== null), j = (e) => vo(`2000-01-01T${e.length === 5 ? `${e}:00` : e}Z`, n.hass, {
			timeStyle: "short",
			timeZone: "UTC"
		}) ?? e.slice(0, 5);
		function re(e) {
			let t = $(e.start), n = $(e.end);
			if (t === null || n === null || t === n) return null;
			let r = Math.floor((n - t + 86400) % 86400 / 60), a = Math.floor(r / 60), o = r % 60, s = i?.language.value === "de";
			return [a && `${a} ${s ? a === 1 ? "Stunde" : "Stunden" : a === 1 ? "hour" : "hours"}`, (o || !a) && `${o} ${s ? o === 1 ? "Minute" : "Minuten" : o === 1 ? "minute" : "minutes"}`].filter((e) => typeof e == "string").join(" ");
		}
		let M = /* @__PURE__ */ z(!1);
		V(M, (e) => r("editing", e));
		let N = /* @__PURE__ */ z(!1), ie = /* @__PURE__ */ z("loading"), ae = /* @__PURE__ */ z(), oe = /* @__PURE__ */ z(), se = /* @__PURE__ */ z(null), ce = /* @__PURE__ */ z(""), le = /* @__PURE__ */ z(""), ue = /* @__PURE__ */ z(null), de = Z(() => i?.entity("switch", "bridge_charge_enabled")?.state?.state === "on"), fe = /* @__PURE__ */ z([]), pe = 0, me = /* @__PURE__ */ z(null), he = /* @__PURE__ */ z(null), ge = /* @__PURE__ */ z(!1), _e = /* @__PURE__ */ z(!1), ve = Z(() => i?.connected.value === !0 && i.ready.value), ye = Z(() => {
			if (me.value === "timeError" && he.value) {
				let e = fe.value.findIndex((e) => e.key === he.value.key);
				return `${s.value.window} ${e + 1}: ${s.value[he.value.reason]}`;
			}
			return me.value ? s.value[me.value] : null;
		});
		function be(e, t) {
			return ae.value?.querySelector(`[name="window_${e}_${t}"]`);
		}
		function xe(e, t, n) {
			let r = fe.value.find((t) => t.key === e), i = n.target;
			r && (i.value = r[t] = zs(i.value)), I(e);
		}
		function I(e) {
			(e === void 0 || he.value?.key === e) && (he.value = null, me.value === "timeError" && (me.value = null));
		}
		function Se(e) {
			if (v) return;
			let t = e && typeof e == "object" && "code" in e ? e.code : "failed";
			ge.value = t === "conflict", me.value = t === "bridge_pv_start_required" ? "bridgePvRequired" : t === "pv_sensor_missing" ? "pvMissing" : t === "invalid_tariff" || t === "invalid_format" ? "invalid" : [
				"conflict",
				"disconnected",
				"forbidden"
			].includes(String(t)) ? String(t) : "failed";
		}
		function Ce(e) {
			return e === null ? "" : e.toFixed(2).replace(".", i?.language.value === "de" ? "," : ".");
		}
		async function we() {
			if (i && !N.value) {
				ie.value = "loading", N.value = !0, me.value = null, I(), _e.value = !1;
				try {
					let e = await i.loadTariff();
					if (v) return;
					if (!e.can_edit || e.tariff_type !== "time_of_use") throw { code: "forbidden" };
					se.value = e, ce.value = Ce(e.base_price_ct_kwh), le.value = Ce(e.feed_in_price_ct_kwh), ue.value = e.profiles?.time_of_use.pv_sensor ?? null, fe.value = e.windows.map((e) => ({
						key: pe++,
						start: Oe(e.start),
						end: Oe(e.end),
						price: Ce(e.price_ct_kwh)
					})), ge.value = !1, M.value = !0;
				} catch (e) {
					Se(e);
				} finally {
					N.value = !1, await vn(), M.value && ae.value?.querySelector("input")?.focus();
				}
			}
		}
		function L() {
			M.value = !1, me.value = null, I(), ge.value = !1, fe.value = [], vn(() => oe.value?.focus());
		}
		async function Te() {
			fe.value.push({
				key: pe++,
				start: "",
				end: "",
				price: ""
			}), await vn(), ae.value?.querySelector(".tariff-plan__window:last-of-type input")?.focus();
		}
		async function Ee(e) {
			I(fe.value[e]?.key), fe.value.splice(e, 1), await vn();
			let t = ae.value?.querySelectorAll(".tariff-plan__window");
			(t?.[Math.min(e, t.length - 1)]?.querySelector("input") ?? ae.value?.querySelector(".tariff-plan__add"))?.focus();
		}
		function De(e, t, n) {
			if (!/^-?\d+(?:[.,]\d{1,2})?$/.test(e.trim())) return null;
			let r = Number(e.trim().replace(",", "."));
			return Number.isFinite(r) && r >= t && r <= n ? r : null;
		}
		function Oe(e) {
			return e.length === 8 && e.endsWith(":00") ? e.slice(0, 5) : e;
		}
		async function ke() {
			if (!i || !se.value || N.value || ge.value) return;
			me.value = null, I();
			for (let e of fe.value) for (let t of ["start", "end"]) {
				let n = be(e.key, t);
				n && (e[t] = zs(n.value));
			}
			let e = De(ce.value, -200, 500), t = De(le.value, 0, 200), a = fe.value.map((e) => ({
				...e,
				value: De(e.price, -200, 500)
			}));
			if (e === null || t === null || a.some((e) => e.value === null)) {
				me.value = "priceError";
				return;
			}
			let o = [];
			for (let e of a) {
				let t = $(e.start), n = $(e.end);
				if (t === null || n === null || t === n) {
					let r = t === null ? "start" : "end";
					he.value = {
						key: e.key,
						field: r,
						reason: t === null ? "startError" : n === null ? "endError" : "equalTimeError"
					}, me.value = "timeError", await vn(), be(e.key, r)?.focus();
					return;
				}
				o.push(...t < n ? [{
					start: t,
					end: n
				}] : [{
					start: t,
					end: 86400
				}, {
					start: 0,
					end: n
				}]);
			}
			let s = o.filter((e) => e.start < e.end).sort((e, t) => e.start - t.start);
			if (s.some((e, t) => t > 0 && e.start < s[t - 1].end)) {
				me.value = "overlap";
				return;
			}
			ie.value = "saving", N.value = !0;
			let c = g(m.value);
			try {
				let o = {
					revision: se.value.revision,
					base_price_ct_kwh: e,
					feed_in_price_ct_kwh: t,
					windows: a.map((e) => ({
						start: e.start.length === 5 ? `${e.start}:00` : e.start,
						end: e.end.length === 5 ? `${e.end}:00` : e.end,
						price_ct_kwh: e.value
					}))
				}, s = n.compact ? await i.configureTariff({
					revision: o.revision,
					tariff_type: "time_of_use",
					profile: {
						base_price_ct_kwh: o.base_price_ct_kwh,
						feed_in_price_ct_kwh: o.feed_in_price_ct_kwh,
						windows: o.windows,
						pv_sensor: ue.value
					}
				}) : await i.saveTariff(o);
				if (v) return;
				f.value = s, h.value = c, _(), L(), _e.value = !0, r("saved");
			} catch (e) {
				Se(e);
			} finally {
				N.value = !1;
			}
		}
		return V(ve, (e) => {
			!e && M.value ? me.value = "disconnected" : e && me.value === "disconnected" && (me.value = null);
		}), V(x, (e) => {
			!e && i?.ready.value && L();
		}), (t, n) => x.value ? (W(), G("section", {
			key: 0,
			class: P(["tariff-plan", { "tariff-plan--compact": e.compact }]),
			"aria-labelledby": `${B(a)}-tariff`
		}, [
			q("header", Bc, [q("h2", { id: `${B(a)}-tariff` }, F(s.value.tariff), 9, Vc), J(No, null, {
				default: An(() => [q("button", {
					ref_key: "editButton",
					ref: oe,
					type: "button",
					disabled: N.value || !ve.value || M.value && ge.value,
					"aria-expanded": M.value,
					"aria-controls": `${B(a)}-editor`,
					onClick: n[0] ||= (e) => M.value ? ke() : we()
				}, F(N.value ? s.value[ie.value] : M.value ? s.value.save : s.value.edit), 9, Hc), M.value ? (W(), G("button", {
					key: 0,
					type: "button",
					disabled: N.value,
					onClick: L
				}, F(s.value.cancel), 9, Uc)) : X("", !0)]),
				_: 1
			})]),
			N.value ? (W(), G("p", Wc, F(s.value[ie.value]), 1)) : X("", !0),
			!M.value && !e.compact ? (W(), G("p", Gc, F(s.value.introduction), 1)) : X("", !0),
			e.compact ? (W(), G("div", Kc, [ur(t.$slots, "current-price"), !o.value && T.value ? (W(), G("p", qc, [q("span", null, F(s.value.lowTariffPrice), 1), q("strong", null, F(l(y.value.low_tariff_price_eur_kwh)), 1)])) : X("", !0)])) : X("", !0),
			e.compact && !M.value ? (W(), G("div", Jc, [
				S.value.length ? (W(), G("ul", Yc, [(W(!0), G(U, null, H(S.value, (e, t) => (W(), G("li", { key: t }, [q("span", null, [
					Y(F(s.value.everyDay) + " " + F(j(e.start)) + " – " + F(j(e.end)), 1),
					re(e) ? (W(), G("span", Xc, " (" + F(re(e)) + ")", 1)) : X("", !0),
					e.end < e.start ? (W(), G("span", Zc, " (" + F(s.value.overnightLabel) + ")", 1)) : X("", !0)
				]), q("span", Qc, [O(e) ? (W(), G("span", $c, F(s.value.low), 1)) : X("", !0), q("strong", null, F(l(e.price_eur_kwh)), 1)])]))), 128))])) : (W(), G("p", el, F(s.value.noWindows), 1)),
				q("div", tl, [q("span", null, [Y(F(s.value.base), 1), q("small", null, F(s.value.remaining), 1)]), q("span", nl, [k.value ? (W(), G("span", rl, F(s.value.low), 1)) : X("", !0), q("strong", null, F(l(y.value.base_price_eur_kwh)), 1)])]),
				q("div", il, [q("span", null, F(s.value.feed), 1), q("strong", null, F(l(y.value.feed_in_price_eur_kwh)), 1)]),
				!o.value && T.value ? (W(), G("p", al, [D.value ? (W(), G(U, { key: 0 }, [Y(F(s.value.lowUntil) + " " + F(E.value) + ".", 1)], 64)) : (W(), G(U, { key: 1 }, [Y(F(s.value.notLow), 1)], 64))])) : !o.value && (f.value || !b.value) ? (W(), G("p", ol, F(s.value.awaitingTariff), 1)) : o.value ? X("", !0) : (W(), G("p", sl, F(s.value.noLowTariff), 1)),
				q("p", cl, F(o.value ? s.value.fixedTimeImpact : s.value.compactImpact), 1)
			])) : X("", !0),
			_e.value ? (W(), G("p", ll, F(s.value.saved), 1)) : X("", !0),
			ye.value ? (W(), G("p", {
				key: 5,
				id: `${B(a)}-error`,
				role: "alert",
				class: "tariff-plan__error"
			}, F(ye.value), 9, ul)) : X("", !0),
			M.value ? (W(), G("form", {
				key: 6,
				id: `${B(a)}-editor`,
				ref_key: "editor",
				ref: ae,
				class: "tariff-plan__editor",
				"aria-busy": N.value,
				novalidate: "",
				onSubmit: io(ke, ["prevent"])
			}, [
				se.value?.base_price_ct_kwh === null ? (W(), G("p", fl, F(s.value.first), 1)) : X("", !0),
				q("fieldset", { disabled: N.value || !ve.value }, [
					q("p", ml, F(s.value.gross), 1),
					q("div", hl, [q("h3", null, F(s.value.baseSection), 1), q("label", null, [
						Y(F(s.value.base) + " (ct/kWh)", 1),
						jn(q("input", {
							"onUpdate:modelValue": n[1] ||= (e) => ce.value = e,
							name: "base_price",
							type: "text",
							inputmode: "decimal",
							autocomplete: "off",
							"aria-describedby": `${B(a)}-base-hint`
						}, null, 8, gl), [[Xa, ce.value]]),
						q("small", { id: `${B(a)}-base-hint` }, F(s.value.baseHint), 9, _l)
					])]),
					q("div", vl, [
						q("h3", null, F(s.value.windowsSection), 1),
						q("p", yl, F(s.value.windowsHint), 1),
						q("p", {
							id: `${B(a)}-time-hint`,
							class: "tariff-plan__hint"
						}, F(s.value.timeHint), 9, bl),
						fe.value.length ? X("", !0) : (W(), G("p", xl, F(s.value.noWindows), 1)),
						(W(!0), G(U, null, H(fe.value, (e, t) => (W(), G("div", {
							key: e.key,
							class: "tariff-plan__window"
						}, [
							q("span", Sl, F(s.value.window) + " " + F(t + 1), 1),
							q("label", null, [Y(F(s.value.from), 1), jn(q("input", {
								"onUpdate:modelValue": (t) => e.start = t,
								name: `window_${e.key}_start`,
								type: "text",
								class: "tariff-plan__time",
								inputmode: "numeric",
								autocomplete: "off",
								placeholder: "HH:MM",
								"aria-invalid": he.value?.key === e.key && he.value.field === "start",
								"aria-describedby": he.value?.key === e.key && he.value.field === "start" ? `${B(a)}-time-hint ${B(a)}-error` : `${B(a)}-time-hint`,
								onInput: (t) => I(e.key),
								onChange: (t) => xe(e.key, "start", t),
								"aria-label": `${s.value.window} ${t + 1}: ${s.value.from}`
							}, null, 40, Cl), [[Xa, e.start]])]),
							q("label", null, [Y(F(s.value.to), 1), jn(q("input", {
								"onUpdate:modelValue": (t) => e.end = t,
								name: `window_${e.key}_end`,
								type: "text",
								class: "tariff-plan__time",
								inputmode: "numeric",
								autocomplete: "off",
								placeholder: "HH:MM",
								"aria-invalid": he.value?.key === e.key && he.value.field === "end",
								"aria-describedby": he.value?.key === e.key && he.value.field === "end" ? `${B(a)}-time-hint ${B(a)}-error` : `${B(a)}-time-hint`,
								onInput: (t) => I(e.key),
								onChange: (t) => xe(e.key, "end", t),
								"aria-label": `${s.value.window} ${t + 1}: ${s.value.to}`
							}, null, 40, wl), [[Xa, e.end]])]),
							q("label", null, [Y(F(s.value.price) + " (ct/kWh)", 1), jn(q("input", {
								"onUpdate:modelValue": (t) => e.price = t,
								class: "tariff-plan__price",
								type: "text",
								inputmode: "decimal",
								autocomplete: "off",
								"aria-label": `${s.value.window} ${t + 1}: ${s.value.price} (ct/kWh)`
							}, null, 8, Tl), [[Xa, e.price]])]),
							q("button", {
								type: "button",
								class: "tariff-plan__remove",
								"aria-label": `${s.value.window} ${t + 1}: ${s.value.remove}`,
								onClick: (e) => Ee(t)
							}, F(s.value.remove), 9, El)
						]))), 128)),
						fe.value.length < 8 ? (W(), G("button", {
							key: 1,
							type: "button",
							class: "tariff-plan__add",
							onClick: Te
						}, F(s.value.add), 1)) : X("", !0),
						fe.value.length ? (W(), G("p", Dl, F(s.value.overnight), 1)) : X("", !0)
					]),
					q("div", Ol, [q("h3", null, F(s.value.feedSection), 1), q("label", null, [
						Y(F(s.value.feed) + " (ct/kWh)", 1),
						jn(q("input", {
							"onUpdate:modelValue": n[2] ||= (e) => le.value = e,
							name: "feed_in_price",
							type: "text",
							inputmode: "decimal",
							autocomplete: "off",
							"aria-describedby": `${B(a)}-feed-hint`
						}, null, 8, kl), [[Xa, le.value]]),
						q("small", { id: `${B(a)}-feed-hint` }, F(s.value.feedHint), 9, Al)
					])]),
					e.compact ? (W(), G("details", {
						key: 0,
						class: "tariff-plan__details tariff-plan__pv-details",
						open: de.value || me.value === "bridgePvRequired" || me.value === "pvMissing"
					}, [
						q("summary", null, F(s.value.pvDetails), 1),
						q("p", Ml, F(s.value.pvHint), 1),
						J(mc, {
							modelValue: ue.value,
							"onUpdate:modelValue": n[3] ||= (e) => ue.value = e,
							hass: e.hass,
							label: de.value ? s.value.pvRequired : s.value.pv
						}, null, 8, [
							"modelValue",
							"hass",
							"label"
						])
					], 8, jl)) : X("", !0),
					q("div", Nl, [
						q("strong", null, F(s.value.impact), 1),
						q("p", null, F(o.value ? s.value.fixedTimeImpact : s.value.impactHint), 1),
						q("p", null, F(s.value.saveHint), 1)
					])
				], 8, pl),
				q("div", Pl, [J(No, null, {
					default: An(() => [q("button", {
						type: "submit",
						class: "tariff-plan__save",
						disabled: N.value || !ve.value || ge.value
					}, F(N.value ? s.value[ie.value] : s.value.save), 9, Fl), q("button", {
						type: "button",
						disabled: N.value,
						onClick: L
					}, F(s.value.cancel), 9, Il)]),
					_: 1
				}), ge.value ? (W(), G("button", {
					key: 0,
					type: "button",
					disabled: N.value || !ve.value,
					onClick: we
				}, F(s.value.reload), 9, Ll)) : X("", !0)])
			], 40, dl)) : X("", !0),
			!M.value && !e.compact && !f.value ? (W(), G("div", Rl, [q("p", zl, [q("span", null, F(s.value.currentPrice), 1), q("strong", null, F(w.value ? u.value : s.value.unavailable), 1)]), !o.value && T.value ? (W(), G("p", Bl, [
				q("strong", null, F(s.value.lowTariffPrice) + ":", 1),
				Y(" " + F(l(y.value.low_tariff_price_eur_kwh)) + ". ", 1),
				D.value ? (W(), G(U, { key: 0 }, [Y(F(s.value.lowUntil) + " " + F(E.value) + ". ", 1)], 64)) : (W(), G(U, { key: 1 }, [Y(F(s.value.notLow), 1)], 64))
			])) : o.value ? X("", !0) : (W(), G("p", Vl, F(s.value.noLowTariff), 1))])) : X("", !0),
			!M.value && !e.compact && w.value && y.value.next_price_change_at && !f.value ? (W(), G("p", Hl, [q("strong", null, F(s.value.next) + ":", 1), Y(" " + F(d(y.value.next_price_change_at)), 1)])) : X("", !0),
			!M.value && !e.compact ? (W(), G("details", Ul, [
				q("summary", null, F(s.value.allPrices), 1),
				q("div", {
					class: "tariff-plan__scroll",
					tabindex: "0",
					role: "region",
					"aria-label": s.value.allPrices
				}, [q("table", Gl, [q("thead", null, [q("tr", null, [
					q("th", Kl, F(s.value.status), 1),
					q("th", ql, F(s.value.from), 1),
					q("th", Jl, F(s.value.to), 1),
					q("th", Yl, F(s.value.price), 1)
				])]), q("tbody", null, [(W(!0), G(U, null, H(S.value, (e, t) => (W(), G("tr", {
					key: t,
					class: P({
						"tariff-plan__current": te(e),
						"tariff-plan__low": O(e)
					})
				}, [
					q("td", null, F(ee(te(e), O(e))), 1),
					q("td", null, F(j(e.start)), 1),
					q("td", null, F(j(e.end)), 1),
					q("td", null, F(l(e.price_eur_kwh)), 1)
				], 2))), 128)), q("tr", { class: P({
					"tariff-plan__current": ne.value,
					"tariff-plan__low": k.value
				}) }, [
					q("td", null, F(ee(ne.value, k.value)), 1),
					q("td", Xl, F(s.value.base), 1),
					q("td", null, F(l(y.value.base_price_eur_kwh)), 1)
				], 2)])])], 8, Wl),
				q("p", null, [q("strong", null, F(s.value.feed) + ":", 1), Y(" " + F(l(y.value.feed_in_price_eur_kwh)), 1)]),
				!w.value && !f.value ? (W(), G("p", Zl, [Y(F(s.value.noPrice), 1), typeof C.value == "string" && C.value ? (W(), G("span", Ql, F(s.value.technicalReason) + ": " + F(C.value), 1)) : X("", !0)])) : X("", !0)
			])) : X("", !0),
			q("details", $l, [
				q("summary", null, F(s.value.details), 1),
				q("p", null, F(o.value ? s.value.fixedTimeImpact : s.value.rule), 1),
				q("p", null, F(s.value.configure), 1)
			])
		], 10, zc)) : X("", !0);
	}
}), [["styles", [".tariff-plan{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.tariff-plan h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.tariff-plan__introduction{color:var(--secondary-text-color,#666);margin:0 0 16px}.tariff-plan__compact-summary{margin:0}.tariff-plan__periods{margin:12px 0;padding:0;list-style:none}.tariff-plan__periods li{border-top:1px solid var(--divider-color,#e0e0e0);flex-wrap:wrap;justify-content:space-between;gap:4px 12px;padding:10px 0;line-height:1.5;display:flex}.tariff-plan__period-price{flex-wrap:wrap;align-items:center;gap:8px;display:flex}.tariff-plan__badge{border:1px solid var(--success-color,#43a047);border-radius:6px;margin-inline-start:8px;padding:2px 7px;font-size:12px;font-weight:500;line-height:1.5;display:inline-block}.tariff-plan__periods strong{white-space:nowrap}.tariff-plan__step{margin:20px 0}.tariff-plan__step h3{margin:0 0 10px;font-size:15px;line-height:1.5}.tariff-plan__step>label{max-width:460px}.tariff-plan__step>label input{max-width:240px}.tariff-plan__step .tariff-plan__hint{margin-top:0}.tariff-plan__impact{background:var(--secondary-background-color,#f5f5f5);border-radius:8px;margin:16px 0;padding:14px;font-size:14px;line-height:1.6}.tariff-plan__impact p{margin:6px 0}.tariff-plan__empty{color:var(--secondary-text-color,#666);font-size:14px}.tariff-plan__overview{grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:12px;display:grid}.tariff-plan__overview>p{margin:0}.tariff-plan__current-price{background:var(--secondary-background-color,#f5f5f5);border-radius:8px;flex-direction:column;gap:4px;padding:12px;display:flex}.tariff-plan__current-price>span{color:var(--secondary-text-color,#666);font-size:14px}.tariff-plan__current-price>strong{font-variant-numeric:tabular-nums;font-size:26px}.tariff-plan__low-status{padding:12px 0;font-size:14px}.tariff-plan__low-unavailable{border-inline-start:3px solid var(--warning-color,#ff9800);padding-inline-start:12px;font-size:14px}.tariff-plan p{overflow-wrap:anywhere;line-height:1.6}.tariff-plan p:last-child{margin-bottom:0}.tariff-plan__scroll{overflow-x:auto}.tariff-plan__table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%;line-height:1.5}.tariff-plan__table th,.tariff-plan__table td{text-align:left;white-space:nowrap;border-bottom:1px solid var(--divider-color,#e0e0e0);padding:10px 8px}.tariff-plan__table th:last-child,.tariff-plan__table td:last-child{text-align:right}.tariff-plan__current{background:var(--secondary-background-color,color-mix(in srgb, currentColor 8%, transparent));font-weight:600}.tariff-plan__header{flex-wrap:wrap;justify-content:space-between;align-items:center;gap:12px;margin-bottom:12px;display:flex}.tariff-plan__header h2{margin:0}.tariff-plan button{font:inherit;cursor:pointer;min-height:44px;color:var(--primary-color,#03a9f4);border:1px solid var(--divider-color,#e0e0e0);background:0 0;border-radius:8px;padding:8px 12px}.tariff-plan button:disabled{cursor:default;opacity:.5}.tariff-plan button:focus-visible,.tariff-plan input:focus-visible,.tariff-plan summary:focus-visible,.tariff-plan__scroll:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.tariff-plan__editor{margin-bottom:16px}.tariff-plan__editor fieldset{border:0;min-width:0;margin:0;padding:0}.tariff-plan__editor label{flex-direction:column;gap:6px;min-width:0;font-size:14px;display:flex}.tariff-plan__editor input{box-sizing:border-box;border:1px solid var(--divider-color,#bbb);width:100%;min-width:0;min-height:44px;font:inherit;font-variant-numeric:tabular-nums;color:var(--primary-text-color,#212121);background:var(--card-background-color,#fff);border-radius:6px;padding:10px}.tariff-plan__editor small,.tariff-plan__hint{color:var(--secondary-text-color,#666);font-size:13px}.tariff-plan__window{border-top:1px solid var(--divider-color,#e0e0e0);grid-template-columns:repeat(2,minmax(0,1fr));align-items:end;gap:12px;margin-top:20px;padding-top:16px;display:grid}.tariff-plan__window-name{grid-column:1/-1;font-size:14px;font-weight:600}.tariff-plan__window label:nth-of-type(3){grid-column:1}.tariff-plan__remove{justify-self:end}.tariff-plan__add{margin-top:16px}.tariff-plan__actions{flex-wrap:wrap;gap:8px;display:flex}.tariff-plan__error{color:var(--error-color,#db4437)}.tariff-plan input[aria-invalid=true]{border-color:var(--error-color,#db4437)}.tariff-plan__details{margin-top:14px;font-size:14px}.tariff-plan__details summary{cursor:pointer;color:var(--secondary-text-color,#666);box-sizing:border-box;min-height:44px;padding:12px 0;line-height:1.5}@media (max-width:400px){.tariff-plan__window{grid-template-columns:minmax(0,1fr)}}@media (max-width:600px){.tariff-plan{padding:20px}}@container sax-content (width>=860px){.tariff-plan{padding:18px}.tariff-plan h2{margin-bottom:12px;font-size:16px}.tariff-plan p{margin-top:10px;line-height:1.5}.tariff-plan__table th,.tariff-plan__table td{padding:7px 8px}}.tariff-plan.tariff-plan--compact{box-shadow:none;background:0 0;border:0;border-radius:0;padding:0}.tariff-plan--compact .tariff-plan__header{border-bottom:1px solid var(--divider-color,#ddd);flex-wrap:nowrap;margin-bottom:14px;padding-bottom:12px}.tariff-plan--compact .tariff-plan__header h2{margin:0;font-size:18px}.tariff-plan--compact .tariff-plan__header button{flex-shrink:0}.tariff-plan__price-highlights{flex-wrap:wrap;justify-content:space-between;align-items:center;gap:8px 16px;margin-bottom:12px;display:flex}.tariff-plan--compact .tariff-plan__low-status{text-align:right;margin:0;padding:0}.tariff-plan__low-status>span{color:var(--secondary-text-color,#666);display:block}.tariff-plan__low-status>strong{font-size:20px;font-weight:500;display:block}.tariff-plan__base-row,.tariff-plan__feed-row{border-top:1px solid var(--divider-color,#ddd);justify-content:space-between;align-items:center;gap:8px 12px;padding:10px 0;display:flex}.tariff-plan__base-row small{color:var(--secondary-text-color,#666);font-size:13px;display:block}.tariff-plan__feed-row>span{color:var(--secondary-text-color,#666)}.tariff-plan__feed-row strong{white-space:nowrap;font-weight:500}.tariff-plan--compact .tariff-plan__periods{margin:0}.tariff-plan--compact .tariff-plan__period-status{color:var(--secondary-text-color,#666);font-size:13px}.tariff-plan--compact .tariff-plan__impact{margin:10px 0 0;padding:8px 10px}.tariff-plan--compact>.tariff-plan__details{border-top:1px solid var(--divider-color,#ddd);margin-top:8px}"]]]);
//#endregion
//#region src/tariff-chart.ts
function tu(e, t = 1e3) {
	let n = Date.parse(e?.start ?? ""), r = Date.parse(e?.end ?? ""), i = Number.isFinite(n) && Number.isFinite(r) && r > n ? (e?.slots ?? []).flatMap((e) => {
		let t = Date.parse(e.start), i = Date.parse(e.end);
		return Number.isFinite(t) && Number.isFinite(i) && i > t && t >= n && i <= r && Number.isFinite(e.price_ct_kwh) ? [{
			...e,
			from: t,
			to: i
		}] : [];
	}).sort((e, t) => e.from - t.from) : [];
	i.some((e, t) => t > 0 && e.from < i[t - 1].to) && i.splice(0);
	let a = Math.min(0, ...i.map((e) => e.price_ct_kwh)), o = Math.max(0, ...i.map((e) => e.price_ct_kwh)), s = Math.max(1, (o - a) * .12), c = a - s, l = o + s, u = (e) => 48 + (e - n) / (r - n) * (t - 60), d = (e) => 26 + (l - e) / (l - c) * 184, f = "";
	return i.forEach((e, t) => {
		let n = i[t - 1];
		f += n && n.to === e.from ? ` V ${d(e.price_ct_kwh)}` : ` M ${u(e.from)} ${d(e.price_ct_kwh)}`, f += ` H ${u(e.to)}`;
	}), {
		start: n,
		end: r,
		slots: i,
		min: c,
		max: l,
		x: u,
		y: d,
		path: f,
		ticks: [.../* @__PURE__ */ new Set([
			a,
			0,
			a + (o - a) / 2,
			o
		])].sort((e, t) => e - t)
	};
}
//#endregion
//#region src/components/TariffPriceChart.vue?vue&type=script&setup=true&lang.ts
var nu = ["aria-busy"], ru = {
	key: 0,
	role: "status"
}, iu = {
	key: 1,
	class: "tariff-price-chart__empty",
	role: "status"
}, au = {
	key: 0,
	class: "tariff-price-chart__partial"
}, ou = ["viewBox", "aria-label"], su = [
	"x2",
	"y1",
	"y2"
], cu = ["y"], lu = ["d"], uu = ["x1", "x2"], du = ["x"], fu = { key: 2 }, pu = [
	"x1",
	"x2",
	"y1",
	"y2"
], mu = ["x", "text-anchor"], hu = {
	class: "tariff-price-chart__detail",
	"aria-live": "polite"
}, gu = { class: "tariff-price-chart__scroll" }, _u = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "TariffPriceChart",
	props: {
		series: { type: [Object, null] },
		hass: { type: Object },
		loading: { type: Boolean }
	},
	setup(e) {
		let t = e, n = Z(() => t.hass?.language?.startsWith("de") ?? !0), r = Z(() => n.value ? {
			empty: "Für diesen Tag sind noch keine Preise verfügbar.",
			partial: "Für Teile des Tages fehlen Preise. Die Lücken werden nicht aufgefüllt.",
			loading: "Preise werden geladen …",
			title: "Strompreise im Tagesverlauf in Cent pro Kilowattstunde",
			hint: "Preisdetails durch Antippen oder mit den Pfeiltasten.",
			table: "Preise als Tabelle",
			from: "Von",
			to: "Bis",
			price: "Preis",
			gap: "Keine Preisdaten",
			now: "Jetzt"
		} : {
			empty: "Prices are not available for this day yet.",
			partial: "Prices are missing for parts of the day. Gaps remain empty.",
			loading: "Loading prices …",
			title: "Electricity prices throughout the day in cents per kilowatt hour",
			hint: "Tap the chart or use the arrow keys for price details.",
			table: "Prices as a table",
			from: "From",
			to: "To",
			price: "Price",
			gap: "No price data",
			now: "Now"
		}), i = /* @__PURE__ */ z(), a = /* @__PURE__ */ z(620), o;
		or(() => {
			typeof ResizeObserver > "u" || !i.value || (o = new ResizeObserver((e) => {
				a.value = Math.max(180, e[0]?.contentRect.width ?? 620);
			}), o.observe(i.value));
		}), cr(() => o?.disconnect());
		let s = Z(() => tu(t.series, a.value)), c = /* @__PURE__ */ z(null);
		V(() => t.series?.start, () => {
			c.value = null;
		});
		let l = (e) => _o(e, t.hass, 2) ?? "—", u = Z(() => {
			if (!t.series) return !1;
			try {
				let e = new Intl.DateTimeFormat("en", {
					timeZone: t.series.time_zone,
					timeZoneName: "shortOffset"
				}), n = (t) => e.formatToParts(new Date(t)).find((e) => e.type === "timeZoneName")?.value;
				return n(Date.parse(t.series.start)) !== n(Date.parse(t.series.end) - 1);
			} catch {
				return !1;
			}
		}), d = (e, n = !1) => vo(e, t.hass, {
			...n && u.value ? {
				hour: "2-digit",
				minute: "2-digit",
				timeZoneName: "shortOffset"
			} : { timeStyle: "short" },
			timeZone: t.series?.time_zone
		}) ?? "—", f = Z(() => {
			let e = c.value;
			return e === null ? -1 : s.value.slots.findIndex((t) => e >= t.from && e < t.to);
		}), p = Z(() => s.value.slots[f.value]), m = Z(() => Date.parse(t.series?.now ?? "")), h = Z(() => m.value >= s.value.start && m.value < s.value.end), g = Z(() => [
			s.value.start,
			s.value.start + (s.value.end - s.value.start) / 2,
			s.value.end
		]);
		function _(e) {
			let t = e.currentTarget.getBoundingClientRect(), n = (e.clientX - t.left) / t.width * a.value;
			c.value = s.value.start + (n - 48) / (a.value - 60) * (s.value.end - s.value.start);
		}
		function v(e) {
			if (![
				"ArrowLeft",
				"ArrowRight",
				"Home",
				"End"
			].includes(e.key) || !s.value.slots.length) return;
			e.preventDefault();
			let t = e.key === "Home" ? 0 : e.key === "End" ? s.value.slots.length - 1 : Math.max(0, Math.min(s.value.slots.length - 1, f.value + (e.key === "ArrowRight" ? 1 : -1)));
			c.value = s.value.slots[t].from;
		}
		return (t, n) => (W(), G("div", {
			ref_key: "container",
			ref: i,
			class: "tariff-price-chart",
			"aria-busy": e.loading
		}, [e.loading && !e.series ? (W(), G("p", ru, F(r.value.loading), 1)) : s.value.slots.length ? (W(), G(U, { key: 2 }, [
			e.series?.status === "partial" ? (W(), G("p", au, F(r.value.partial), 1)) : X("", !0),
			(W(), G("svg", {
				viewBox: `0 0 ${a.value} 252`,
				preserveAspectRatio: "none",
				role: "img",
				"aria-label": `${r.value.title}. ${r.value.hint}`,
				tabindex: "0",
				onPointermove: _,
				onPointerdown: _,
				onKeydown: v
			}, [
				q("title", null, F(r.value.title), 1),
				n[0] ||= q("text", {
					x: "48",
					y: "15"
				}, "ct/kWh", -1),
				(W(!0), G(U, null, H(s.value.ticks, (e) => (W(), G("g", { key: e }, [q("line", {
					x1: "48",
					x2: a.value - 12,
					y1: s.value.y(e),
					y2: s.value.y(e),
					class: "tariff-price-chart__grid"
				}, null, 8, su), q("text", {
					x: "40",
					y: s.value.y(e) + 4,
					"text-anchor": "end"
				}, F(l(e)), 9, cu)]))), 128)),
				q("path", {
					d: s.value.path,
					class: "tariff-price-chart__line"
				}, null, 8, lu),
				h.value ? (W(), G("line", {
					key: 0,
					x1: s.value.x(m.value),
					x2: s.value.x(m.value),
					y1: "25",
					y2: "216",
					class: "tariff-price-chart__now"
				}, null, 8, uu)) : X("", !0),
				h.value ? (W(), G("text", {
					key: 1,
					x: Math.max(68, Math.min(a.value - 30, s.value.x(m.value))),
					y: "23",
					"text-anchor": "middle"
				}, F(r.value.now), 9, du)) : X("", !0),
				p.value ? (W(), G("g", fu, [q("line", {
					x1: s.value.x(p.value.from),
					x2: s.value.x(p.value.to),
					y1: s.value.y(p.value.price_ct_kwh),
					y2: s.value.y(p.value.price_ct_kwh),
					class: "tariff-price-chart__selected"
				}, null, 8, pu)])) : X("", !0),
				(W(!0), G(U, null, H(g.value, (e, t) => (W(), G("text", {
					key: e,
					x: s.value.x(e),
					y: "244",
					"text-anchor": t === 0 ? "start" : t === 2 ? "end" : "middle"
				}, F(t === 2 ? "24:00" : d(new Date(e).toISOString())), 9, mu))), 128))
			], 40, ou)),
			q("p", hu, F(p.value ? `${d(p.value.start, !0)}–${d(p.value.end, !0)} · ${l(p.value.price_ct_kwh)} ct/kWh` : c.value === null ? r.value.hint : r.value.gap), 1),
			q("details", null, [q("summary", null, F(r.value.table), 1), q("div", gu, [q("table", null, [q("thead", null, [q("tr", null, [
				q("th", null, F(r.value.from), 1),
				q("th", null, F(r.value.to), 1),
				q("th", null, F(r.value.price), 1)
			])]), q("tbody", null, [(W(!0), G(U, null, H(s.value.slots, (e) => (W(), G("tr", { key: e.start }, [
				q("td", null, F(d(e.start, !0)), 1),
				q("td", null, F(d(e.end, !0)), 1),
				q("td", null, F(l(e.price_ct_kwh)) + " ct/kWh", 1)
			]))), 128))])])])])
		], 64)) : (W(), G("div", iu, F(r.value.empty), 1))], 8, nu));
	}
}), [["styles", [".tariff-price-chart{min-width:0}.tariff-price-chart svg{touch-action:pan-y;width:100%;height:240px;display:block;overflow:visible}.tariff-price-chart svg text{fill:var(--secondary-text-color,#666);font-size:14px}.tariff-price-chart__line{fill:none;stroke:var(--primary-color,#03a9f4);stroke-width:3px;vector-effect:non-scaling-stroke}.tariff-price-chart__grid{stroke:var(--divider-color,#ddd);vector-effect:non-scaling-stroke}.tariff-price-chart__now{stroke:var(--secondary-text-color,#666);stroke-dasharray:4;vector-effect:non-scaling-stroke}.tariff-price-chart__selected{stroke:var(--success-color,#38964b);stroke-width:6px;vector-effect:non-scaling-stroke}.tariff-price-chart__empty{text-align:center;min-height:240px;color:var(--secondary-text-color,#666);place-items:center;display:grid}.tariff-price-chart__detail,.tariff-price-chart__partial{min-height:20px;color:var(--secondary-text-color,#666);font-size:14px}.tariff-price-chart summary{cursor:pointer;min-height:32px;padding:6px 0}.tariff-price-chart__scroll{overflow:auto}.tariff-price-chart table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%}.tariff-price-chart th,.tariff-price-chart td{text-align:left;border-bottom:1px solid var(--divider-color,#ddd);white-space:nowrap;padding:8px}.tariff-price-chart th:last-child,.tariff-price-chart td:last-child{text-align:right}"]]]), vu = ["aria-busy"], yu = ["aria-busy"], bu = { class: "entity-control__description" }, xu = ["for"], Su = ["id"], Cu = ["id"], wu = { class: "entity-control__input" }, Tu = [
	"id",
	"value",
	"min",
	"max",
	"step",
	"disabled",
	"aria-describedby",
	"aria-invalid",
	"onInput"
], Eu = ["id"], Du = {
	key: 0,
	class: "entity-control__error",
	role: "alert"
}, Ou = {
	key: 1,
	role: "status",
	"aria-live": "polite"
}, ku = /* @__PURE__ */ Gn({
	__name: "ChargingNumberFields",
	props: {
		fields: { type: Array },
		socThresholdApplies: {
			type: Boolean,
			default: !0
		},
		disabled: {
			type: Boolean,
			default: !1
		}
	},
	emits: ["apply"],
	setup(e, { expose: t, emit: n }) {
		let r = e, i = n, a = Pn(Co), o = `sax-charging-number-${Kn()}`, s = /* @__PURE__ */ Nt({}), c = /* @__PURE__ */ Nt({}), l = /* @__PURE__ */ new Map(), u = /* @__PURE__ */ z(!1), d = 0, f = Z(() => a?.language.value === "de" ? {
			pending: "Änderung wird an Home Assistant gesendet …",
			invalid: "Bitte einen gültigen Wert im erlaubten Bereich eingeben.",
			order: "Das Netzladeziel muss mindestens so hoch wie der Ladestart sein.",
			failed: "Die Änderung ist fehlgeschlagen. Bitte erneut versuchen.",
			unavailable: "Nicht verfügbar",
			readonly: "Keine Berechtigung zum Ändern",
			disconnected: "Keine Verbindung zu Home Assistant"
		} : {
			pending: "Sending change to Home Assistant …",
			invalid: "Please enter a valid value within the allowed range.",
			order: "The grid charge target must be at least as high as the start threshold.",
			failed: "The change failed. Please try again.",
			unavailable: "Unavailable",
			readonly: "You do not have permission to change this setting",
			disconnected: "Disconnected from Home Assistant"
		});
		function p(e) {
			return a?.entity("number", e) ?? null;
		}
		let m = Z(() => u.value || r.fields.some((e) => p(e.key)?.pending));
		function h(e) {
			return r.disabled || m.value || !a?.ready.value || !p(e)?.canControl;
		}
		function g(e) {
			return e.trim() === "" ? null : Q(e);
		}
		function _(e) {
			let t = s[e];
			return !!t && t.edited && g(t.value) !== g(t.confirmed);
		}
		function v(e, t) {
			if (e === "timed_charge_max_soc" && t === "max") {
				let e = r.fields.some((e) => e.key === "max_soc") ? g(s.max_soc?.value ?? "") : null;
				if (e !== null) return e;
			}
			let n = p(e)?.state?.attributes[t];
			return typeof n == "number" && Number.isFinite(n) ? n : void 0;
		}
		V(() => r.fields.map(({ key: e }) => [
			e,
			p(e)?.metadata.entity_id,
			p(e)?.state?.state
		]), () => {
			for (let { key: e } of r.fields) {
				let t = p(e), n = t?.metadata.entity_id ?? null, r = t?.state?.state ?? "", i = s[e];
				!i || n && n !== i.entityId ? (d += 1, s[e] = {
					entityId: n,
					confirmed: r,
					value: t?.available && g(r) !== null ? r : "",
					edited: !1
				}, delete c[e]) : n && r !== i.confirmed && (i.confirmed = r, (!i.edited || g(i.value) === g(r)) && (i.value = t?.available && g(r) !== null ? r : "", i.edited = !1, delete c[e]));
			}
		}, {
			immediate: !0,
			flush: "sync"
		}), cr(() => {
			d += 1;
		});
		function y(e, t) {
			if (h(e)) return;
			let n = s[e];
			n && (n.value = t.target.value, n.edited = !0, delete c[e], a?.clearControlError("number", e));
		}
		function b(e, t) {
			t instanceof HTMLInputElement ? l.set(e, t) : l.delete(e);
		}
		function x(e) {
			let t = c[e];
			return t ? f.value[t] : p(e)?.error ?? null;
		}
		function S(e) {
			return m.value ? f.value.pending : a?.connected.value ? p(e)?.available ? p(e)?.metadata.can_control ? "" : f.value.readonly : f.value.unavailable : f.value.disconnected;
		}
		function C(e, t) {
			return c[e] = t, l.get(e)?.focus(), !1;
		}
		function w() {
			m.value || i("apply");
		}
		function T() {
			if (m.value) return !1;
			for (let e of Object.keys(s)) {
				let t = p(e), n = t?.state?.state ?? "", r = t?.available && g(n) !== null ? n : "";
				s[e] = {
					entityId: t?.metadata.entity_id ?? null,
					confirmed: n,
					value: r,
					edited: !1
				};
				let i = l.get(e);
				i && (i.value = r), delete c[e], a?.clearControlError("number", e);
			}
			return !0;
		}
		function E() {
			if (m.value || r.disabled || !a) return null;
			let e = (e, t) => (C(e, t), null);
			for (let { key: e } of r.fields) {
				let t = l.get(e), n = s[e];
				t && n && t.value !== n.value && (n.value = t.value, n.edited = !0, delete c[e], a.clearControlError("number", e));
			}
			let t = r.fields.filter(({ key: e }) => _(e));
			if (!t.length) {
				for (let e of Object.keys(c)) delete c[e];
				return {};
			}
			for (let { key: t } of r.fields) {
				delete c[t];
				let n = p(t);
				if (!n?.available) {
					if (_(t)) return e(t, "unavailable");
					continue;
				}
				if (_(t) && (!n.canControl || !a.ready.value)) return e(t, "readonly");
				let r = g(s[t]?.value ?? ""), i = v(t, "min"), o = v(t, "min_positive"), u = v(t, "max"), d = v(t, "step");
				if (r === null || l.get(t)?.validity.badInput || i === void 0 || u === void 0 || d === void 0 || d <= 0 || i > u || r < i || r > 0 && o !== void 0 && r < o || r > u && (t !== "timed_charge_max_soc" || _(t)) || !Number.isFinite((r - i) / d) || Math.abs((r - i) / d - Math.round((r - i) / d)) > 1e-7) return e(t, "invalid");
			}
			let n = "timed_charge_min_soc", i = "timed_charge_max_soc", o = t.some(({ key: e }) => e === n), u = t.some(({ key: e }) => e === i);
			if (r.socThresholdApplies !== !1 && (o || u)) {
				let t = (e) => r.fields.some((t) => t.key === e) ? g(s[e]?.value ?? "") : p(e)?.available ? g(p(e)?.state?.state ?? "") : null, a = t(n), l = t(i);
				if (a !== null && l !== null && a > l) return o && u && (c[n] = "order"), e(u ? i : n, "order");
			}
			return Object.fromEntries(t.map(({ key: e }) => [e, g(s[e].value)]));
		}
		async function D() {
			let e = E();
			if (!e || !a) return !1;
			let t = r.fields.filter(({ key: t }) => t in e);
			if (!t.length) return !0;
			let n = "timed_charge_min_soc", i = "timed_charge_max_soc", o = t.some(({ key: e }) => e === n), m = t.some(({ key: e }) => e === i);
			u.value = !0;
			let h = d, g = t.map(({ key: e }) => [e, s[e]?.entityId]);
			try {
				let e = await a.performChargingSettings(Object.fromEntries(t.map(({ key: e }) => [e, s[e].value])));
				if (d !== h || g.some(([e, t]) => p(e)?.metadata.entity_id !== t)) return !1;
				if (!e) {
					let e = t.some(({ key: e }) => p(e)?.error === f.value.order);
					e && o && m && (c[n] = "order", c[i] = "order");
					let r = e ? t.find(({ key: e }) => e === (m ? i : n)) ?? t[0] : t.find(({ key: e }) => p(e)?.error) ?? t[0];
					p(r.key)?.error || (c[r.key] = "failed"), u.value = !1, await vn(), d === h && l.get(r.key)?.focus();
				}
				return e;
			} catch {
				return u.value = !1, await vn(), d === h && C(t[0].key, "failed"), !1;
			} finally {
				u.value = !1;
			}
		}
		return t({
			submit: D,
			prepare: E,
			reset: T,
			pending: m
		}), (t, n) => (W(), G("div", {
			class: "charging-number-fields",
			"aria-busy": m.value
		}, [(W(!0), G(U, null, H(e.fields, (e) => (W(), G("form", {
			key: e.key,
			class: "entity-control",
			"aria-busy": m.value,
			onSubmit: io(w, ["prevent"])
		}, [
			q("div", bu, [
				q("label", {
					for: `${o}-${e.key}`,
					class: "entity-control__name"
				}, F(e.label), 9, xu),
				q("p", {
					id: `${o}-${e.key}-value`,
					class: "entity-control__value"
				}, F(p(e.key)?.displayValue ?? f.value.unavailable), 9, Su),
				e.hint ? (W(), G("p", {
					key: 0,
					id: `${o}-${e.key}-hint`,
					class: "entity-control__value"
				}, F(e.hint), 9, Cu)) : X("", !0)
			]),
			q("div", wu, [q("input", {
				id: `${o}-${e.key}`,
				ref_for: !0,
				ref: (t) => b(e.key, t),
				value: s[e.key]?.value ?? "",
				type: "number",
				min: v(e.key, "min"),
				max: v(e.key, "max"),
				step: v(e.key, "step"),
				disabled: h(e.key),
				"aria-describedby": [
					`${o}-${e.key}-value`,
					e.hint && `${o}-${e.key}-hint`,
					`${o}-${e.key}-status`
				].filter(Boolean).join(" "),
				"aria-invalid": !!x(e.key),
				required: "",
				onInput: (t) => y(e.key, t),
				onInvalid: io(w, ["prevent"])
			}, null, 40, Tu)]),
			q("div", {
				id: `${o}-${e.key}-status`,
				class: "entity-control__feedback"
			}, [x(e.key) ? (W(), G("p", Du, F(x(e.key)), 1)) : S(e.key) ? (W(), G("p", Ou, F(S(e.key)), 1)) : X("", !0)], 8, Eu)
		], 40, yu))), 128))], 8, vu));
	}
});
//#endregion
//#region src/charging-months.ts
function Au(e) {
	let t = Array.from({ length: 12 }, (e, t) => `timed_charge_month_${t + 1}`);
	return {
		monthKeys: t,
		monthSummary: Z(() => {
			let n = e?.language.value === "de", r = n ? "Monatsauswahl nicht vollständig bekannt" : "Month selection is not fully known", i = new Intl.DateTimeFormat(n ? "de" : "en", {
				month: "short",
				timeZone: "UTC"
			}), a = t.map((t, n) => {
				let r = e?.entity("switch", t), a = r?.state?.state;
				return {
					known: r?.available && (a === "on" || a === "off"),
					selected: r?.available && a === "on",
					name: i.format(new Date(Date.UTC(2024, n, 1)))
				};
			}), o = a.filter((e) => e.selected), s = a.some((e) => !e.known);
			return o.length === 12 ? n ? "Ganzjährig" : "All year" : o.length ? `${o.map((e) => e.name).join(", ")}${s ? ` · ${r}` : ""}` : s ? r : n ? "Keine ausgewählt · Automatische Netzladung ganzjährig inaktiv" : "None selected · Automatic grid charging inactive all year";
		})
	};
}
//#endregion
//#region src/components/FixedTimeChargingInput.vue?vue&type=script&setup=true&lang.ts
var ju = [
	"value",
	"disabled",
	"aria-invalid",
	"aria-describedby"
], Mu = ["id"], Nu = ["id"], Pu = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "FixedTimeChargingInput",
	props: {
		modelValue: { type: String },
		disabled: { type: Boolean },
		error: { type: [String, null] }
	},
	emits: ["update:modelValue", "apply"],
	setup(e, { expose: t, emit: n }) {
		let r = e, i = n, a = Pn(Co), o = /* @__PURE__ */ z(), s = `sax-fixed-start-${Kn()}`, c = Z(() => a?.language.value === "de" ? {
			start: "Täglicher Ladestart",
			hint: "Lädt ab dieser Uhrzeit unabhängig vom Ladestart-SOC und Strompreis bis zum maximalen Netzlade-SOC. Die globale Grenze Max SOC gilt weiterhin. Die automatische Netzladung muss eingeschaltet sein.",
			invalid: "Bitte eine vollständige Uhrzeit im Format HH:MM eingeben, zum Beispiel 02:00.",
			failed: "Die Änderung ist fehlgeschlagen. Dein Entwurf bleibt erhalten.",
			conflict: "Die Einstellungen wurden inzwischen geändert. Dein Entwurf bleibt erhalten. Bitte erneut übernehmen."
		} : {
			start: "Daily charging start",
			hint: "Charges from this time regardless of the start SOC and electricity price until the maximum grid charging SOC is reached. The global Max SOC limit still applies. Automatic grid charging must be on.",
			invalid: "Enter a complete time in HH:MM format, for example 02:00.",
			failed: "The change failed. Your draft is preserved.",
			conflict: "The settings have changed elsewhere. Your draft is preserved. Please apply it again."
		});
		return t({
			value: () => o.value?.value ?? r.modelValue,
			focus: () => o.value?.focus()
		}), (t, n) => (W(), G("form", {
			class: "fixed-time-charging-input",
			onSubmit: n[2] ||= io((e) => i("apply"), ["prevent"])
		}, [
			q("label", { for: s }, F(c.value.start), 1),
			q("input", {
				id: s,
				ref_key: "input",
				ref: o,
				value: e.modelValue,
				type: "text",
				inputmode: "numeric",
				placeholder: "02:00",
				autocomplete: "off",
				disabled: e.disabled,
				"aria-invalid": e.error === "invalid",
				"aria-describedby": `${s}-hint${e.error ? ` ${s}-error` : ""}`,
				onInput: n[0] ||= (e) => i("update:modelValue", e.target.value),
				onChange: n[1] ||= (e) => i("update:modelValue", B(zs)(e.target.value))
			}, null, 40, ju),
			q("p", {
				id: `${s}-hint`,
				class: "electricity-muted"
			}, F(c.value.hint), 9, Mu),
			e.error ? (W(), G("p", {
				key: 0,
				id: `${s}-error`,
				class: "electricity-error",
				role: "alert"
			}, F(c.value[e.error]), 9, Nu)) : X("", !0)
		], 32));
	}
}), [["styles", [".fixed-time-charging-input{gap:8px;margin-top:16px;display:grid}.fixed-time-charging-input input{box-sizing:border-box;border:1px solid var(--divider-color,#ddd);background:var(--card-background-color,#fff);width:12ch;max-width:100%;min-height:44px;color:var(--primary-text-color,#212121);font:inherit;border-radius:6px;padding:10px}.fixed-time-charging-input p{margin:0;line-height:1.6}.fixed-time-charging-input input:focus-visible{outline:3px solid var(--primary-color,#03a9f4);outline-offset:2px}.fixed-time-charging-input input[aria-invalid=true]{border-color:var(--error-color,#b00020)}"]]]);
//#endregion
//#region src/fixed-time-charging.ts
function Fu(e) {
	function t(e) {
		return e && /^\d{2}:\d{2}:00$/.test(e) ? e.slice(0, 5) : e ?? "02:00";
	}
	let n = Z(() => e?.tariff.value?.fixed_time_charging), r = Z(() => n.value?.enabled === !0), i = /* @__PURE__ */ z(r.value), a = /* @__PURE__ */ z(t(n.value?.start)), o = /* @__PURE__ */ z(!1), s = /* @__PURE__ */ z(!1), c = /* @__PURE__ */ z(null), l = Z(() => e?.ready.value === !0 && e.connected.value === !0 && e.tariff.value?.can_configure === !0);
	V(n, (e) => {
		o.value || (i.value = e?.enabled === !0, a.value = t(e?.start));
	}, { immediate: !0 });
	function u() {
		return !s.value && (o.value = !1, i.value = r.value, a.value = t(n.value?.start), c.value = null, !0);
	}
	function d() {
		!s.value && l.value && (i.value = !0, o.value = !0, c.value = null);
	}
	function f(e) {
		a.value = e, o.value = !0, c.value = null;
	}
	function p(e = a.value) {
		return !i.value || (a.value = zs(e), $(a.value) === null ? (c.value = "invalid", !1) : (c.value = null, !0));
	}
	async function m(u, d) {
		let f = e?.tariff.value;
		if (s.value || !l.value || !e || !f) return !1;
		s.value = !0, c.value = null;
		try {
			return await e.configureTariff({
				revision: f.revision,
				tariff_type: f.tariff_type,
				...d && Object.keys(d).length ? { charging_settings: d } : {},
				...u ? { charging_method: u } : { fixed_time_charging: {
					enabled: !0,
					start: a.value
				} }
			}), o.value = !1, i.value = r.value, a.value = t(n.value?.start), !0;
		} catch (t) {
			if (c.value = t?.code === "conflict" ? "conflict" : "failed", c.value === "conflict") try {
				await e.loadTariff();
			} catch {}
			return !1;
		} finally {
			s.value = !1;
		}
	}
	async function h(e) {
		return i.value ? p() ? (!e || !Object.keys(e).length) && r.value && $(a.value) === $(n.value?.start ?? "") ? (o.value = !1, !0) : m(void 0, e) : !1 : !0;
	}
	async function g(e, t) {
		s.value || (c.value = null, r.value ? await m(e) : (i.value = !1, o.value = !1, await t()));
	}
	return {
		active: r,
		selected: i,
		start: a,
		pending: s,
		error: c,
		canConfigure: l,
		reset: u,
		choose: d,
		edit: f,
		validate: p,
		submit: h,
		leave: g
	};
}
//#endregion
//#region src/components/DynamicChargingSettings.vue?vue&type=script&setup=true&lang.ts
var Iu = { class: "dynamic-charging-settings" }, Lu = { class: "dynamic-charging-summary" }, Ru = { class: "electricity-summary-rows" }, zu = {
	key: 0,
	class: "electricity-targets"
}, Bu = { class: "electricity-target" }, Vu = { class: "electricity-target" }, Hu = {
	key: 1,
	class: "electricity-summary-rows fixed-time-month-summary"
}, Uu = {
	key: 0,
	class: "electricity-muted dynamic-charging-neutral-summary"
}, Wu = {
	key: 1,
	class: "electricity-error",
	role: "alert"
}, Gu = {
	key: 2,
	role: "status",
	"aria-live": "polite"
}, Ku = {
	key: 3,
	class: "dynamic-charging-editor"
}, qu = ["aria-label", "aria-busy"], Ju = [
	"data-strategy",
	"aria-pressed",
	"disabled",
	"onClick"
], Yu = ["aria-pressed", "disabled"], Xu = {
	key: 1,
	class: "electricity-error",
	role: "alert"
}, Zu = { class: "electricity-muted" }, Qu = {
	key: 0,
	class: "dynamic-charging-notice"
}, $u = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "DynamicChargingSettings",
	props: { editing: { type: Boolean } },
	emits: ["apply"],
	setup(e, { expose: t, emit: n }) {
		let r = e, i = n, a = /* @__PURE__ */ z(), o = Pn(Co), s = Fu(o), c = /* @__PURE__ */ z(), l = Z(() => s.pending.value || a.value?.pending || _.value?.pending || !1), u = Z(() => s.pending.value || a.value?.pending || !1);
		async function d() {
			if (u.value) return !1;
			if (!s.validate(c.value?.value())) return c.value?.focus(), !1;
			if (s.selected.value) {
				let e = a.value?.prepare() ?? null;
				return e !== null && s.submit(e);
			}
			return await a.value?.submit() ?? !0;
		}
		t({
			submit: d,
			reset: () => !u.value && s.reset() && (a.value?.reset() ?? !0),
			pending: u
		});
		let { monthKeys: f, monthSummary: p } = Au(o), m = /* @__PURE__ */ z(r.editing);
		V(() => r.editing, (e) => {
			e && (m.value = !0);
		});
		let h = Z(() => o?.language.value === "de"), g = Z(() => h.value ? {
			mode: "Ladeweise",
			fixedTime: "Ab fester Uhrzeit",
			months: "Aktive Monate",
			global: "Max SOC (%)",
			globalSummary: "Max SOC",
			saved: "Ladeweise",
			targetLabel: "Netzladeziel (%)",
			targetHint: "Globale Ladegrenze · gilt auch für Solarstrom.",
			hours: "Maximale Ladezeit je 24 Stunden",
			price: "Höchster Preis zum Laden (ct/kWh)",
			noPriceLimit: "Keine feste Preisgrenze.",
			neutral: "Speicher bei günstigem Strom schonen bis (ct/kWh)",
			neutralSummary: "Speicher schonen unter",
			neutralBand: "und oberhalb der Ladepreisgrenze",
			neutralInactive: "Speicher schonen: ohne Wirkung.",
			neutralUnavailable: "Grenze zum Schonen des Speichers nicht verfügbar.",
			unavailable: "Ladeweise nicht verfügbar.",
			readonly: "Keine Berechtigung zum Ändern der Ladeweise.",
			disconnected: "Keine Verbindung zu Home Assistant.",
			pending: "Ladeweise wird übernommen …",
			targetSummary: "Netzladeziel",
			modes: {
				smart: "Bedarfsgerecht laden",
				relative: "Günstigste Stunden nutzen",
				absolute: "Bis zu einem festen Preis laden",
				off: "Keine automatische Ladung"
			}
		} : {
			mode: "Charging method",
			fixedTime: "Start at a fixed time",
			months: "Active months",
			global: "Max SOC (%)",
			globalSummary: "Max SOC",
			saved: "Charging method",
			targetLabel: "Grid charge target (%)",
			targetHint: "Global charge limit · also applies to solar charging.",
			hours: "Maximum charging time per 24 hours",
			price: "Maximum price for charging (ct/kWh)",
			noPriceLimit: "No fixed price cap.",
			neutral: "Preserve battery energy below (ct/kWh)",
			neutralSummary: "Preserve battery energy below",
			neutralBand: "and above the charging price cap",
			neutralInactive: "Preserving battery energy: no effect.",
			neutralUnavailable: "Battery preservation threshold unavailable.",
			unavailable: "Charging method unavailable.",
			readonly: "You do not have permission to change the charging method.",
			disconnected: "Disconnected from Home Assistant.",
			pending: "Applying charging method …",
			targetSummary: "Grid charge target",
			modes: {
				smart: "Charge what is needed",
				relative: "Use the cheapest hours",
				absolute: "Charge below a fixed price",
				off: "No automatic charging"
			}
		}), _ = Z(() => o?.entity("select", "price_charge_strategy")), v = [
			"smart",
			"relative",
			"absolute",
			"off"
		], y = Z(() => {
			if (s.active.value && o?.connected.value) return "fixed_time";
			let e = _.value?.state?.state;
			return _.value?.available && v.includes(e) ? e : null;
		}), b = Z(() => s.selected.value ? "fixed_time" : y.value), x = Z(() => _.value?.state?.attributes.options), S = Z(() => !_.value?.canControl || l.value), C = Z(() => o?.connected.value ? _.value?.available ? _.value.metadata.can_control ? s.pending.value || _.value.pending ? g.value.pending : "" : g.value.readonly : g.value.unavailable : g.value.disconnected), w = Z(() => o?.entity("number", "max_soc")), T = Z(() => o?.entity("number", "timed_charge_max_soc")), E = Z(() => b.value === "fixed_time" ? [{
			key: "timed_charge_max_soc",
			label: g.value.targetLabel
		}, {
			key: "max_soc",
			label: g.value.global
		}] : b.value && b.value !== "off" ? [
			{
				key: "max_soc",
				label: g.value.targetLabel
			},
			b.value === "absolute" ? {
				key: "price_charge_max_price",
				label: g.value.price
			} : {
				key: "price_charge_hours",
				label: g.value.hours
			},
			{
				key: "price_charge_neutral_price",
				label: g.value.neutral
			}
		] : []), D = Z(() => o?.entity("number", y.value === "absolute" ? "price_charge_max_price" : "price_charge_hours")), O = Z(() => {
			let e = o?.entity("number", "price_charge_neutral_price"), t = o?.entity("number", "price_charge_max_price"), n = Q(e?.state?.state), r = Q(t?.state?.state);
			return !e?.available || n === null || y.value === "absolute" && (!t?.available || r === null) ? g.value.neutralUnavailable : y.value === "absolute" && r !== null && n <= r ? g.value.neutralInactive : `${g.value.neutralSummary} ${e.displayValue}${y.value === "absolute" ? ` ${g.value.neutralBand}` : ""}.`;
		});
		async function k(e) {
			if (!S.value && Array.isArray(x.value) && x.value.includes(e)) {
				if (y.value === e) {
					s.selected.value && s.reset();
					return;
				}
				await s.leave(e, () => o.perform("select", "price_charge_strategy", e));
			}
		}
		return (t, n) => (W(), G("div", Iu, [
			q("div", Lu, [
				q("dl", Ru, [q("div", null, [q("dt", null, F(g.value.saved), 1), q("dd", null, F(y.value === "fixed_time" ? g.value.fixedTime : y.value ? g.value.modes[y.value] : g.value.unavailable), 1)])]),
				y.value && y.value !== "off" ? (W(), G("div", zu, [q("div", Bu, [q("span", null, F(g.value.targetSummary), 1), q("strong", null, F(y.value === "fixed_time" ? T.value?.available ? T.value.displayValue : "—" : w.value?.available ? w.value.displayValue : "—"), 1)]), q("div", Vu, [q("span", null, F(y.value === "fixed_time" ? g.value.globalSummary : y.value === "absolute" ? g.value.price : g.value.hours), 1), q("strong", null, F(y.value === "fixed_time" ? w.value?.available ? w.value.displayValue : "—" : D.value?.available ? D.value.displayValue : "—"), 1)])])) : X("", !0),
				y.value === "fixed_time" ? (W(), G("dl", Hu, [q("div", null, [q("dt", null, F(g.value.months), 1), q("dd", null, F(B(p)), 1)])])) : X("", !0)
			]),
			y.value && y.value !== "off" && y.value !== "fixed_time" ? (W(), G("p", Uu, F(O.value), 1)) : X("", !0),
			_.value?.error ? (W(), G("p", Wu, F(_.value.error), 1)) : C.value ? (W(), G("p", Gu, F(C.value), 1)) : X("", !0),
			m.value ? jn((W(), G("div", Ku, [
				q("h3", null, F(g.value.mode), 1),
				q("div", {
					class: "dynamic-charging-methods",
					role: "group",
					"aria-label": g.value.mode,
					"aria-busy": l.value
				}, [(W(), G(U, null, H(v, (e) => q("button", {
					key: e,
					type: "button",
					"data-strategy": e,
					"aria-pressed": b.value === e,
					disabled: S.value || !Array.isArray(x.value) || !x.value.includes(e),
					onClick: (t) => k(e)
				}, [q("strong", null, F(g.value.modes[e]), 1)], 8, Ju)), 64)), q("button", {
					type: "button",
					"data-strategy": "fixed_time",
					"aria-pressed": b.value === "fixed_time",
					disabled: S.value || !B(s).canConfigure.value,
					onClick: n[0] ||= (...e) => B(s).choose && B(s).choose(...e)
				}, [q("strong", null, F(g.value.fixedTime), 1)], 8, Yu)], 8, qu),
				b.value === "fixed_time" ? (W(), K(Pu, {
					key: 0,
					ref_key: "timeInput",
					ref: c,
					"model-value": B(s).start.value,
					disabled: S.value || !B(s).canConfigure.value,
					error: B(s).error.value,
					"onUpdate:modelValue": B(s).edit,
					onApply: n[1] ||= (e) => i("apply")
				}, null, 8, [
					"model-value",
					"disabled",
					"error",
					"onUpdate:modelValue"
				])) : X("", !0),
				B(s).error.value && b.value !== "fixed_time" ? (W(), G("p", Xu, F(h.value ? "Die Änderung ist fehlgeschlagen. Bitte erneut versuchen." : "The change failed. Please try again."), 1)) : X("", !0),
				J(ku, {
					ref_key: "numbers",
					ref: a,
					fields: E.value,
					"soc-threshold-applies": b.value !== "fixed_time",
					disabled: B(s).pending.value,
					onApply: n[2] ||= (e) => i("apply")
				}, null, 8, [
					"fields",
					"soc-threshold-applies",
					"disabled"
				]),
				b.value === "fixed_time" ? (W(), G(U, { key: 2 }, [q("h3", null, F(g.value.months), 1), J(Rs, {
					"entity-keys": B(f),
					"always-expanded": ""
				}, null, 8, ["entity-keys"])], 64)) : X("", !0),
				b.value && b.value !== "off" && b.value !== "fixed_time" ? (W(), G(U, { key: 3 }, [q("p", Zu, F(g.value.targetHint), 1), b.value === "absolute" ? X("", !0) : (W(), G("p", Qu, F(g.value.noPriceLimit), 1))], 64)) : X("", !0)
			], 512)), [[ua, e.editing]]) : X("", !0)
		]));
	}
}), [["styles", [".dynamic-charging-methods{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:16px;display:grid}.dynamic-charging-methods button{text-align:left;color:var(--primary-text-color,#212121);padding:12px}.dynamic-charging-methods button[aria-pressed=true]{border:2px solid var(--primary-color,#03a9f4);background:var(--secondary-background-color,#f5f5f5);padding:11px}.dynamic-charging-methods strong{line-height:1.5;display:block}.dynamic-charging-editor>.entity-control{box-shadow:none;background:0 0;border:0;border-radius:0;padding:12px 0}.dynamic-charging-notice{border-left:3px solid var(--primary-color,#03a9f4);padding-left:12px}@media (max-width:700px){.dynamic-charging-methods{grid-template-columns:minmax(0,1fr)}}"]]]), ed = { class: "tou-charging-settings" }, td = { class: "tou-charging-summary" }, nd = { class: "electricity-summary-rows" }, rd = {
	key: 0,
	class: "electricity-target tou-charging-threshold"
}, id = { class: "electricity-target tou-charging-target" }, ad = { class: "electricity-target tou-charging-global" }, od = {
	key: 1,
	class: "electricity-summary-rows"
}, sd = { class: "electricity-summary-rows tou-charging-month-summary" }, cd = {
	key: 0,
	class: "tou-charging-error",
	role: "alert"
}, ld = {
	key: 1,
	class: "tou-charging-error",
	role: "alert"
}, ud = {
	key: 2,
	role: "status",
	"aria-live": "polite"
}, dd = {
	key: 0,
	class: "tou-charging-editor"
}, fd = ["aria-label", "aria-busy"], pd = [
	"data-method",
	"aria-pressed",
	"disabled",
	"onClick"
], md = ["aria-pressed", "disabled"], hd = {
	key: 1,
	class: "tou-charging-hint"
}, gd = { class: "tou-charging-limits" }, _d = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "TimeOfUseChargingSettings",
	props: {
		editing: { type: Boolean },
		hass: { type: Object }
	},
	emits: ["apply"],
	setup(e, { expose: t, emit: n }) {
		let r = e, i = n, a = /* @__PURE__ */ z(), o = Pn(Co), s = Fu(o), c = /* @__PURE__ */ z(), l = Z(() => s.pending.value || a.value?.pending || g.value?.pending || !1), u = Z(() => s.pending.value || a.value?.pending || !1);
		async function d() {
			if (u.value) return !1;
			if (!s.validate(c.value?.value())) return c.value?.focus(), !1;
			if (s.selected.value) {
				let e = a.value?.prepare() ?? null;
				return e !== null && s.submit(e);
			}
			return await a.value?.submit() ?? !0;
		}
		t({
			submit: d,
			reset: () => !u.value && s.reset() && (a.value?.reset() ?? !0),
			pending: u
		});
		let f = Z(() => o?.language.value === "de"), p = `sax-tou-method-${Kn()}`, m = /* @__PURE__ */ z(r.editing);
		V(() => r.editing, (e) => {
			e && (m.value = !0);
		});
		let h = Z(() => f.value ? {
			saved: "Ladeweise",
			start: "Start nur unter",
			startAtZero: "Start bei",
			mode: "Ladeweise",
			fixed: "Festes Netzladeziel",
			fixed_time: "Ab fester Uhrzeit",
			bridge: "Nur Bedarf bis Solarstrom",
			target: "Netzladeziel",
			fixedTarget: "Netzladeziel (%)",
			bridgeTarget: "Maximales Netzladeziel (%)",
			minimumEnergy: "Mindestlademenge",
			noMinimum: "Keine",
			minimumHint: "0 kWh für reine Bedarfsladung oder mindestens 0,5 kWh.",
			socBuffer: "SOC-Puffer",
			bufferHint: "Akkustand, der bis zum PV-Start möglichst erhalten bleiben soll.",
			pvRequired: "PV-Prognose fehlt · unter „Preise & Zeiten“ ergänzen.",
			months: "Aktive Monate",
			allYear: "Ganzjährig",
			noMonths: "Keine ausgewählt · Automatische Netzladung ganzjährig inaktiv",
			unknownMonths: "Monatsauswahl nicht vollständig bekannt",
			threshold: "Ladestart unter (%)",
			maxSoc: "Max SOC",
			global: "Max SOC (%)",
			unavailable: "Ladeweise nicht verfügbar.",
			valueUnavailable: "Nicht verfügbar",
			readonly: "Keine Berechtigung zum Ändern der Ladeweise.",
			disconnected: "Keine Verbindung zu Home Assistant.",
			pending: "Ladeweise wird übernommen …"
		} : {
			saved: "Charging method",
			start: "Start only below",
			startAtZero: "Start at",
			mode: "Charging method",
			fixed: "Fixed grid charge target",
			fixed_time: "Start at a fixed time",
			bridge: "Only what is needed until solar power",
			target: "Grid charge target",
			fixedTarget: "Grid charge target (%)",
			bridgeTarget: "Maximum grid charge target (%)",
			minimumEnergy: "Minimum charging energy",
			noMinimum: "None",
			minimumHint: "Enter 0 kWh to charge according to need, or at least 0.5 kWh.",
			socBuffer: "SOC buffer",
			bufferHint: "Battery level to preserve until solar production starts.",
			pvRequired: "Solar forecast missing · add it under Prices & times.",
			months: "Active months",
			allYear: "All year",
			noMonths: "None selected · Automatic grid charging inactive all year",
			unknownMonths: "Month selection is not fully known",
			threshold: "Start threshold (%)",
			maxSoc: "Max SOC",
			global: "Max SOC (%)",
			unavailable: "Charging method unavailable.",
			valueUnavailable: "Unavailable",
			readonly: "You do not have permission to change the charging method.",
			disconnected: "Disconnected from Home Assistant.",
			pending: "Applying charging method …"
		}), g = Z(() => o?.entity("switch", "bridge_charge_enabled")), _ = ["fixed", "bridge"], v = Z(() => s.active.value && o?.connected.value ? "fixed_time" : g.value?.available ? g.value.state?.state === "off" ? "fixed" : g.value.state?.state === "on" ? "bridge" : null : null), y = Z(() => s.selected.value ? "fixed_time" : v.value), b = Z(() => !g.value?.canControl || l.value || v.value === null), x = Z(() => s.pending.value || g.value?.pending ? h.value.pending : o?.connected.value ? v.value ? g.value?.metadata.can_control ? "" : h.value.readonly : h.value.unavailable : h.value.disconnected), S = Z(() => o?.entity("number", "timed_charge_max_soc")), C = Z(() => o?.entity("number", "timed_charge_min_soc")), w = Z(() => o?.entity("number", "max_soc")), T = Z(() => o?.entity("number", "bridge_charge_min_energy_kwh")), E = Z(() => o?.entity("number", "bridge_charge_soc_buffer")), D = Z(() => [
			...y.value === "fixed" ? [{
				key: "timed_charge_min_soc",
				label: h.value.threshold
			}] : [],
			...y.value ? [{
				key: "timed_charge_max_soc",
				label: y.value === "bridge" ? h.value.bridgeTarget : h.value.fixedTarget
			}] : [],
			{
				key: "max_soc",
				label: h.value.global
			},
			...y.value === "bridge" ? [{
				key: "bridge_charge_min_energy_kwh",
				label: `${h.value.minimumEnergy} (kWh)`,
				hint: h.value.minimumHint
			}, {
				key: "bridge_charge_soc_buffer",
				label: `${h.value.socBuffer} (%)`,
				hint: h.value.bufferHint
			}] : []
		]), O = Z(() => v.value === "bridge" ? h.value.bridgeTarget.replace(" (%)", "") : h.value.target), k = Z(() => S.value?.available ? S.value.displayValue : h.value.valueUnavailable), ee = Z(() => !!o?.tariff.value?.profiles?.time_of_use.pv_sensor), { monthKeys: A, monthSummary: te } = Au(o);
		async function ne(e) {
			if (!b.value) {
				if (v.value === e) {
					s.selected.value && s.reset();
					return;
				}
				await s.leave(e, () => o.perform("switch", "bridge_charge_enabled", e === "bridge"));
			}
		}
		return (t, n) => (W(), G("div", ed, [
			q("div", td, [
				q("dl", nd, [q("div", null, [q("dt", null, F(h.value.saved), 1), q("dd", null, F(v.value ? h.value[v.value] : h.value.unavailable), 1)])]),
				v.value ? (W(), G("div", {
					key: 0,
					class: P(["electricity-targets tou-charging-soc-row", { "tou-charging-soc-row--bridge": v.value !== "fixed" }])
				}, [
					v.value === "fixed" ? (W(), G("div", rd, [q("span", null, F(B(Q)(C.value?.state?.state) === 0 ? h.value.startAtZero : h.value.start), 1), q("strong", null, F(C.value?.available ? C.value.displayValue : h.value.valueUnavailable), 1)])) : X("", !0),
					q("div", id, [q("span", null, F(O.value), 1), q("strong", null, F(k.value), 1)]),
					q("div", ad, [q("span", null, F(h.value.maxSoc), 1), q("strong", null, F(w.value?.available ? w.value.displayValue : h.value.valueUnavailable), 1)])
				], 2)) : X("", !0),
				v.value === "bridge" ? (W(), G("dl", od, [q("div", null, [q("dt", null, F(h.value.minimumEnergy), 1), q("dd", null, F(T.value?.available ? B(Q)(T.value.state?.state) === 0 ? h.value.noMinimum : T.value.displayValue : h.value.valueUnavailable), 1)]), q("div", null, [q("dt", null, F(h.value.socBuffer), 1), q("dd", null, F(E.value?.available ? E.value.displayValue : h.value.valueUnavailable), 1)])])) : X("", !0),
				q("dl", sd, [q("div", null, [q("dt", null, F(h.value.months), 1), q("dd", null, F(B(te)), 1)])])
			]),
			q("div", {
				id: p,
				class: "tou-charging-feedback"
			}, [
				B(s).error.value && y.value !== "fixed_time" ? (W(), G("p", cd, F(f.value ? "Die Änderung ist fehlgeschlagen. Bitte erneut versuchen." : "The change failed. Please try again."), 1)) : X("", !0),
				e.editing && g.value?.error ? (W(), G("p", ld, F(g.value.error), 1)) : X("", !0),
				x.value && (e.editing || !g.value?.pending) ? (W(), G("p", ud, F(x.value), 1)) : X("", !0)
			]),
			m.value ? jn((W(), G("div", dd, [
				q("h3", null, F(h.value.mode), 1),
				q("div", {
					class: "tou-charging-methods",
					role: "group",
					"aria-label": h.value.mode,
					"aria-describedby": p,
					"aria-busy": l.value
				}, [(W(), G(U, null, H(_, (e) => q("button", {
					key: e,
					type: "button",
					"data-method": e,
					"aria-pressed": y.value === e,
					disabled: b.value,
					onClick: (t) => ne(e)
				}, [q("strong", null, F(h.value[e]), 1)], 8, pd)), 64)), q("button", {
					type: "button",
					"data-method": "fixed_time",
					"aria-pressed": y.value === "fixed_time",
					disabled: b.value || !B(s).canConfigure.value,
					onClick: n[0] ||= (...e) => B(s).choose && B(s).choose(...e)
				}, [q("strong", null, F(h.value.fixed_time), 1)], 8, md)], 8, fd),
				y.value === "fixed_time" ? (W(), K(Pu, {
					key: 0,
					ref_key: "timeInput",
					ref: c,
					"model-value": B(s).start.value,
					disabled: b.value || !B(s).canConfigure.value,
					error: B(s).error.value,
					"onUpdate:modelValue": B(s).edit,
					onApply: n[1] ||= (e) => i("apply")
				}, null, 8, [
					"model-value",
					"disabled",
					"error",
					"onUpdate:modelValue"
				])) : X("", !0),
				y.value === "bridge" && !ee.value ? (W(), G("p", hd, F(h.value.pvRequired), 1)) : X("", !0),
				q("div", gd, [J(ku, {
					ref_key: "numbers",
					ref: a,
					fields: D.value,
					"soc-threshold-applies": y.value !== "fixed_time",
					disabled: B(s).pending.value,
					onApply: n[2] ||= (e) => i("apply")
				}, null, 8, [
					"fields",
					"soc-threshold-applies",
					"disabled"
				])]),
				q("h3", null, F(h.value.months), 1),
				J(Rs, {
					"entity-keys": B(A),
					"always-expanded": ""
				}, null, 8, ["entity-keys"])
			], 512)), [[ua, e.editing]]) : X("", !0)
		]));
	}
}), [["styles", [".tou-charging-settings{min-width:0}.tou-charging-settings .tou-charging-soc-row{grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.tou-charging-settings .tou-charging-soc-row--bridge{grid-template-columns:repeat(2,minmax(0,1fr))}.tou-charging-soc-row>.electricity-target{padding:8px}.tou-charging-soc-row>.electricity-target>strong{margin-top:auto;font-size:clamp(18px,4cqi,24px)}.tou-charging-limits .entity-control{box-shadow:none;background:0 0;border:0;border-radius:0;padding:12px 0}.tou-charging-summary,.tou-charging-threshold,.tou-charging-month-summary{overflow-wrap:anywhere;line-height:1.5}.tou-charging-hint{color:var(--secondary-text-color,#666);font-size:14px;line-height:1.6}.tou-charging-error{color:var(--error-color,#b00020)}.tou-charging-methods{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:16px 0;display:grid}.tou-charging-methods button{border:1px solid var(--divider-color,#ddd);background:var(--card-background-color,#fff);min-width:0;min-height:44px;color:var(--primary-text-color,#212121);text-align:left;font:inherit;cursor:pointer;border-radius:8px;padding:12px}.tou-charging-methods button[aria-pressed=true]{border:2px solid var(--primary-color,#03a9f4);background:var(--secondary-background-color,#f5f5f5);padding:11px}.tou-charging-methods strong{line-height:1.5;display:block}.tou-charging-methods button:disabled{opacity:.55;cursor:not-allowed}.tou-charging-methods button:focus-visible{outline:3px solid var(--primary-color,#03a9f4);outline-offset:3px}@media (max-width:700px){.tou-charging-methods{grid-template-columns:minmax(0,1fr)}}"]]]), vd = { class: "electricity-tariff-view" }, yd = { class: "electricity-card electricity-tariff-bar" }, bd = { class: "electricity-tariff-bar__row" }, xd = { class: "electricity-active" }, Sd = ["disabled", "aria-expanded"], Cd = ["aria-busy"], wd = ["disabled"], Td = { class: "electricity-sr-only" }, Ed = ["value"], Dd = {
	key: 0,
	role: "status"
}, Od = ["disabled"], kd = ["disabled"], Ad = {
	key: 1,
	class: "electricity-operation-status",
	role: "status",
	"aria-live": "polite"
}, jd = {
	key: 2,
	role: "alert",
	class: "electricity-error"
}, Md = ["disabled"], Nd = {
	key: 4,
	role: "status"
}, Pd = {
	key: 5,
	role: "status"
}, Fd = {
	key: 6,
	role: "status"
}, Id = {
	key: 0,
	class: "electricity-columns"
}, Ld = ["aria-label"], Rd = { class: "electricity-current" }, zd = { class: "electricity-muted" }, Bd = { class: "electricity-current-price" }, Vd = { key: 0 }, Hd = ["aria-busy"], Ud = ["disabled", "aria-expanded"], Wd = ["disabled"], Gd = { class: "electricity-current" }, Kd = { class: "electricity-muted" }, qd = { class: "electricity-current-price" }, Jd = { key: 0 }, Yd = { class: "electricity-price-summary electricity-summary-rows" }, Xd = ["aria-busy"], Zd = ["id"], Qd = ["disabled"], $d = { class: "electricity-muted" }, ef = { class: "electricity-fields" }, tf = ["aria-invalid", "aria-describedby"], nf = { class: "electricity-muted" }, rf = { class: "electricity-muted" }, af = { class: "electricity-fields" }, of = { class: "electricity-muted" }, sf = {
	key: 0,
	class: "electricity-muted electricity-additional-settings"
}, cf = { class: "electricity-price-advanced" }, lf = { class: "electricity-fields" }, uf = ["aria-invalid", "aria-describedby"], df = ["aria-invalid", "aria-describedby"], ff = ["value"], pf = { class: "electricity-muted" }, mf = { class: "electricity-muted" }, hf = { class: "electricity-fields" }, gf = ["aria-invalid", "aria-describedby"], _f = { class: "electricity-muted" }, vf = ["disabled"], yf = ["disabled"], bf = { class: "electricity-price-details" }, xf = ["aria-label"], Sf = ["aria-pressed", "onClick"], Cf = { class: "electricity-day" }, wf = { key: 0 }, Tf = {
	key: 0,
	class: "electricity-card electricity-charging"
}, Ef = [
	"disabled",
	"aria-busy",
	"aria-expanded"
], Df = ["disabled"], Of = {
	key: 0,
	class: "electricity-activation"
}, kf = ["aria-busy"], Af = [
	"checked",
	"aria-describedby",
	"disabled"
], jf = {
	id: "electricity-master-status",
	class: "electricity-master-status",
	role: "status",
	"aria-live": "polite"
}, Mf = {
	key: 0,
	id: "electricity-activation-error",
	class: "electricity-error",
	role: "alert"
}, Nf = ["disabled"], Pf = {
	key: 2,
	class: "electricity-muted"
}, Ff = {
	key: 3,
	class: "electricity-muted"
}, If = {
	key: 4,
	class: "electricity-muted"
}, Lf = { key: 5 }, Rf = {
	key: 3,
	class: "electricity-charging-feedback"
}, zf = {
	key: 0,
	class: "electricity-error",
	role: "alert"
}, Bf = {
	key: 1,
	role: "status",
	"aria-live": "polite"
}, Vf = {
	key: 4,
	class: "electricity-charging-editor"
}, Hf = ["disabled"], Uf = ["disabled"], Wf = {
	key: 0,
	role: "status",
	"aria-live": "polite"
}, Gf = {
	key: 5,
	class: "electricity-charge-status"
}, Kf = ["aria-label"], qf = { key: 0 }, Jf = {
	key: 1,
	class: "electricity-summary-rows electricity-pv-summary"
}, Yf = {
	key: 0,
	class: "electricity-planned-pv"
}, Xf = {
	key: 1,
	class: "electricity-footnote"
}, Zf = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "ElectricityTariffView",
	props: { hass: { type: Object } },
	setup(e) {
		let t = e, n = Pn(Co), r = Z(() => n?.language.value === "de"), i = Z(() => r.value ? {
			active: "Aktiver Tarif",
			tou: "Zeitvariabel",
			dynamic: "Dynamisch",
			unset: "Noch nicht eingerichtet",
			change: "Tarif wechseln",
			apply: "Tarif übernehmen",
			cancel: "Abbrechen",
			save: "Übernehmen",
			done: "Übernehmen",
			edit: "Bearbeiten",
			loading: "Wird geladen …",
			saving: "Wird gespeichert …",
			applying: "Tarif wird übernommen …",
			entityPending: "Änderung wird an Home Assistant gesendet …",
			automatic: "Automatische Netzladung",
			turningOn: "Einschalten wird übernommen …",
			turningOff: "Ausschalten wird übernommen …",
			chooseHint: "Nur der gewählte Tarif ist aktiv. Gespeicherte Einstellungen bleiben beim Wechsel erhalten.",
			incomplete: "Dieser Tarif ist noch nicht eingerichtet. Nach dem Wechsel bleibt die automatische Netzladung aus. Richte danach „Preise & Zeiten“ ein.",
			touHint: "Feste Preise zu wiederkehrenden Uhrzeiten",
			dynamicHint: "Preise aus einem Strompreis-Sensor",
			price: "Strompreis",
			current: "Aktuell",
			today: "Heute",
			tomorrow: "Morgen",
			prices: "Preise & Zeiten",
			feed: "Einspeisevergütung",
			source: "Strompreis-Sensor (erforderlich)",
			sourceSummary: "Preisquelle",
			attribute: "Preisattribut (optional)",
			unit: "Einheit der Preisquelle",
			pv: "PV-Prognose-Sensor (optional)",
			pvFactor: "Anrechenbarer PV-Anteil (%)",
			advanced: "Weitere Einstellungen",
			sourceSettings: "Preisquelle genauer einstellen",
			attributeHint: "Meist werden die Preislisten automatisch erkannt. Trage nur dann ein Attribut ein, wenn deine Preisquelle es erfordert.",
			unitHint: "Nur ändern, wenn die Einheit des Sensors fehlt oder nicht korrekt erkannt wird. Eine falsche Einheit verändert alle angezeigten und für die Ladung verwendeten Preise.",
			pvHint: "Wähle den erwarteten PV-Gesamtertrag für morgen als Energie in kWh oder Wh, keine aktuelle Leistung und keinen heutigen Restertrag. Bedarfsgerechtes Laden kann diese Energie berücksichtigen und dadurch weniger Netzstrom einkaufen. Ohne Quelle wird kein PV-Ertrag abgezogen.",
			pvFactorHint: "100 % rechnet die gesamte Prognose an. Ein kleinerer Anteil plant vorsichtiger mit PV und kann mehr Netzladung erlauben. 0 % berücksichtigt keinen PV-Ertrag.",
			customSettings: "Gespeicherte Zusatzwerte",
			feedHint: "Vergütung für eingespeisten Strom laut deinem Vertrag. Wenn du keine Vergütung erhältst, trage 0 ein. Sie wird für die Ersparnisberechnung verwendet, nicht als Ladepreisgrenze.",
			missingPriceSensor: "Bitte einen Strompreis-Sensor auswählen.",
			missingFeed: "Bitte die Einspeisevergütung in ct/kWh eintragen. Wenn du keine Vergütung erhältst, trage 0 ein.",
			invalidFeed: "Bitte die Einspeisevergütung als Zahl von 0 bis 200 ct/kWh mit höchstens zwei Nachkommastellen eingeben.",
			priceSensorMissing: "Der gewählte Strompreis-Sensor wurde nicht gefunden. Bitte einen vorhandenen Sensor auswählen.",
			unsupportedPriceUnit: "Die Einheit der Preisquelle wird nicht unterstützt. Prüfe die Einheit am Sensor und wähle hier nur die dazu passende Einheit. Preise in anderen Währungen müssen zuerst in Euro umgerechnet werden.",
			pvSensorMissing: "Der gewählte PV-Prognose-Sensor wurde nicht gefunden. Bitte einen vorhandenen Sensor auswählen oder die optionale Auswahl löschen.",
			invalidAttribute: "Bitte einen Attributnamen mit höchstens 128 Zeichen eingeben oder das Feld für die automatische Erkennung leer lassen.",
			invalidPvFactor: "Bitte einen ganzen PV-Anteil von 0 bis 100 % eingeben.",
			charging: "Netzladung",
			pvSummary: "PV-Ertragsprognose",
			pvWaiting: "Warte auf Ertragswert …",
			pvReadError: "Ertragswert derzeit nicht abrufbar",
			noPv: "Nicht eingerichtet",
			gross: "Alle Preise brutto in ct/kWh.",
			activationOff: "Keine automatische Ladung aus dem Netz.",
			activationOn: "Lädt, sobald die Ladebedingungen erfüllt sind.",
			editFirst: "Beende die Bearbeitung, um die Automatik zu schalten.",
			chart: "Preisverlauf",
			plannedPv: "Im Ladeplan angerechnete PV-Energie",
			details: "Ladeplan & Prognose",
			priceHint: "Alle Preise brutto in ct/kWh. Die Quelleneinheit wird nur zur Umrechnung verwendet.",
			readonly: "Keine Berechtigung zum Ändern des Tarifs.",
			disconnected: "Keine Verbindung zu Home Assistant. Dein Entwurf bleibt erhalten.",
			bridgePvRequired: "Die PV-Start-Quelle wird für die aktive verbrauchsbasierte Ladung benötigt. Wähle eine Quelle oder schalte diese Ladeplanung zuerst aus.",
			failed: "Die Änderung ist fehlgeschlagen. Bitte erneut versuchen.",
			conflict: "Der Tarif wurde inzwischen geändert. Dein Entwurf bleibt erhalten. Lade die gespeicherten Einstellungen erneut.",
			reload: "Gespeicherte Einstellungen laden (Entwurf verwerfen)",
			invalid: "Die Tarifeinstellungen sind ungültig. Bitte die Angaben im geöffneten Formular prüfen.",
			saved: "Einstellungen gespeichert.",
			tariffChanged: "Der aktive Tarif wurde an anderer Stelle gewechselt. Der bisherige Preisentwurf wurde geschlossen.",
			unavailable: "Nicht verfügbar",
			sourceHint: "Die Preisquelle muss die Preise inklusive der gewünschten Steuern und Zuschläge liefern.",
			units: {
				auto: "Automatisch erkennen",
				eur_kwh: "EUR/kWh",
				ct_kwh: "ct/kWh",
				eur_mwh: "EUR/MWh",
				ct_mwh: "ct/MWh"
			}
		} : {
			active: "Active tariff",
			tou: "Time of use",
			dynamic: "Dynamic",
			unset: "Not configured",
			change: "Change tariff",
			apply: "Apply tariff",
			cancel: "Cancel",
			save: "Apply",
			done: "Apply",
			edit: "Edit",
			loading: "Loading …",
			saving: "Saving …",
			applying: "Applying tariff …",
			entityPending: "Sending change to Home Assistant …",
			automatic: "Automatic grid charging",
			turningOn: "Turning on …",
			turningOff: "Turning off …",
			chooseHint: "Only the selected tariff is active. Saved settings are preserved when switching.",
			incomplete: "This tariff is not configured yet. Automatic grid charging will be off after switching. Then set up “Prices & times”.",
			touHint: "Fixed prices at recurring times",
			dynamicHint: "Prices from an electricity price sensor",
			price: "Electricity price",
			current: "Current",
			today: "Today",
			tomorrow: "Tomorrow",
			prices: "Prices & times",
			feed: "Feed-in remuneration",
			source: "Electricity price sensor (required)",
			sourceSummary: "Price source",
			attribute: "Price attribute (optional)",
			unit: "Price source unit",
			pv: "PV forecast sensor (optional)",
			pvFactor: "PV share to account for (%)",
			advanced: "More settings",
			sourceSettings: "Adjust price source details",
			attributeHint: "Price lists are usually detected automatically. Only enter an attribute if your price source requires it.",
			unitHint: "Only change this if the sensor unit is missing or detected incorrectly. A wrong unit changes every price displayed and used for charging.",
			pvHint: "Choose the total solar energy forecast for tomorrow in kWh or Wh, not current power or today's remaining production. Charging what is needed can account for this energy and buy less grid energy. Without a source, no solar production is deducted.",
			pvFactorHint: "100% accounts for the entire forecast. A smaller share plans more cautiously for solar production and may allow more grid charging. 0% ignores solar production.",
			customSettings: "Saved additional values",
			feedHint: "The remuneration for exported electricity in your contract. Enter 0 if you receive no remuneration. It is used to calculate savings, not as a charging price cap.",
			missingPriceSensor: "Please select an electricity price sensor.",
			missingFeed: "Please enter the feed-in remuneration in ct/kWh. Enter 0 if you receive no remuneration.",
			invalidFeed: "Enter a feed-in remuneration from 0 to 200 ct/kWh with at most two decimal places.",
			priceSensorMissing: "The selected electricity price sensor was not found. Please select an existing sensor.",
			unsupportedPriceUnit: "The price source unit is not supported. Check the sensor unit and select only the matching unit here. Prices in other currencies must be converted to euros first.",
			pvSensorMissing: "The selected PV forecast sensor was not found. Select an existing sensor or clear this optional selection.",
			invalidAttribute: "Enter an attribute name with at most 128 characters or leave the field blank for automatic detection.",
			invalidPvFactor: "Enter a whole PV percentage from 0 to 100%.",
			charging: "Grid charging",
			pvSummary: "Solar yield forecast",
			pvWaiting: "Waiting for yield data …",
			pvReadError: "Yield data currently unavailable",
			noPv: "Not configured",
			gross: "All prices include tax and use ct/kWh.",
			activationOff: "No automatic charging from the grid.",
			activationOn: "Charges when the configured conditions are met.",
			editFirst: "Finish editing before switching automatic charging.",
			chart: "Price chart",
			plannedPv: "Solar energy accounted for in the charging plan",
			details: "Charging plan & forecast",
			priceHint: "All prices include tax and use ct/kWh. The source unit is used for conversion only.",
			readonly: "You do not have permission to change the tariff.",
			disconnected: "Disconnected from Home Assistant. Your draft is preserved.",
			bridgePvRequired: "The active consumption-based charging plan requires a PV start source. Choose a source or turn off this charging plan first.",
			failed: "The change failed. Please try again.",
			conflict: "The tariff has changed elsewhere. Your draft is preserved. Reload the saved settings.",
			reload: "Load saved settings (discard draft)",
			invalid: "The tariff settings are invalid. Please check the values in the open form.",
			saved: "Settings saved.",
			tariffChanged: "The active tariff was changed elsewhere. The previous price draft was closed.",
			unavailable: "Unavailable",
			sourceHint: "The price source must include the taxes and fees you want to account for.",
			units: {
				auto: "Detect automatically",
				eur_kwh: "EUR/kWh",
				ct_kwh: "ct/kWh",
				eur_mwh: "EUR/MWh",
				ct_mwh: "ct/MWh"
			}
		}), a = /* @__PURE__ */ z(null);
		V(() => n?.tariff.value, (e) => {
			e && (a.value = e);
		}, { immediate: !0 });
		let o = Z(() => n?.tariff.value ?? a.value), s = Z(() => o.value?.tariff_type), c = Z(() => o.value?.fixed_time_charging?.enabled === !0), l = Z(() => s.value === "time_of_use" || s.value === "dynamic"), u = Z(() => n?.connected.value === !0 && n.ready.value), d = Z(() => o.value?.can_configure === !0 && u.value), f = Z(() => s.value === "dynamic" ? i.value.dynamic : s.value === "time_of_use" ? i.value.tou : i.value.unset), p = Z(() => n?.entity("switch", s.value === "dynamic" ? "price_charge_enabled" : "timed_charge_enabled")), m = Z(() => typeof o.value?.automation_enabled == "boolean" ? o.value.automation_enabled : p.value?.available ? p.value.state?.state === "on" : null), h = /* @__PURE__ */ z(null), g = /* @__PURE__ */ z(!1), _ = /* @__PURE__ */ z("today"), v = /* @__PURE__ */ z(null), y = /* @__PURE__ */ z(null), b = /* @__PURE__ */ z(null), x = Kn(), S = /* @__PURE__ */ z(!1), C = /* @__PURE__ */ z(!1), w = /* @__PURE__ */ z(null), T = /* @__PURE__ */ z(null), E = /* @__PURE__ */ z(!1), D = /* @__PURE__ */ z(!1), O = /* @__PURE__ */ z(!1), k = /* @__PURE__ */ z("time_of_use"), ee = /* @__PURE__ */ z(""), A = /* @__PURE__ */ z(!1), te = /* @__PURE__ */ z(!1), ne = /* @__PURE__ */ z(!1), j = /* @__PURE__ */ z({
			feed_in_price_ct_kwh: null,
			price_sensor: null,
			price_attribute: null,
			price_unit: "auto",
			pv_sensor: null,
			pv_factor: 100
		}), re = /* @__PURE__ */ z(""), M = /* @__PURE__ */ z(""), N = /* @__PURE__ */ z(""), ie = /* @__PURE__ */ z(), ae = /* @__PURE__ */ z(), oe = /* @__PURE__ */ z(), se = /* @__PURE__ */ z(), ce = /* @__PURE__ */ z(!1), le = !1, ue = 0, de = 0;
		cr(() => {
			le = !0, ue++, window.clearInterval(we);
		});
		let P = Z(() => A.value || te.value || ne.value), fe = Z(() => _o(u.value ? h.value?.current_price_ct_kwh : null, t.hass, 2)), pe = Z(() => h.value ? vo(`${h.value.date}T12:00:00Z`, t.hass, {
			dateStyle: "medium",
			timeZone: "UTC"
		}) : null), me = Z(() => {
			let e = s.value === "dynamic" ? o.value?.profiles?.dynamic.price_sensor : n?.entity("sensor", "economics_current_import_price")?.metadata.entity_id;
			return e ? t.hass?.states[e] : void 0;
		}), he = Z(() => {
			let e = n?.entity("sensor", "price_charge_status_text"), r = e?.state?.attributes, i = o.value?.profiles?.dynamic.pv_sensor;
			if (!e?.available || !i || r?.pv_prognose_sensor !== i) return null;
			let a = Q(r.pv_prognose_kwh);
			return a !== null && a >= 0 ? _o(a, t.hass, 1) : null;
		}), ge = Array.from({ length: 12 }, (e, t) => `timed_charge_month_${t + 1}`), _e = Z(() => {
			let e = !c.value && n?.entity("switch", "bridge_charge_enabled")?.state?.state === "on";
			return (s.value === "dynamic" ? [
				["number", "max_soc"],
				["number", "price_charge_max_price"],
				["number", "price_charge_hours"],
				["number", "price_charge_neutral_price"]
			] : [
				["number", "max_soc"],
				["number", "timed_charge_max_soc"],
				["number", "timed_charge_min_soc"],
				...e ? [["number", "bridge_charge_min_energy_kwh"], ["number", "bridge_charge_soc_buffer"]] : [],
				["switch", "bridge_charge_enabled"],
				...ge.map((e) => ["switch", e])
			]).map(([e, t]) => n?.entity(e, t)).filter((e) => e && (e.pending || e.error));
		}), ve = Z(() => {
			let e = o.value?.profiles?.dynamic;
			return e ? [
				e.price_attribute ? `${i.value.attribute}: ${e.price_attribute}` : "",
				e.price_unit === "auto" ? "" : `${i.value.unit}: ${i.value.units[e.price_unit]}`,
				e.pv_factor === 100 ? "" : `${i.value.pvFactor}: ${e.pv_factor}`
			].filter(Boolean).join(" · ") : "";
		}), ye = Z(() => {
			let e = o.value?.profiles?.dynamic.price_sensor;
			return e ? t.hass?.states[e]?.attributes.friendly_name ?? e : i.value.unset;
		}), be = Z(() => _o(o.value?.profiles?.dynamic.feed_in_price_ct_kwh, t.hass, 2)), xe = Z(() => {
			let e = s.value === "dynamic" ? o.value?.profiles?.dynamic.pv_sensor : o.value?.profiles?.time_of_use.pv_sensor;
			if (!e) return i.value.noPv;
			if (!n?.connected.value) return i.value.pvReadError;
			let t = n?.entity("sensor", "charging_pv_forecast");
			return t?.state?.attributes.source_entity_id === e ? t.available ? t.displayValue : t.state?.attributes.reading_status === "error" ? i.value.pvReadError : i.value.pvWaiting : i.value.pvWaiting;
		});
		function I(e, t) {
			v.value = t, A.value && (b.value = e, vn(() => {
				if (le) return;
				let t = ie.value?.querySelector(`[name="dynamic_${e}"]`), n = t?.closest("details");
				n && (n.open = !0), t?.focus();
			}));
		}
		function Se(e, t = null) {
			if (le) return;
			y.value = t;
			let n = e && typeof e == "object" && "code" in e ? String(e.code) : "failed";
			S.value = n === "conflict", b.value = null;
			let r = {
				price_sensor_not_configured: ["price_sensor", i.value.missingPriceSensor],
				price_sensor_missing: ["price_sensor", i.value.priceSensorMissing],
				price_unit_unsupported: ["price_unit", i.value.unsupportedPriceUnit],
				pv_sensor_missing: ["pv_sensor", i.value.pvSensorMissing],
				invalid_price_attribute: ["price_attribute", i.value.invalidAttribute],
				invalid_feed_in_price: ["feed", re.value.trim() ? i.value.invalidFeed : i.value.missingFeed],
				invalid_pv_factor: ["pv_factor", i.value.invalidPvFactor]
			}[n];
			if (r) {
				I(...r);
				return;
			}
			v.value = n === "bridge_pv_start_required" ? i.value.bridgePvRequired : n === "conflict" ? i.value.conflict : n === "forbidden" ? i.value.readonly : n === "disconnected" ? i.value.disconnected : n === "invalid_tariff" || n === "invalid_format" ? i.value.invalid : i.value.failed;
		}
		async function Ce() {
			let e = ++ue;
			if (!n || !u.value || !l.value) {
				h.value = null, g.value = !1;
				return;
			}
			let t = s.value, r = o.value?.revision, i = _.value, a = Date.now(), c = (e) => e.tariff_type === t && e.revision === r && e.day === i;
			h.value && (!c(h.value) || a >= de) && (h.value = null), g.value = !0;
			try {
				let l = await n.loadTariffSeries(i);
				if (!le && e === ue && s.value === t && o.value?.revision === r && _.value === i) {
					let e = i === "today" ? l.end : l.start;
					de = a + (Date.parse(e) - Date.parse(l.now)), h.value = c(l) && Date.now() < de ? l : null;
				}
			} catch {
				!le && e === ue && (h.value = null);
			} finally {
				!le && e === ue && (g.value = !1);
			}
		}
		V([
			() => t.hass?.connection,
			me,
			u,
			s,
			() => o.value?.revision,
			_
		], ([e, t], [n, r]) => {
			let i = s.value === "dynamic" && (!t?.state || t.state === "unknown" || t.state === "unavailable");
			(e !== n || !t && r || i) && (h.value = null), Ce();
		}, { immediate: !0 }), V(s, (e, t) => {
			t && e !== t && P.value && (A.value = !1, te.value = !1, ne.value = !1, v.value = null, b.value = null, S.value = !1, D.value = !0), _.value = "today", h.value = null;
		}), V(u, (e) => {
			e && n?.loadTariff().catch(Se);
		}, { immediate: !0 });
		let we = window.setInterval(() => {
			u.value && (Ce(), C.value || n?.loadTariff().catch(() => {}));
		}, 6e4), L = Z(() => {
			let e = o.value?.profiles?.[k.value];
			return !e || e.feed_in_price_ct_kwh === null ? !0 : "price_sensor" in e ? !e.price_sensor : e.base_price_ct_kwh === null;
		});
		function Te() {
			D.value = !1, k.value = s.value === "dynamic" ? "dynamic" : "time_of_use", ee.value = o.value?.revision ?? "", O.value = !0, v.value = null, E.value = !1;
		}
		async function Ee() {
			if (n && d.value && !C.value) {
				C.value = !0, T.value = "applying", v.value = null;
				try {
					await n.configureTariff({
						revision: ee.value,
						tariff_type: k.value,
						...L.value ? { automation_enabled: !1 } : {}
					}), le || (O.value = !1, E.value = !0);
				} catch (e) {
					Se(e);
				} finally {
					T.value = null, C.value = !1;
				}
			}
		}
		async function De(e) {
			let t = e.target, r = t.checked;
			if (t.checked = m.value === !0, n && d.value && l.value && !C.value) {
				C.value = !0, w.value = r, v.value = null, E.value = !1;
				try {
					await n.configureTariff({
						revision: o.value.revision,
						tariff_type: s.value,
						automation_enabled: r
					});
				} catch (e) {
					Se(e, "activation");
				} finally {
					w.value = null, C.value = !1;
				}
			}
		}
		async function Oe() {
			if (D.value = !1, n && !C.value) {
				C.value = !0, T.value = "loading", v.value = null, b.value = null, E.value = !1;
				try {
					let e = await n.loadTariff();
					if (le) return;
					if (!e.can_configure || e.tariff_type !== "dynamic" || !e.profiles) throw { code: "forbidden" };
					j.value = { ...e.profiles.dynamic }, re.value = j.value.feed_in_price_ct_kwh === null ? "" : String(j.value.feed_in_price_ct_kwh).replace(".", r.value ? "," : "."), M.value = String(j.value.pv_factor), N.value = e.revision, A.value = !0, S.value = !1;
				} catch (e) {
					Se(e);
				} finally {
					T.value = null, C.value = !1, await vn(), ie.value?.querySelector("select,input")?.focus();
				}
			}
		}
		function ke() {
			A.value = !1, v.value = null, b.value = null, S.value = !1, vn(() => ae.value?.focus());
		}
		async function Ae() {
			if (!n || C.value || S.value) return;
			if (b.value = null, !j.value.price_sensor) {
				I("price_sensor", i.value.missingPriceSensor);
				return;
			}
			if (!re.value.trim()) {
				I("feed", i.value.missingFeed);
				return;
			}
			let e = /^\d+(?:[.,]\d{1,2})?$/.test(re.value.trim()) ? Number(re.value.trim().replace(",", ".")) : NaN;
			if (!Number.isFinite(e) || e < 0 || e > 200) {
				I("feed", i.value.invalidFeed);
				return;
			}
			let t = Number(M.value);
			if (String(M.value).trim() === "" || !Number.isInteger(t) || t < 0 || t > 100) {
				I("pv_factor", i.value.invalidPvFactor);
				return;
			}
			C.value = !0, T.value = "saving", v.value = null;
			try {
				await n.configureTariff({
					revision: N.value,
					tariff_type: "dynamic",
					profile: {
						...j.value,
						price_attribute: j.value.price_attribute?.trim() || null,
						feed_in_price_ct_kwh: e,
						pv_factor: t
					}
				}), le || (ke(), E.value = !0);
			} catch (e) {
				Se(e);
			} finally {
				T.value = null, C.value = !1;
			}
		}
		async function je() {
			if (n && !C.value) {
				C.value = !0, T.value = "loading";
				try {
					await n.loadTariff(), le || (A.value = !1, O.value = !1, v.value = null, b.value = null, S.value = !1);
				} catch (e) {
					Se(e);
				} finally {
					T.value = null, C.value = !1;
				}
			}
		}
		function Me() {
			ne.value = !1, vn(() => oe.value?.focus());
		}
		function Ne() {
			ce.value || se.value?.pending || se.value?.reset() !== !1 && Me();
		}
		async function Pe() {
			if (ce.value || se.value?.pending) return;
			let e = se.value;
			if (e) {
				ce.value = !0;
				try {
					await e.submit() && Me();
				} finally {
					ce.value = !1;
				}
			}
		}
		return (t, n) => (W(), G("div", vd, [
			q("section", yd, [
				q("div", bd, [q("div", xd, [
					q("span", null, F(i.value.active), 1),
					q("strong", null, F(f.value), 1),
					q("button", {
						type: "button",
						disabled: !d.value || C.value || P.value,
						"aria-expanded": O.value,
						onClick: Te
					}, F(i.value.change), 9, Sd)
				])]),
				O.value ? (W(), G("form", {
					key: 0,
					class: "electricity-choice",
					"aria-busy": T.value === "applying",
					onSubmit: io(Ee, ["prevent"])
				}, [
					q("fieldset", { disabled: C.value || !u.value }, [q("legend", Td, F(i.value.active), 1), (W(), G(U, null, H(["time_of_use", "dynamic"], (e) => q("label", { key: e }, [jn(q("input", {
						"onUpdate:modelValue": n[0] ||= (e) => k.value = e,
						type: "radio",
						name: "electricity-tariff",
						value: e
					}, null, 8, Ed), [[Za, k.value]]), q("span", null, [q("strong", null, F(e === "time_of_use" ? i.value.tou : i.value.dynamic), 1), q("small", null, F(e === "time_of_use" ? i.value.touHint : i.value.dynamicHint), 1)])])), 64))], 8, wd),
					q("p", null, F(i.value.chooseHint), 1),
					L.value ? (W(), G("p", Dd, F(i.value.incomplete), 1)) : X("", !0),
					J(No, { class: "electricity-actions" }, {
						default: An(() => [q("button", {
							type: "submit",
							disabled: C.value || !u.value || S.value
						}, F(T.value === "applying" ? i.value.applying : i.value.apply), 9, Od), q("button", {
							type: "button",
							disabled: C.value,
							onClick: n[1] ||= (e) => {
								O.value = !1, v.value = null;
							}
						}, F(i.value.cancel), 9, kd)]),
						_: 1
					})
				], 40, Cd)) : X("", !0),
				T.value ? (W(), G("p", Ad, F(i.value[T.value]), 1)) : X("", !0),
				v.value && !b.value && y.value !== "activation" ? (W(), G("p", jd, F(v.value), 1)) : X("", !0),
				S.value && y.value !== "activation" ? (W(), G("button", {
					key: 3,
					type: "button",
					disabled: C.value || !u.value,
					onClick: je
				}, F(i.value.reload), 9, Md)) : X("", !0),
				E.value ? (W(), G("p", Nd, F(i.value.saved), 1)) : X("", !0),
				D.value ? (W(), G("p", Pd, F(i.value.tariffChanged), 1)) : X("", !0),
				!o.value && !v.value ? (W(), G("p", Fd, F(i.value.loading), 1)) : X("", !0)
			]),
			l.value ? (W(), G("div", Id, [q("section", {
				class: "electricity-card electricity-price-card",
				"aria-label": i.value.prices
			}, [s.value === "time_of_use" ? (W(), K(eu, {
				key: 0,
				hass: e.hass,
				compact: "",
				onEditing: n[2] ||= (e) => te.value = e,
				onSaved: Ce
			}, {
				"current-price": An(() => [q("div", Rd, [q("span", zd, F(i.value.price) + " · " + F(i.value.current), 1), q("p", Bd, [Y(F(fe.value ?? i.value.unavailable), 1), fe.value === null ? X("", !0) : (W(), G("span", Vd, " ct/kWh"))])])]),
				_: 1
			}, 8, ["hass"])) : s.value === "dynamic" ? (W(), G("section", {
				key: 1,
				class: "electricity-card electricity-prices",
				"aria-busy": T.value === "loading" || T.value === "saving"
			}, [
				q("header", null, [q("div", null, [q("h2", null, F(i.value.prices), 1)]), J(No, null, {
					default: An(() => [q("button", {
						ref_key: "priceButton",
						ref: ae,
						type: "button",
						disabled: C.value || !d.value || O.value || A.value && (!u.value || S.value),
						"aria-expanded": A.value,
						onClick: n[3] ||= (e) => A.value ? Ae() : Oe()
					}, F(T.value === "loading" ? i.value.loading : T.value === "saving" ? i.value.saving : A.value ? i.value.save : i.value.edit), 9, Ud), A.value ? (W(), G("button", {
						key: 0,
						type: "button",
						disabled: C.value,
						onClick: ke
					}, F(i.value.cancel), 9, Wd)) : X("", !0)]),
					_: 1
				})]),
				q("div", Gd, [q("span", Kd, F(i.value.price) + " · " + F(i.value.current), 1), q("p", qd, [Y(F(fe.value ?? i.value.unavailable), 1), fe.value === null ? X("", !0) : (W(), G("span", Jd, " ct/kWh"))])]),
				q("dl", Yd, [q("div", null, [q("dt", null, F(i.value.sourceSummary), 1), q("dd", null, F(ye.value), 1)]), q("div", null, [q("dt", null, F(i.value.feed), 1), q("dd", null, [Y(F(be.value ?? i.value.unavailable), 1), be.value === null ? X("", !0) : (W(), G(U, { key: 0 }, [Y(" ct/kWh")], 64))])])]),
				A.value ? (W(), G("form", {
					key: 0,
					ref_key: "pricesEditor",
					ref: ie,
					class: "electricity-price-editor",
					"aria-busy": T.value === "saving",
					novalidate: "",
					onSubmit: io(Ae, ["prevent"])
				}, [
					v.value && b.value ? (W(), G("p", {
						key: 0,
						id: B(x),
						role: "alert",
						class: "electricity-error"
					}, F(v.value), 9, Zd)) : X("", !0),
					q("fieldset", { disabled: C.value || !u.value }, [
						q("p", $d, F(i.value.priceHint), 1),
						q("div", ef, [J(mc, {
							modelValue: j.value.price_sensor,
							"onUpdate:modelValue": n[4] ||= (e) => j.value.price_sensor = e,
							hass: e.hass,
							label: i.value.source,
							name: "dynamic_price_sensor",
							invalid: b.value === "price_sensor",
							"described-by": b.value === "price_sensor" ? B(x) : void 0
						}, null, 8, [
							"modelValue",
							"hass",
							"label",
							"invalid",
							"described-by"
						]), q("label", null, [Y(F(i.value.feed) + " (ct/kWh)", 1), jn(q("input", {
							"onUpdate:modelValue": n[5] ||= (e) => re.value = e,
							type: "text",
							inputmode: "decimal",
							name: "dynamic_feed",
							autocomplete: "off",
							required: "",
							"aria-invalid": b.value === "feed" || void 0,
							"aria-describedby": b.value === "feed" ? B(x) : void 0
						}, null, 8, tf), [[Xa, re.value]])])]),
						q("p", nf, F(i.value.sourceHint), 1),
						q("p", rf, F(i.value.feedHint), 1),
						q("div", af, [J(mc, {
							modelValue: j.value.pv_sensor,
							"onUpdate:modelValue": n[6] ||= (e) => j.value.pv_sensor = e,
							hass: e.hass,
							label: i.value.pv,
							name: "dynamic_pv_sensor",
							invalid: b.value === "pv_sensor",
							"described-by": b.value === "pv_sensor" ? B(x) : void 0
						}, null, 8, [
							"modelValue",
							"hass",
							"label",
							"invalid",
							"described-by"
						])]),
						q("p", of, F(i.value.pvHint), 1),
						ve.value ? (W(), G("p", sf, F(i.value.customSettings) + ": " + F(ve.value), 1)) : X("", !0),
						q("details", cf, [
							q("summary", null, F(i.value.advanced), 1),
							q("h3", null, F(i.value.sourceSettings), 1),
							q("div", lf, [q("label", null, [Y(F(i.value.attribute), 1), jn(q("input", {
								"onUpdate:modelValue": n[7] ||= (e) => j.value.price_attribute = e,
								name: "dynamic_price_attribute",
								type: "text",
								autocomplete: "off",
								"aria-invalid": b.value === "price_attribute" || void 0,
								"aria-describedby": b.value === "price_attribute" ? B(x) : void 0
							}, null, 8, uf), [[Xa, j.value.price_attribute]])]), q("label", null, [Y(F(i.value.unit), 1), jn(q("select", {
								"onUpdate:modelValue": n[8] ||= (e) => j.value.price_unit = e,
								name: "dynamic_price_unit",
								"aria-invalid": b.value === "price_unit" || void 0,
								"aria-describedby": b.value === "price_unit" ? B(x) : void 0
							}, [(W(!0), G(U, null, H(i.value.units, (e, t) => (W(), G("option", {
								key: t,
								value: t
							}, F(e), 9, ff))), 128))], 8, df), [[Qa, j.value.price_unit]])])]),
							q("p", pf, F(i.value.attributeHint), 1),
							q("p", mf, F(i.value.unitHint), 1),
							q("div", hf, [q("label", null, [Y(F(i.value.pvFactor), 1), jn(q("input", {
								"onUpdate:modelValue": n[9] ||= (e) => M.value = e,
								name: "dynamic_pv_factor",
								type: "number",
								min: "0",
								max: "100",
								step: "1",
								"aria-invalid": b.value === "pv_factor" || void 0,
								"aria-describedby": b.value === "pv_factor" ? B(x) : void 0
							}, null, 8, gf), [[Xa, M.value]])])]),
							q("p", _f, F(i.value.pvFactorHint), 1)
						])
					], 8, Qd),
					J(No, { class: "electricity-actions" }, {
						default: An(() => [q("button", {
							type: "submit",
							disabled: C.value || !u.value || S.value
						}, F(T.value === "saving" ? i.value.saving : i.value.save), 9, vf), q("button", {
							type: "button",
							disabled: C.value,
							onClick: ke
						}, F(i.value.cancel), 9, yf)]),
						_: 1
					})
				], 40, Xd)) : X("", !0)
			], 8, Hd)) : X("", !0), q("details", bf, [
				q("summary", null, F(i.value.chart), 1),
				s.value === "dynamic" ? (W(), G("div", {
					key: 0,
					class: "electricity-days",
					"aria-label": i.value.price
				}, [(W(), G(U, null, H(["today", "tomorrow"], (e) => q("button", {
					key: e,
					type: "button",
					"aria-pressed": _.value === e,
					onClick: (t) => _.value = e
				}, F(e === "today" ? i.value.today : i.value.tomorrow), 9, Sf)), 64))], 8, xf)) : X("", !0),
				q("p", Cf, [Y(F(_.value === "today" ? i.value.today : i.value.tomorrow), 1), pe.value ? (W(), G("span", wf, " · " + F(pe.value), 1)) : X("", !0)]),
				J(_u, {
					series: h.value,
					hass: e.hass,
					loading: g.value
				}, null, 8, [
					"series",
					"hass",
					"loading"
				])
			])], 8, Ld), l.value ? (W(), G("section", Tf, [
				q("header", null, [q("div", null, [q("h2", null, F(i.value.charging), 1)]), J(No, null, {
					default: An(() => [q("button", {
						ref_key: "chargingButton",
						ref: oe,
						type: "button",
						disabled: O.value || ce.value || se.value?.pending,
						"aria-busy": ce.value,
						"aria-expanded": ne.value,
						onClick: n[10] ||= (e) => ne.value ? Pe() : ne.value = !0
					}, F(ce.value ? i.value.saving : ne.value ? i.value.done : i.value.edit), 9, Ef), ne.value ? (W(), G("button", {
						key: 0,
						type: "button",
						disabled: ce.value || se.value?.pending,
						onClick: Ne
					}, F(i.value.cancel), 9, Df)) : X("", !0)]),
					_: 1
				})]),
				l.value ? (W(), G("section", Of, [
					q("label", {
						class: "electricity-master",
						"aria-busy": w.value !== null
					}, [q("input", {
						type: "checkbox",
						role: "switch",
						checked: m.value === !0,
						"aria-describedby": v.value && y.value === "activation" ? "electricity-master-status electricity-activation-error" : "electricity-master-status",
						disabled: !d.value || C.value || m.value === null || O.value || P.value,
						onChange: De
					}, null, 40, Af), Y(F(i.value.automatic), 1)], 8, kf),
					q("p", jf, F(w.value === null ? "" : w.value ? i.value.turningOn : i.value.turningOff), 1),
					v.value && y.value === "activation" ? (W(), G("p", Mf, F(v.value), 1)) : X("", !0),
					S.value && y.value === "activation" ? (W(), G("button", {
						key: 1,
						type: "button",
						disabled: C.value || !u.value,
						onClick: je
					}, F(i.value.reload), 9, Nf)) : X("", !0),
					u.value ? d.value ? P.value || O.value ? (W(), G("p", If, F(i.value.editFirst), 1)) : (W(), G("p", Lf, F(m.value === null ? i.value.unavailable : m.value ? i.value.activationOn : i.value.activationOff), 1)) : (W(), G("p", Ff, F(i.value.readonly), 1)) : (W(), G("p", Pf, F(i.value.disconnected), 1))
				])) : X("", !0),
				s.value === "dynamic" ? (W(), K($u, {
					key: 1,
					ref_key: "chargingSettings",
					ref: se,
					editing: ne.value,
					onApply: Pe
				}, null, 8, ["editing"])) : X("", !0),
				s.value === "time_of_use" ? (W(), K(_d, {
					key: 2,
					ref_key: "chargingSettings",
					ref: se,
					editing: ne.value,
					hass: e.hass,
					onApply: Pe
				}, null, 8, ["editing", "hass"])) : X("", !0),
				ne.value ? X("", !0) : (W(), G("div", Rf, [(W(!0), G(U, null, H(_e.value, (e) => (W(), G(U, { key: e?.metadata.entity_id }, [e?.error ? (W(), G("p", zf, F(e.name) + ": " + F(e.error), 1)) : e?.pending ? (W(), G("p", Bf, F(e.name) + ": " + F(i.value.entityPending), 1)) : X("", !0)], 64))), 128))])),
				ne.value ? (W(), G("div", Vf, [J(No, {
					class: "electricity-actions",
					"aria-busy": ce.value
				}, {
					default: An(() => [q("button", {
						type: "button",
						disabled: O.value || ce.value || se.value?.pending,
						onClick: Pe
					}, F(ce.value ? i.value.saving : i.value.done), 9, Hf), q("button", {
						type: "button",
						disabled: ce.value || se.value?.pending,
						onClick: Ne
					}, F(i.value.cancel), 9, Uf)]),
					_: 1
				}, 8, ["aria-busy"]), ce.value ? (W(), G("p", Wf, F(i.value.entityPending), 1)) : X("", !0)])) : X("", !0),
				c.value ? (W(), G("div", Gf, [J(ds, {
					domain: "sensor",
					"entity-key": "timed_charge_active_text"
				})])) : X("", !0),
				l.value ? (W(), G("section", {
					key: 6,
					class: "electricity-plan",
					"aria-label": i.value.details
				}, [
					s.value !== "time_of_use" && !c.value ? (W(), G("h3", qf, F(i.value.details), 1)) : X("", !0),
					c.value ? X("", !0) : (W(), G("dl", Jf, [q("div", null, [q("dt", null, F(i.value.pvSummary), 1), q("dd", null, F(xe.value), 1)])])),
					s.value === "time_of_use" || c.value ? (W(), K(Rc, {
						key: 2,
						hass: e.hass,
						automatic: m.value === !0
					}, null, 8, ["hass", "automatic"])) : (W(), G(U, { key: 3 }, [
						J(ds, {
							domain: "sensor",
							"entity-key": "price_charge_active_text"
						}),
						J(ds, {
							domain: "sensor",
							"entity-key": "price_charge_status_text"
						}),
						J(ds, {
							domain: "sensor",
							"entity-key": "price_charge_next_start"
						}),
						he.value === null ? X("", !0) : (W(), G("p", Yf, [Y(F(i.value.plannedPv) + ": ", 1), q("strong", null, F(he.value) + " kWh", 1)]))
					], 64))
				], 8, Kf)) : X("", !0)
			])) : X("", !0)])) : X("", !0),
			l.value ? (W(), G("p", Xf, F(i.value.gross), 1)) : X("", !0)
		]));
	}
}), [["styles", [".electricity-tariff-view{gap:16px;min-width:0;margin-top:12px;display:grid}.electricity-card{border:1px solid var(--divider-color,#ddd);border-radius:var(--ha-card-border-radius,12px);background:var(--card-background-color,#fff);min-width:0;padding:16px 18px}.electricity-card h2{margin:0;font-size:18px}.electricity-card h3{margin:20px 0 10px;font-size:16px}.electricity-card p{margin:10px 0 0;line-height:1.6}.electricity-card button{font:inherit;cursor:pointer;border:1px solid var(--divider-color,#ddd);min-height:44px;color:var(--primary-color,#03a9f4);background:0 0;border-radius:7px;padding:8px 12px}.electricity-card button:disabled{opacity:.5;cursor:default}.electricity-card header,.electricity-tariff-bar__row{flex-wrap:wrap;justify-content:space-between;align-items:center;gap:16px;display:flex}.electricity-card header>div:not(.editor-actions){flex:1;min-width:0}.electricity-card header>.editor-actions{white-space:nowrap;flex-shrink:0}.electricity-active{flex-wrap:wrap;align-items:center;gap:10px;display:flex}.electricity-active>span,.electricity-muted{color:var(--secondary-text-color,#666)}.electricity-master{cursor:pointer;align-items:center;gap:10px;min-height:44px;display:flex}.electricity-master-status:empty{display:none}.electricity-master-status{border-left:3px solid var(--primary-color,#03a9f4);background:var(--secondary-background-color,#f5f5f5);padding:10px 14px;font-weight:500}.electricity-activation .electricity-master{margin-top:0;font-weight:600}.electricity-price-details{margin-top:16px}.electricity-master[aria-busy=true]{cursor:progress}.electricity-master input{width:22px;height:22px;accent-color:var(--primary-color,#03a9f4);flex-shrink:0}.electricity-choice{border-top:1px solid var(--divider-color,#ddd);margin-top:16px;padding-top:16px}.electricity-choice fieldset{border:0;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;min-width:0;padding:0;display:grid}.electricity-choice fieldset>label{border:1px solid var(--divider-color,#ddd);cursor:pointer;border-radius:8px;gap:12px;padding:14px;display:flex}.electricity-choice input{accent-color:var(--primary-color,#03a9f4);flex-shrink:0;width:20px;height:20px}.electricity-choice strong,.electricity-choice small{display:block}.electricity-choice small{color:var(--secondary-text-color,#666);margin-top:5px;font-size:14px}.electricity-actions{margin-top:16px}.electricity-current-price{font-size:32px;font-weight:500;line-height:1.1!important}.electricity-current-price span{font-size:16px;font-weight:400}.electricity-days{gap:6px;margin-top:12px;display:flex}.electricity-days [aria-pressed=true]{background:var(--secondary-background-color,#eee);border-color:var(--primary-color,#03a9f4)}.electricity-day{margin:20px 0!important}.electricity-error{color:var(--error-color,#db4437)}.electricity-price-editor [aria-invalid=true]{border-color:var(--error-color,#db4437);outline:1px solid var(--error-color,#db4437)}.electricity-fields{grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:16px;display:grid}.electricity-fields>label{flex-direction:column;gap:6px;min-width:0;font-size:14px;display:flex}.electricity-fields input,.electricity-fields select{width:100%;min-width:0;min-height:44px;font:inherit;color:var(--primary-text-color,#222);background:var(--card-background-color,#fff);border:1px solid var(--divider-color,#ccc);border-radius:6px;padding:10px}.electricity-price-editor fieldset{border:0;min-width:0;margin:0;padding:0}.electricity-price-advanced{border-top:1px solid var(--divider-color,#ddd);margin-top:16px;padding-top:12px}.electricity-price-advanced>summary{cursor:pointer;align-content:center;min-height:44px}.dynamic-charging-settings .entity-control,.electricity-charging-editor .entity-control{margin-top:12px}.electricity-price-details>summary{cursor:pointer;align-content:center;min-height:44px;font-size:14px;font-weight:500;display:list-item}.electricity-plan>.charge-plan{box-shadow:none;border:0;padding:16px 0 0}.electricity-sr-only{clip-path:inset(50%);width:1px;height:1px;position:absolute;overflow:hidden}@media (max-width:700px){.electricity-tariff-bar__row{flex-direction:column;align-items:flex-start}.electricity-fields,.electricity-choice fieldset{grid-template-columns:minmax(0,1fr)}.electricity-card{padding:16px}.electricity-card header{align-items:flex-start}.electricity-current-price{font-size:28px}}.electricity-columns{align-items:start;gap:16px;min-width:0;display:grid}.electricity-card.electricity-tariff-bar{background:0 0;border:0;padding:0}.electricity-tariff-bar__row{justify-content:flex-end}.electricity-active>strong{color:var(--primary-text-color,#212121)}.electricity-price-card{container:sax-tariff-prices/inline-size}.electricity-card.electricity-prices{border:0;border-radius:0;padding:0}.electricity-prices>header,.electricity-charging>header{border-bottom:1px solid var(--divider-color,#ddd);margin-bottom:14px;padding-bottom:12px}.electricity-card .electricity-current-price{margin:3px 0 0}.electricity-current{min-width:0}.electricity-prices>.electricity-current{margin:14px 0}.electricity-activation{background:var(--secondary-background-color,#f5f5f5);border-radius:8px;margin-bottom:12px;padding:8px 12px 12px}.electricity-activation>p{color:var(--secondary-text-color,#666);margin-top:2px}.electricity-summary-rows{margin:0}.electricity-summary-rows>div{border-bottom:1px solid var(--divider-color,#ddd);justify-content:space-between;align-items:center;gap:8px 16px;min-height:41px;padding:7px 0;display:flex}.electricity-summary-rows dt{color:var(--secondary-text-color,#666)}.electricity-summary-rows dd{text-align:right;overflow-wrap:anywhere;min-width:0;margin:0}.electricity-targets{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:12px 0;display:grid}.electricity-target{background:var(--secondary-background-color,#f5f5f5);border-radius:8px;flex-direction:column;gap:4px;min-width:0;padding:10px 12px;display:flex}.electricity-target>span{color:var(--secondary-text-color,#666);font-size:14px}.electricity-target>strong{overflow-wrap:anywhere;font-size:24px;font-weight:500}.electricity-charge-status .entity-value{padding:12px 0}.electricity-plan,.electricity-price-details,.tou-charging-rules{border-top:1px solid var(--divider-color,#ddd);margin-top:10px;padding-top:0}.tou-charging-rules>summary{cursor:pointer;align-content:center;min-height:44px}.electricity-footnote{color:var(--secondary-text-color,#666);margin:0;font-size:13px}@container sax-content (width>=860px){.electricity-columns{grid-template-columns:minmax(0,1.14fr) minmax(0,1fr)}.electricity-tariff-view{margin-top:-36px}.electricity-tariff-bar__row{min-height:44px;padding-left:260px}}@container sax-tariff-prices (width<=560px){.electricity-fields{grid-template-columns:minmax(0,1fr);gap:10px}}"]]]), Qf = { class: "year" }, $f = ["viewBox", "aria-label"], ep = ["x", "y"], tp = [
	"x2",
	"y1",
	"y2"
], np = ["x", "y"], rp = [
	"x2",
	"y1",
	"y2"
], ip = ["x1", "x2"], ap = ["x", "y"], op = ["x1", "x2"], sp = [
	"y1",
	"x2",
	"y2",
	"stroke",
	"stroke-dasharray"
], cp = [
	"cx",
	"cy",
	"fill"
], lp = { class: "selection" }, up = ["for"], dp = ["for"], fp = [
	"id",
	"max",
	"aria-valuetext"
], pp = ["aria-label"], mp = {
	viewBox: "0 0 28 12",
	width: "28",
	height: "12",
	"aria-hidden": "true"
}, hp = ["stroke", "stroke-dasharray"], gp = 254, _p = 52, vp = 26, yp = 204, bp = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "TariffComparisonCostChart",
	props: {
		language: { type: String },
		annualConsumption: { type: Number },
		tariffs: { type: Array }
	},
	setup(e) {
		let t = e, n = Z(() => t.language === "de" ? {
			title: "Jahreskosten nach Stromverbrauch",
			year: "Tarifjahr",
			firstYear: "Erstes Jahr",
			laterYears: "Folgejahre",
			cost: "Jahreskosten (€)",
			consumption: "Jahresverbrauch (kWh)",
			selection: "Jahresverbrauch im Diagramm (kWh)",
			selectedCosts: "Kosten beim ausgewählten Verbrauch"
		} : {
			title: "Annual costs by electricity consumption",
			year: "Tariff year",
			firstYear: "First year",
			laterYears: "Subsequent years",
			cost: "Annual cost (€)",
			consumption: "Annual consumption (kWh)",
			selection: "Annual consumption in chart (kWh)",
			selectedCosts: "Costs at selected consumption"
		}), r = Z(() => t.language === "de" ? "de-DE" : "en-GB"), i = Z(() => new Intl.NumberFormat(r.value, { maximumFractionDigits: 2 })), a = Z(() => new Intl.NumberFormat(r.value, {
			notation: "compact",
			maximumFractionDigits: 1
		})), o = Z(() => new Intl.NumberFormat(r.value, {
			notation: "scientific",
			maximumFractionDigits: 1
		})), s = Z(() => new Intl.NumberFormat(r.value, {
			style: "currency",
			currency: "EUR"
		})), c = [
			"#0081a5",
			"#b75128",
			"#725ec3",
			"#43882e",
			"#aa417c",
			"#77742b"
		], l = [
			"none",
			"8 4",
			"3 4",
			"10 4 3 4",
			"2 3",
			"5 3 2 3"
		], u = `sax-cost-chart-${Kn()}`, d = /* @__PURE__ */ z(!0), f = /* @__PURE__ */ z(t.annualConsumption), p = /* @__PURE__ */ z(), m = /* @__PURE__ */ z(620), h;
		V(() => t.annualConsumption, (e) => {
			f.value = e;
		}), or(() => {
			let e = p.value;
			e && (m.value = Math.max(180, e.clientWidth), !(typeof ResizeObserver > "u") && (h = new ResizeObserver(([e]) => {
				e && (m.value = Math.max(180, Math.round(e.contentRect.width)));
			}), h.observe(e)));
		}), cr(() => h?.disconnect());
		let g = Z(() => m.value - 22);
		function _(e) {
			let t = Math.abs(e);
			return t >= 0xe8d4a51000 ? o.value.format(e) : t >= 1e4 ? a.value.format(e) : i.value.format(e);
		}
		function v(e, t) {
			let n = d.value ? e.firstYearAtZero : e.standardAtZero, r = t === 0 ? n : n + e.annualCostPerKwh * t;
			return Math.min(Number.MAX_VALUE, Math.max(-Number.MAX_VALUE, r));
		}
		let y = Z(() => {
			if (t.annualConsumption === 0) return 6e3;
			let e = Math.min(Number.MAX_VALUE, Math.max(100, t.annualConsumption * 2)), n = 10 ** Math.floor(Math.log10(e));
			return Math.min(Number.MAX_VALUE, Math.ceil(e / n) * n);
		}), b = Z(() => t.tariffs.map((e, t) => ({
			tariff: e,
			start: v(e, 0),
			end: v(e, y.value),
			color: c[t % c.length],
			dash: l[(t + Math.floor(t / c.length)) % l.length]
		}))), x = Z(() => {
			let e = b.value.reduce(({ low: e, high: t }, { start: n, end: r }) => ({
				low: Math.min(e, n),
				high: Math.max(t, r)
			}), {
				low: 0,
				high: 0
			}), t = Math.max(1, -e.low, e.high);
			return {
				low: e.low / t,
				high: e.high / t || +(e.low === 0),
				scale: t
			};
		}), S = Z(() => [
			0,
			.25,
			.5,
			.75,
			1
		].map((e) => y.value * e)), C = Z(() => {
			let { low: e, high: t, scale: n } = x.value;
			return [
				0,
				.25,
				.5,
				.75,
				1
			].map((r) => (e + r * (t - e)) * n);
		});
		function w(e) {
			return _p + e / y.value * (g.value - _p);
		}
		function T(e) {
			let { low: t, high: n, scale: r } = x.value;
			return yp - (e / r - t) / (n - t) * 178;
		}
		function E(e) {
			let t = e.costAtConsumption(f.value, d.value);
			return t === null ? "—" : s.value.format(t);
		}
		return (e, t) => (W(), G("div", {
			ref_key: "container",
			ref: p,
			class: "cost-chart"
		}, [
			q("fieldset", Qf, [
				q("legend", null, F(n.value.year), 1),
				q("label", null, [jn(q("input", {
					"onUpdate:modelValue": t[0] ||= (e) => d.value = e,
					name: u,
					type: "radio",
					value: !0
				}, null, 512), [[Za, d.value]]), Y(" " + F(n.value.firstYear), 1)]),
				q("label", null, [jn(q("input", {
					"onUpdate:modelValue": t[1] ||= (e) => d.value = e,
					name: u,
					type: "radio",
					value: !1
				}, null, 512), [[Za, d.value]]), Y(" " + F(n.value.laterYears), 1)])
			]),
			(W(), G("svg", {
				viewBox: `0 0 ${m.value} ${gp}`,
				role: "img",
				"aria-label": n.value.title
			}, [
				q("text", {
					x: _p,
					y: "14"
				}, F(n.value.cost), 1),
				q("text", {
					x: (_p + g.value) / 2,
					y: 247,
					"text-anchor": "middle"
				}, F(n.value.consumption), 9, ep),
				(W(!0), G(U, null, H(C.value, (e, t) => (W(), G("g", { key: t }, [q("line", {
					class: "grid-line",
					x1: _p,
					x2: g.value,
					y1: T(e),
					y2: T(e)
				}, null, 8, tp), q("text", {
					x: 46,
					y: T(e) + 4,
					"text-anchor": "end"
				}, F(_(e)), 9, np)]))), 128)),
				x.value.low < 0 && x.value.high > 0 ? (W(), G("line", {
					key: 0,
					class: "zero-line",
					x1: _p,
					x2: g.value,
					y1: T(0),
					y2: T(0)
				}, null, 8, rp)) : X("", !0),
				(W(!0), G(U, null, H(S.value, (e) => (W(), G("g", { key: e }, [q("line", {
					class: "grid-line",
					x1: w(e),
					x2: w(e),
					y1: vp,
					y2: yp
				}, null, 8, ip), q("text", {
					x: w(e),
					y: 222,
					"text-anchor": "middle"
				}, F(_(e)), 9, ap)]))), 128)),
				q("line", {
					class: "cursor-line",
					x1: w(f.value),
					x2: w(f.value),
					y1: vp,
					y2: yp
				}, null, 8, op),
				(W(!0), G(U, null, H(b.value, ({ tariff: e, start: t, end: n, color: r, dash: i }) => (W(), G("g", { key: e.id }, [q("line", {
					class: "tariff-line",
					x1: _p,
					y1: T(t),
					x2: g.value,
					y2: T(n),
					stroke: r,
					"stroke-dasharray": i
				}, null, 8, sp), q("circle", {
					cx: w(f.value),
					cy: T(v(e, f.value)),
					r: "3.5",
					fill: r
				}, null, 8, cp)]))), 128))
			], 8, $f)),
			q("div", lp, [
				q("label", { for: `${u}-consumption` }, F(n.value.selection), 9, up),
				q("output", { for: `${u}-consumption` }, F(i.value.format(f.value)) + " kWh", 9, dp),
				jn(q("input", {
					id: `${u}-consumption`,
					"onUpdate:modelValue": t[2] ||= (e) => f.value = e,
					type: "range",
					min: "0",
					max: y.value,
					step: "any",
					"aria-valuetext": `${i.value.format(f.value)} kWh`
				}, null, 8, fp), [[
					Xa,
					f.value,
					void 0,
					{ number: !0 }
				]])
			]),
			q("ul", {
				class: "selected-costs",
				role: "list",
				"aria-label": n.value.selectedCosts
			}, [(W(!0), G(U, null, H(b.value, ({ tariff: e, color: t, dash: n }) => (W(), G("li", { key: e.id }, [
				(W(), G("svg", mp, [q("line", {
					class: "tariff-line",
					x1: "1",
					y1: "6",
					x2: "27",
					y2: "6",
					stroke: t,
					"stroke-dasharray": n
				}, null, 8, hp)])),
				q("span", null, F(e.name), 1),
				q("strong", null, F(E(e)), 1)
			]))), 128))], 8, pp)
		], 512));
	}
}), [["styles", [".cost-chart[data-v-fa86b695]{gap:12px;min-width:0;display:grid}.year[data-v-fa86b695]{border:0;flex-wrap:wrap;column-gap:20px;min-width:0;margin:0;padding:0;display:flex}.year legend[data-v-fa86b695],.selection label[data-v-fa86b695]{padding:0;font-weight:500}.year label[data-v-fa86b695]{cursor:pointer;align-items:center;gap:8px;min-height:44px;display:flex}.year input[data-v-fa86b695]{width:20px;height:20px;margin:0}.cost-chart>svg[data-v-fa86b695]{width:100%;display:block}svg text[data-v-fa86b695]{fill:var(--secondary-text-color,#666);font:inherit;font-size:11px}.grid-line[data-v-fa86b695],.zero-line[data-v-fa86b695],.cursor-line[data-v-fa86b695]{stroke:var(--divider-color,#ddd)}.zero-line[data-v-fa86b695],.cursor-line[data-v-fa86b695]{stroke:var(--secondary-text-color,#666)}.cursor-line[data-v-fa86b695]{stroke-dasharray:3 4}.tariff-line[data-v-fa86b695]{stroke-width:2.5px;stroke-linecap:round;vector-effect:non-scaling-stroke}.selection[data-v-fa86b695]{flex-wrap:wrap;justify-content:space-between;gap:4px 16px;display:flex}.selection input[data-v-fa86b695]{width:100%;min-height:44px;margin:0}.selection output[data-v-fa86b695]{font-variant-numeric:tabular-nums}.selected-costs[data-v-fa86b695]{grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr));gap:8px 16px;margin:0;padding:0;list-style:none;display:grid}.selected-costs li[data-v-fa86b695]{border-bottom:1px solid var(--divider-color,#ddd);overflow-wrap:anywhere;grid-template-columns:28px 1fr auto;align-items:center;gap:8px;padding-block:4px;display:grid}.selected-costs strong[data-v-fa86b695]{font-variant-numeric:tabular-nums}"]], ["__scopeId", "data-v-fa86b695"]]), xp = 86400, Sp = {
	coefficient: 0n,
	scale: 0
}, Cp = {
	coefficient: 100n,
	scale: 0
};
function wp(e) {
	let t = e.trim();
	return /^(?:[01]?\d|2[0-3])$/.test(t) ? `${t.padStart(2, "0")}:00` : zs(e);
}
function Tp(e) {
	let [t, n = "0"] = e.split("e"), [r, i = ""] = t.split(".");
	return {
		coefficient: BigInt(`${r || "0"}${i}`),
		scale: i.length - Number(n)
	};
}
function Ep(e, t = !1) {
	let n = e.trim().replace(",", ".");
	return n ? n.length > 1e3 ? {
		value: null,
		error: "outOfRange"
	} : /^-?(?:\d+(?:\.\d+)?|\.\d+)$/.test(n) ? n.startsWith("-") ? {
		value: null,
		error: "negative"
	} : Number.isFinite(Number(n)) ? { value: Tp(n) } : {
		value: null,
		error: "outOfRange"
	} : {
		value: null,
		error: "invalidNumber"
	} : t ? { value: Sp } : {
		value: null,
		error: "required"
	};
}
function Dp(e) {
	return Ep(e).error;
}
function Op(e, t) {
	let n = Math.max(e.scale, t.scale);
	return {
		coefficient: e.coefficient * 10n ** BigInt(n - e.scale) + t.coefficient * 10n ** BigInt(n - t.scale),
		scale: n
	};
}
function kp(e, t) {
	return Op(e, {
		coefficient: -t.coefficient,
		scale: t.scale
	});
}
function Ap(e, t) {
	return {
		coefficient: e.coefficient * t.coefficient,
		scale: e.scale + t.scale
	};
}
function jp(e) {
	return Number(`${e.coefficient}e${-e.scale}`);
}
function Mp(e) {
	if (e.scale <= 2) return jp(e);
	let t = 10n ** BigInt(e.scale - 2), n = e.coefficient < 0n ? -1n : 1n;
	return jp({
		coefficient: (e.coefficient * n + t / 2n) / t * n,
		scale: 2
	});
}
function Np(e, t) {
	e.sort((e, t) => e.start - t.start);
	let n;
	for (let r of e) {
		if (n && r.start < n.end) for (let e of [n.windowIndex, r.windowIndex]) t[e].start = "overlap", t[e].end = "overlap";
		(!n || r.end > n.end) && (n = r);
	}
}
function Pp(e, t) {
	let n = Ep(e), r = Ep(t.price), i = Ep(t.baseFee), a = Ep(t.bonus, !0), o = { windowFields: [] };
	n.error && (o.annualConsumption = n.error), r.error && (o.price = r.error), i.error && (o.baseFee = i.error), a.error && (o.bonus = a.error);
	let s = Cp, c = Sp;
	if (t.type === "time-of-use") {
		t.windows.length === 0 && (o.windows = "missingWindow");
		let e = [];
		t.windows.forEach((t, n) => {
			let r = {};
			o.windowFields.push(r);
			let i = $(wp(t.start)), a = $(wp(t.end));
			i === null && (r.start = t.start.trim() ? "invalidTime" : "required"), a === null && (r.end = t.end.trim() ? "invalidTime" : "required"), i !== null && a !== null && (i === a ? r.end = "sameTime" : i < a ? e.push({
				start: i,
				end: a,
				windowIndex: n
			}) : (e.push({
				start: i,
				end: xp,
				windowIndex: n
			}), a > 0 && e.push({
				start: 0,
				end: a,
				windowIndex: n
			})));
			let l = Ep(t.price);
			l.error && (r.price = l.error);
			let u = Ep(t.share);
			u.error ? r.share = u.error : kp(Cp, u.value).coefficient < 0n ? r.share = "shareTooHigh" : (s = kp(s, u.value), l.value !== null && (c = Op(c, Ap(l.value, u.value))));
		}), Np(e, o.windowFields), s.coefficient < 0n && (o.windows = "totalShareTooHigh");
	}
	if (n.value === null || r.value === null || i.value === null || a.value === null || o.windows || o.windowFields.some((e) => Object.keys(e).length > 0)) return {
		valid: !1,
		errors: o
	};
	let l = Op(Ap(r.value, s), c), u = {
		...l,
		scale: l.scale + 4
	}, d = Ap(n.value, u), f = {
		...i.value,
		coefficient: i.value.coefficient * (t.baseFeePeriod === "monthly" ? 12n : 1n)
	}, p = Op(d, f), m = Mp(d), h = Mp(f), g = Mp(p);
	if (Number.isFinite(m) || (o.price = "outOfRange"), Number.isFinite(h) || (o.baseFee = "outOfRange"), o.price || o.baseFee) return {
		valid: !1,
		errors: o
	};
	if (!Number.isFinite(g)) return o.price = "outOfRange", {
		valid: !1,
		errors: o
	};
	let _ = kp(f, a.value);
	return {
		valid: !0,
		annualEnergyCost: m,
		annualBaseFee: h,
		annualCost: g,
		firstYearCost: Mp(Op(d, _)),
		bonus: Mp(a.value),
		standardShare: jp(s),
		firstYearAtZero: jp(_),
		standardAtZero: jp(f),
		annualCostPerKwh: jp(u),
		costAtConsumption(e, t) {
			if (!Number.isFinite(e) || e < 0) return null;
			let n = Mp(Op(Ap(Tp(String(e)), u), t ? _ : f));
			return Number.isFinite(n) ? n : null;
		}
	};
}
//#endregion
//#region src/components/TariffComparisonField.vue?vue&type=script&setup=true&lang.ts
var Fp = { class: "field" }, Ip = ["for"], Lp = [
	"id",
	"inputmode",
	"placeholder",
	"aria-invalid",
	"aria-describedby"
], Rp = ["id"], zp = /* @__PURE__ */ Gn({
	__name: "TariffComparisonField",
	props: /*@__PURE__*/ _r({
		id: { type: String },
		label: { type: String },
		error: { type: String },
		time: { type: Boolean }
	}, {
		modelValue: { required: !0 },
		modelModifiers: {}
	}),
	emits: ["update:modelValue"],
	setup(e) {
		let t = e, n = Sr(e, "modelValue"), r = /* @__PURE__ */ z(!1), i = Z(() => t.error && (r.value || n.value.trim()));
		function a(e) {
			let i = e.currentTarget, a = t.time ? wp(i.value) : i.value;
			i.value !== a && (i.value = a), n.value = a, r.value = !0;
		}
		return (t, r) => (W(), G("div", Fp, [
			q("label", { for: e.id }, F(e.label), 9, Ip),
			jn(q("input", {
				id: e.id,
				"onUpdate:modelValue": r[0] ||= (e) => n.value = e,
				inputmode: e.time ? "numeric" : "decimal",
				placeholder: e.time ? "HH:MM" : void 0,
				"aria-invalid": i.value ? !0 : void 0,
				"aria-describedby": i.value ? `${e.id}-error` : void 0,
				onChange: a,
				onBlur: a
			}, null, 40, Lp), [[Xa, n.value]]),
			i.value ? (W(), G("span", {
				key: 0,
				id: `${e.id}-error`,
				class: "error"
			}, F(e.error), 9, Rp)) : X("", !0)
		]));
	}
}), Bp = { class: "toolbar" }, Vp = { class: "actions" }, Hp = [
	"aria-expanded",
	"aria-controls",
	"disabled"
], Up = ["disabled"], Wp = {
	key: 0,
	class: "hint"
}, Gp = {
	key: 1,
	class: "hint"
}, Kp = ["id"], qp = {
	key: 1,
	class: "hint",
	role: "status"
}, Jp = {
	key: 3,
	class: "tariffs"
}, Yp = ["aria-labelledby"], Xp = { class: "card-header" }, Zp = ["id"], Qp = ["onClick"], $p = { class: "fields" }, em = { class: "field" }, tm = ["for"], nm = ["id", "onUpdate:modelValue"], rm = { class: "field" }, im = ["for"], am = [
	"id",
	"onUpdate:modelValue",
	"onChange"
], om = { value: "fixed" }, sm = { value: "time-of-use" }, cm = {
	key: 0,
	class: "field"
}, lm = ["for"], um = ["id", "onUpdate:modelValue"], dm = { value: "monthly" }, fm = { value: "yearly" }, pm = { class: "hint" }, mm = { class: "fields" }, hm = { class: "actions" }, gm = ["onClick"], _m = ["onClick"], vm = {
	key: 0,
	class: "error"
}, ym = ["id", "onClick"], bm = ["aria-labelledby"], xm = ["id"], Sm = { scope: "col" }, Cm = { key: 0 }, wm = { scope: "row" }, Tm = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "TariffComparisonView",
	props: { language: { type: String } },
	setup(e) {
		let t = e, n = {
			de: {
				annualConsumption: "Jahresverbrauch (kWh)",
				addTariff: "Tarif hinzufügen",
				reset: "Zurücksetzen",
				tariff: "Tarif",
				name: "Tarifname",
				type: "Tarifart",
				fixed: "Fixpreis",
				timeOfUse: "Zeitvariabel",
				price: "Arbeitspreis (ct/kWh)",
				standardPrice: "Standardpreis (ct/kWh)",
				baseFee: "Grundgebühr (€)",
				baseFeePeriod: "Zeitraum der Grundgebühr",
				monthly: "Pro Monat",
				yearly: "Pro Jahr",
				bonus: "Einmaliger Bonus (€)",
				removeTariff: "Tarif entfernen",
				pricesHint: "Preise inklusive Steuern eingeben. Zahlen ohne Tausendertrennzeichen eingeben.",
				windowsHint: "Die Zeitfenster gelten täglich. Gib eine Uhrzeit wie 22, 2230 oder 22:30 ein. Die Anteile beziehen sich auf den Jahresverbrauch. Für den übrigen Verbrauch gilt der Standardpreis.",
				window: "Zeitfenster",
				addWindow: "Zeitfenster hinzufügen",
				copyWindow: "Zeitfenster kopieren",
				removeWindow: "Zeitfenster entfernen",
				start: "Beginn",
				end: "Ende",
				share: "Verbrauchsanteil (%)",
				comparison: "Jahreskosten im Vergleich",
				costChart: "Kostenverlauf",
				noValidTariffs: "Vervollständige einen Tarif, um seinen Kostenverlauf zu sehen.",
				costItem: "Kostenpunkt",
				standardShare: "Verbrauch zum Standardpreis",
				annualEnergyCost: "Verbrauchskosten pro Jahr",
				annualBaseFee: "Grundgebühr pro Jahr",
				firstYearBonus: "Bonus im ersten Jahr",
				firstYearCost: "Kosten im ersten Jahr",
				annualCost: "Kosten pro Folgejahr",
				incomplete: "Eingaben prüfen",
				noTariffs: "Gib den Jahresverbrauch ohne Tausendertrennzeichen ein (z. B. 3500) und füge einen Tarif hinzu.",
				errors: {
					required: "Bitte fülle dieses Feld aus.",
					invalidNumber: "Bitte gib eine gültige Zahl ein.",
					negative: "Der Wert muss mindestens 0 sein.",
					outOfRange: "Der Wert ist zu groß.",
					invalidTime: "Bitte gib eine gültige Uhrzeit ein, z. B. 22 oder 22:30.",
					sameTime: "Beginn und Ende müssen unterschiedlich sein.",
					overlap: "Dieses Zeitfenster überschneidet sich mit einem anderen.",
					shareTooHigh: "Der Verbrauchsanteil darf höchstens 100 % betragen.",
					totalShareTooHigh: "Die Verbrauchsanteile aller Zeitfenster dürfen zusammen höchstens 100 % betragen.",
					missingWindow: "Füge mindestens ein Zeitfenster hinzu."
				}
			},
			en: {
				annualConsumption: "Annual consumption (kWh)",
				addTariff: "Add tariff",
				reset: "Reset",
				tariff: "Tariff",
				name: "Tariff name",
				type: "Tariff type",
				fixed: "Fixed price",
				timeOfUse: "Time of use",
				price: "Unit price (ct/kWh)",
				standardPrice: "Standard price (ct/kWh)",
				baseFee: "Standing charge (€)",
				baseFeePeriod: "Standing charge period",
				monthly: "Per month",
				yearly: "Per year",
				bonus: "One-time bonus (€)",
				removeTariff: "Remove tariff",
				pricesHint: "Enter prices including taxes and numbers without thousands separators.",
				windowsHint: "Time windows apply every day. Enter times such as 22, 2230 or 22:30. Each share is a percentage of annual consumption. Remaining consumption is billed at the standard price.",
				window: "Time window",
				addWindow: "Add time window",
				copyWindow: "Copy time window",
				removeWindow: "Remove time window",
				start: "Start",
				end: "End",
				share: "Share of consumption (%)",
				comparison: "Annual cost comparison",
				costChart: "Cost trends",
				noValidTariffs: "Complete a tariff to see how its costs change with consumption.",
				costItem: "Cost item",
				standardShare: "Consumption at standard price",
				annualEnergyCost: "Annual energy cost",
				annualBaseFee: "Annual standing charge",
				firstYearBonus: "First-year bonus",
				firstYearCost: "First-year cost",
				annualCost: "Cost per subsequent year",
				incomplete: "Check inputs",
				noTariffs: "Enter annual consumption without thousands separators (e.g. 3500) and add a tariff.",
				errors: {
					required: "Fill in this field.",
					invalidNumber: "Enter a valid number.",
					negative: "The value must be at least 0.",
					outOfRange: "The value is too large.",
					invalidTime: "Enter a valid time, e.g. 22 or 22:30.",
					sameTime: "Start and end times must differ.",
					overlap: "This time window overlaps another one.",
					shareTooHigh: "The share of consumption must be at most 100%.",
					totalShareTooHigh: "The shares of all time windows together must be at most 100%.",
					missingWindow: "Add at least one time window."
				}
			}
		}, r = Z(() => n[t.language]), i = Z(() => t.language === "de" ? "de-DE" : "en-GB"), a = Z(() => new Intl.NumberFormat(i.value, {
			style: "currency",
			currency: "EUR"
		})), o = Z(() => new Intl.NumberFormat(i.value, {
			style: "percent",
			maximumFractionDigits: 6
		})), s = `sax-compare-${Kn()}`, c = /* @__PURE__ */ z(), l = /* @__PURE__ */ z(), u = /* @__PURE__ */ z(""), d = /* @__PURE__ */ z([]), f = /* @__PURE__ */ z(!1), p = 0, m = 0, h = Z(() => d.value.map((e) => ({
			tariff: e,
			name: e.name.trim() || `${r.value.tariff} ${e.number}`,
			result: Pp(u.value, e)
		}))), g = Z(() => h.value.flatMap(({ tariff: e, name: t, result: n }) => n.valid ? [{
			id: e.id,
			name: t,
			firstYearAtZero: n.firstYearAtZero,
			standardAtZero: n.standardAtZero,
			annualCostPerKwh: n.annualCostPerKwh,
			costAtConsumption: n.costAtConsumption
		}] : [])), _ = Z(() => Number(u.value.replace(",", "."))), v = `${s}-consumption`, y = Z(() => C(Dp(u.value))), b = [
			"standardShare",
			"annualEnergyCost",
			"annualBaseFee",
			"firstYearBonus",
			"firstYearCost",
			"annualCost"
		], x = [
			"price",
			"baseFee",
			"bonus"
		], S = [
			"start",
			"end",
			"price",
			"share"
		];
		function C(e) {
			return e ? r.value.errors[e] : void 0;
		}
		function w(e) {
			vn(() => c.value?.querySelector(`#${e}`)?.focus());
		}
		function T() {
			let e = `${s}-tariff-${++p}`;
			d.value.push({
				id: e,
				name: "",
				number: ++m,
				type: "fixed",
				price: "",
				baseFee: "",
				baseFeePeriod: "monthly",
				bonus: "",
				windows: []
			}), w(`${e}-name`);
		}
		function E(e, { index: t = e.windows.length, source: n, focus: r = !0 } = {}) {
			let i = `${s}-window-${++p}`;
			e.windows.splice(t, 0, {
				id: i,
				start: "",
				end: "",
				price: n?.price ?? "",
				share: n?.share ?? ""
			}), r && w(`${i}-start`);
		}
		function D(e) {
			e.type === "time-of-use" && !e.windows.length && E(e, { focus: !1 });
		}
		function O(e) {
			let t = d.value.indexOf(e);
			d.value.splice(t, 1);
			let n = d.value[t] ?? d.value[t - 1];
			n ? w(`${n.id}-name`) : (f.value = !1, l.value?.focus());
		}
		function k(e, t) {
			e.windows.splice(t, 1), w(`${e.id}-add-window`);
		}
		function ee() {
			d.value = [], f.value = !1, m = 0, l.value?.focus();
		}
		return (t, n) => (W(), G("div", {
			ref_key: "view",
			ref: c,
			class: "tariff-comparison-view"
		}, [
			q("div", Bp, [J(zp, {
				id: v,
				modelValue: u.value,
				"onUpdate:modelValue": n[0] ||= (e) => u.value = e,
				class: "consumption",
				label: r.value.annualConsumption,
				error: y.value
			}, null, 8, [
				"modelValue",
				"label",
				"error"
			]), q("div", Vp, [
				q("button", {
					ref_key: "addButton",
					ref: l,
					type: "button",
					class: "primary",
					onClick: T
				}, F(r.value.addTariff), 513),
				d.value.length ? (W(), G("button", {
					key: 0,
					type: "button",
					"aria-expanded": f.value,
					"aria-controls": `${s}-cost-chart`,
					disabled: !f.value && !g.value.length,
					onClick: n[1] ||= (e) => f.value = !f.value
				}, F(r.value.costChart), 9, Hp)) : X("", !0),
				q("button", {
					type: "button",
					disabled: !d.value.length,
					onClick: ee
				}, F(r.value.reset), 9, Up)
			])]),
			d.value.length ? (W(), G("p", Gp, F(r.value.pricesHint), 1)) : (W(), G("p", Wp, F(r.value.noTariffs), 1)),
			d.value.length ? jn((W(), G("div", {
				key: 2,
				id: `${s}-cost-chart`
			}, [f.value && g.value.length ? (W(), K(bp, {
				key: 0,
				language: e.language,
				"annual-consumption": _.value,
				tariffs: g.value
			}, null, 8, [
				"language",
				"annual-consumption",
				"tariffs"
			])) : f.value ? (W(), G("p", qp, F(r.value.noValidTariffs), 1)) : X("", !0)], 8, Kp)), [[ua, f.value]]) : X("", !0),
			d.value.length ? (W(), G("div", Jp, [(W(!0), G(U, null, H(h.value, ({ tariff: e, name: t, result: n }) => (W(), G("article", {
				key: e.id,
				class: "tariff",
				"aria-labelledby": `${e.id}-heading`
			}, [
				q("div", Xp, [q("h2", { id: `${e.id}-heading` }, F(t), 9, Zp), q("button", {
					type: "button",
					onClick: (t) => O(e)
				}, F(r.value.removeTariff), 9, Qp)]),
				q("div", $p, [
					q("div", em, [q("label", { for: `${e.id}-name` }, F(r.value.name), 9, tm), jn(q("input", {
						id: `${e.id}-name`,
						"onUpdate:modelValue": (t) => e.name = t
					}, null, 8, nm), [[Xa, e.name]])]),
					q("div", rm, [q("label", { for: `${e.id}-type` }, F(r.value.type), 9, im), jn(q("select", {
						id: `${e.id}-type`,
						"onUpdate:modelValue": (t) => e.type = t,
						onChange: (t) => D(e)
					}, [q("option", om, F(r.value.fixed), 1), q("option", sm, F(r.value.timeOfUse), 1)], 40, am), [[Qa, e.type]])]),
					(W(), G(U, null, H(x, (t) => (W(), G(U, { key: t }, [J(zp, {
						id: `${e.id}-${t}`,
						modelValue: e[t],
						"onUpdate:modelValue": (n) => e[t] = n,
						label: t === "price" && e.type === "time-of-use" ? r.value.standardPrice : r.value[t],
						error: n.valid ? void 0 : C(n.errors[t])
					}, null, 8, [
						"id",
						"modelValue",
						"onUpdate:modelValue",
						"label",
						"error"
					]), t === "baseFee" ? (W(), G("div", cm, [q("label", { for: `${e.id}-base-fee-period` }, F(r.value.baseFeePeriod), 9, lm), jn(q("select", {
						id: `${e.id}-base-fee-period`,
						"onUpdate:modelValue": (t) => e.baseFeePeriod = t
					}, [q("option", dm, F(r.value.monthly), 1), q("option", fm, F(r.value.yearly), 1)], 8, um), [[Qa, e.baseFeePeriod]])])) : X("", !0)], 64))), 64))
				]),
				e.type === "time-of-use" ? (W(), G(U, { key: 0 }, [
					q("p", pm, F(r.value.windowsHint), 1),
					(W(!0), G(U, null, H(e.windows, (t, i) => (W(), G("fieldset", { key: t.id }, [
						q("legend", null, F(r.value.window) + " " + F(i + 1), 1),
						q("div", mm, [(W(), G(U, null, H(S, (e) => J(zp, {
							id: `${t.id}-${e}`,
							key: e,
							modelValue: t[e],
							"onUpdate:modelValue": (n) => t[e] = n,
							label: r.value[e],
							time: e === "start" || e === "end",
							error: n.valid ? void 0 : C(n.errors.windowFields[i]?.[e])
						}, null, 8, [
							"id",
							"modelValue",
							"onUpdate:modelValue",
							"label",
							"time",
							"error"
						])), 64))]),
						q("div", hm, [q("button", {
							type: "button",
							onClick: (n) => E(e, {
								index: i + 1,
								source: t
							})
						}, F(r.value.copyWindow), 9, gm), q("button", {
							type: "button",
							onClick: (t) => k(e, i)
						}, F(r.value.removeWindow), 9, _m)])
					]))), 128)),
					!n.valid && n.errors.windows ? (W(), G("p", vm, F(r.value.errors[n.errors.windows]), 1)) : X("", !0),
					q("button", {
						id: `${e.id}-add-window`,
						type: "button",
						onClick: (t) => E(e)
					}, F(r.value.addWindow), 9, ym)
				], 64)) : X("", !0)
			], 8, Yp))), 128))])) : X("", !0),
			d.value.length ? (W(), G("div", {
				key: 4,
				class: "comparison",
				role: "region",
				"aria-labelledby": `${s}-results`,
				tabindex: "0"
			}, [q("table", null, [
				q("caption", { id: `${s}-results` }, F(r.value.comparison), 9, xm),
				q("thead", null, [q("tr", null, [q("th", Sm, F(r.value.costItem), 1), (W(!0), G(U, null, H(h.value, ({ tariff: e, name: t, result: n }) => (W(), G("th", {
					key: e.id,
					scope: "col"
				}, [Y(F(t) + " ", 1), n.valid ? X("", !0) : (W(), G("small", Cm, F(r.value.incomplete), 1))]))), 128))])]),
				q("tbody", null, [(W(), G(U, null, H(b, (e) => q("tr", {
					key: e,
					class: P({ total: e === "firstYearCost" || e === "annualCost" })
				}, [q("th", wm, F(r.value[e]), 1), (W(!0), G(U, null, H(h.value, ({ tariff: t, result: n }) => (W(), G("td", { key: t.id }, [n.valid ? e === "standardShare" ? (W(), G(U, { key: 1 }, [Y(F(t.type === "fixed" ? "—" : o.value.format(n.standardShare / 100)), 1)], 64)) : e === "firstYearBonus" ? (W(), G(U, { key: 2 }, [Y(F(a.value.format(n.bonus ? -n.bonus : 0)), 1)], 64)) : (W(), G(U, { key: 3 }, [Y(F(a.value.format(n[e])), 1)], 64)) : (W(), G(U, { key: 0 }, [Y("—")], 64))]))), 128))], 2)), 64))])
			])], 8, bm)) : X("", !0)
		], 512));
	}
}), [["styles", [".tariff-comparison-view[data-v-24b1d83e]{gap:16px;margin-top:16px;display:grid}.toolbar[data-v-24b1d83e],.actions[data-v-24b1d83e],.card-header[data-v-24b1d83e]{flex-wrap:wrap;align-items:start;gap:8px;display:flex}.toolbar[data-v-24b1d83e]{justify-content:space-between;align-items:end;gap:12px}.toolbar[data-v-24b1d83e]:has(.error){align-items:start}.tariffs[data-v-24b1d83e],.fields[data-v-24b1d83e]{grid-template-columns:repeat(auto-fit,minmax(min(100%,24rem),1fr));align-items:start;gap:12px;display:grid}.fields[data-v-24b1d83e]{grid-template-columns:repeat(2,minmax(0,1fr))}.card-header[data-v-24b1d83e]{justify-content:space-between;align-items:center}.card-header h2[data-v-24b1d83e]{margin:0}.tariff[data-v-24b1d83e],fieldset[data-v-24b1d83e]{border:1px solid var(--divider-color,#ddd);border-radius:8px;gap:12px;min-width:0;margin:0;padding:12px;display:grid}.tariff[data-v-24b1d83e]{padding:16px}.tariff button[data-v-24b1d83e]{justify-self:start}.field[data-v-24b1d83e]{gap:4px;min-width:0;display:grid}.field label[data-v-24b1d83e],[data-v-24b1d83e] .field label,legend[data-v-24b1d83e]{font-weight:500}.consumption[data-v-24b1d83e]{flex:0 220px}input[data-v-24b1d83e],[data-v-24b1d83e] .field input,select[data-v-24b1d83e],button[data-v-24b1d83e]{border:1px solid var(--divider-color,#aaa);max-width:100%;min-height:44px;color:inherit;background:var(--card-background-color,#fff);font:inherit;border-radius:6px;padding:6px 10px}input[data-v-24b1d83e],[data-v-24b1d83e] .field input,select[data-v-24b1d83e]{border-color:var(--input-idle-line-color,var(--secondary-text-color,#666));width:100%;min-width:0}button[data-v-24b1d83e]{cursor:pointer}button.primary[data-v-24b1d83e]{border-color:var(--primary-color,#03a9f4);background:var(--primary-color,#03a9f4);color:var(--text-primary-color,#fff);font-weight:600}button[data-v-24b1d83e]:disabled{cursor:default;opacity:.6}.hint[data-v-24b1d83e],.error[data-v-24b1d83e],[data-v-24b1d83e] .field .error{margin:0;line-height:1.5}.hint[data-v-24b1d83e],small[data-v-24b1d83e]{color:var(--secondary-text-color,#666)}.error[data-v-24b1d83e],[data-v-24b1d83e] .field .error{color:var(--error-color,#a23a2d)}[data-v-24b1d83e] .field input[aria-invalid=true]{border-color:var(--error-color,#a23a2d)}.comparison[data-v-24b1d83e]{max-width:100%;overflow-x:auto}table[data-v-24b1d83e]{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%}caption[data-v-24b1d83e]{text-align:start;padding:8px 0;font-size:18px;font-weight:500}th[data-v-24b1d83e],td[data-v-24b1d83e]{border-bottom:1px solid var(--divider-color,#ddd);text-align:end;padding:8px 12px}th[data-v-24b1d83e]:first-child{text-align:start;min-width:8rem}thead th[data-v-24b1d83e]{min-width:8rem}td[data-v-24b1d83e]{white-space:nowrap}small[data-v-24b1d83e]{font-weight:400;display:block}.total[data-v-24b1d83e]{background:var(--secondary-background-color,#f4f4f4);font-weight:600}@container sax-content (width<=430px){.fields[data-v-24b1d83e]{grid-template-columns:minmax(0,1fr)}th[data-v-24b1d83e],td[data-v-24b1d83e]{padding-inline:8px}thead th[data-v-24b1d83e]{min-width:5.5rem}th[data-v-24b1d83e]:first-child{min-width:8.5rem}}"]], ["__scopeId", "data-v-24b1d83e"]]), Em = { class: "savings-view" }, Dm = { class: "savings-overview" }, Om = ["aria-labelledby"], km = ["id"], Am = ["aria-labelledby"], jm = ["id"], Mm = {
	key: 0,
	class: "savings-progress"
}, Nm = ["id"], Pm = { class: "savings-large" }, Fm = [
	"role",
	"aria-labelledby",
	"aria-valuemin",
	"aria-valuemax",
	"aria-valuenow"
], Im = {
	key: 1,
	class: "savings-rows"
}, Lm = { key: 0 }, Rm = { key: 1 }, zm = { key: 2 }, Bm = { key: 3 }, Vm = ["aria-label"], Hm = { class: "savings-large" }, Um = ["aria-labelledby"], Wm = ["id"], Gm = ["for"], Km = ["id", "max"], qm = ["for"], Jm = ["id", "min"], Ym = { type: "submit" }, Xm = ["disabled"], Zm = {
	key: 0,
	role: "status"
}, Qm = {
	key: 1,
	role: "alert"
}, $m = { class: "savings-selected-dates" }, eh = { class: "savings-large" }, th = ["id"], nh = { class: "savings-chart-hint" }, rh = [
	"viewBox",
	"aria-labelledby",
	"aria-describedby"
], ih = ["id"], ah = [
	"x1",
	"x2",
	"y1",
	"y2"
], oh = ["x"], sh = ["x"], ch = ["x"], lh = ["x"], uh = [
	"x",
	"y",
	"width",
	"height"
], dh = { class: "savings-chart-table" }, fh = { class: "savings-table-scroll" }, ph = { class: "savings-table" }, mh = {
	key: 1,
	class: "savings-empty"
}, hh = { class: "savings-card savings-explanation" }, gh = {
	key: 1,
	class: "savings-card savings-status",
	role: "status"
}, _h = /*#__PURE__*/ ko(/* @__PURE__ */ Gn({
	__name: "SavingsView",
	props: {
		hass: { type: Object },
		entryId: { type: String }
	},
	setup(e) {
		let t = e, n = Pn(Co), r = Kn(), i = Z(() => n?.language.value === "de"), a = Z(() => i.value ? {
			loading: "Die Statistik wird geladen …",
			unavailable: "Nicht verfügbar",
			unknown: "Unbekannt",
			payback: "Amortisation",
			investment: "Für die Amortisationswerte bitte die Investitionskosten unter „Geräte & Dienste → SAX Power Home → Konfigurieren → Wirtschaftlichkeit“ hinterlegen.",
			prior: "Bereits vor Bilanzbeginn berücksichtigt",
			net: "Netto-Ersparnis",
			started: "Bilanzbeginn",
			periods: "Kalenderwerte",
			day: "Heute bisher",
			week: "Diese Woche bisher",
			month: "Dieser Monat bisher",
			year: "Dieses Jahr bisher",
			from: "Von",
			to: "Bis",
			range: "Freier Zeitraum",
			apply: "Zeitraum anzeigen",
			refresh: "Aktualisieren",
			selected: "Netto-Ersparnis im gewählten Zeitraum",
			chart: "Verlauf im gewählten Zeitraum",
			table: "Werte als Tabelle",
			noData: "Für diesen Zeitraum sind keine Recorder-Daten vorhanden.",
			noChartData: "Für das Diagramm liegen noch keine zusammengefassten Recorder-Daten vor.",
			chartHint: "Die Balken basieren auf zusammengefassten Stundenwerten. Der Zeitraumwert kann bereits neuere Fünf-Minuten-Daten enthalten.",
			noRecorder: "Die Recorder-Statistik ist derzeit nicht verfügbar.",
			failed: "Die Statistik konnte nicht geladen werden. Bitte erneut versuchen.",
			invalid: "Bitte ein gültiges Anfangs- und Enddatum wählen. Das Ende darf nicht vor dem Anfang liegen.",
			explain: "Hinweise zur Berechnung und Datenbasis",
			netHint: "Grundlage sind vermiedene Netzbezugskosten minus Netzladekosten und entgangene Einspeisevergütung. Spätere Kosten reduzieren das aktuelle Ergebnis; Mehrkosten erscheinen als negativer Wert.",
			calendarHint: "Kalenderwerte stammen aus der Recorder-Langzeitstatistik der Netto-Ersparnis. Bei aktualisierten Installationen kann diese Aufzeichnung jünger als der angezeigte Bilanzbeginn sein.",
			rangeHint: "Für freie Zeiträume fließen nur Daten seit Beginn dieser Recorder-Aufzeichnung ein. Eine frühere Auswahl erfindet keine Werte. Fehlt die Historie oder ist die Ergebnis-Entität vom Recorder ausgeschlossen, bleiben Wert und Diagramm unbekannt beziehungsweise leer. Bei einem manuellen Bilanzneustart innerhalb der Auswahl kann der Recorder signierte Änderungen vor und nach dem Neustart zusammenfassen. Der Vorlaufbetrag verändert diese Zeitraumwerte nicht.",
			disabled: "Die Wirtschaftlichkeitsberechnung ist deaktiviert. Bitte unter „Geräte & Dienste → SAX Power Home → Konfigurieren → Wirtschaftlichkeit“ konfigurieren.",
			price_unavailable: "Der Strompreis ist derzeit nicht verfügbar. Aktuelle Zeitraumwerte können unvollständig sein.",
			origin_unavailable: "Die Herkunft der Ladeenergie ist derzeit nicht bestimmbar.",
			partial_price_coverage: "Für einen Teil der Energie fehlte heute ein Preis. Das Ergebnis kann unvollständig sein.",
			missing: "Die Wirtschaftlichkeitsdaten sind momentan nicht verfügbar."
		} : {
			loading: "Loading statistics …",
			unavailable: "Unavailable",
			unknown: "Unknown",
			payback: "Payback",
			investment: "To show payback values, enter the investment cost under Devices & services → SAX Power Home → Configure → Economics.",
			prior: "Already accounted for before accounting started",
			net: "Net savings",
			started: "Accounting started",
			periods: "Calendar values",
			day: "Today so far",
			week: "This week so far",
			month: "This month so far",
			year: "This year so far",
			from: "From",
			to: "To",
			range: "Custom period",
			apply: "Show period",
			refresh: "Refresh",
			selected: "Net savings in the selected period",
			chart: "Changes in the selected period",
			table: "Show values as a table",
			noData: "There are no Recorder data for this period.",
			noChartData: "There are no aggregated Recorder data for the chart yet.",
			chartHint: "The bars use aggregated hourly values. The period value may already include more recent five-minute data.",
			noRecorder: "Recorder statistics are currently unavailable.",
			failed: "Statistics could not be loaded. Please try again.",
			invalid: "Please choose valid start and end dates. The end must not precede the start.",
			explain: "Calculation and data sources",
			netHint: "Net savings are avoided grid import costs minus grid charging costs and forgone feed-in remuneration. Later costs reduce the current result; additional costs appear as negative values.",
			calendarHint: "Calendar values come from the long-term Recorder statistics for net savings. After an upgrade, this history may start later than the displayed accounting start.",
			rangeHint: "Custom periods only include data since this Recorder history began. Choosing an earlier date does not invent values. If history is missing or the result entity is excluded from Recorder, the value and chart remain unknown or empty. A manual accounting restart within the selection may combine signed changes before and after the restart. The prior result does not alter these period values.",
			disabled: "The economics calculation is disabled. Configure it under Devices & services → SAX Power Home → Configure → Economics.",
			price_unavailable: "The electricity price is currently unavailable. Current period values may be incomplete.",
			origin_unavailable: "The origin of the charging energy cannot currently be determined.",
			partial_price_coverage: "A price was missing for some of today's energy. The result may be incomplete.",
			missing: "Economics data are currently unavailable."
		}), o = Z(() => n?.entity("binary_sensor", "economics_investment_configured")), s = Z(() => n?.entity("sensor", "economics_amortization_progress")), c = Z(() => n?.entity("sensor", "economics_remaining_to_payback")), l = Z(() => n?.entity("sensor", "economics_roi")), u = Z(() => n?.entity("sensor", "economics_net_savings")), d = Z(() => n?.entity("sensor", "economics_status")), f = Z(() => s.value?.available ? Q(s.value.state?.state) : null), p = Z(() => f.value === null ? null : Math.max(0, Math.min(100, f.value))), m = (e) => {
			let n = _o(e, t.hass);
			return n === null ? a.value.unavailable : `${n} €`;
		}, h = (e) => vo(e, t.hass) ?? a.value.unavailable, g = (e) => vo(`${e}T12:00:00Z`, t.hass, {
			dateStyle: "medium",
			timeZone: "UTC"
		}) ?? e, _ = Z(() => {
			let e = d.value?.available ? d.value.state?.state : void 0;
			return e === "active" || e === "storage_error" ? null : e === "disabled" || e === "price_unavailable" || e === "origin_unavailable" || e === "partial_price_coverage" ? a.value[e] : a.value.missing;
		}), v = xo(() => t.hass, () => t.entryId, () => u.value?.metadata.entity_id), y = /* @__PURE__ */ z(""), b = /* @__PURE__ */ z(""), x = null;
		V(v.data, (e) => {
			e && ((!y.value && !b.value || y.value === x?.start && b.value === x?.end) && (y.value = e.selected.start_date, b.value = e.selected.end_date), x = {
				start: e.selected.start_date,
				end: e.selected.end_date
			});
		}), V(() => t.entryId, () => {
			y.value = "", b.value = "", x = null;
		});
		let S = Z(() => v.error.value === "invalid" ? a.value.invalid : v.error.value === "failed" ? a.value.failed : v.error.value === "unavailable" || v.data.value?.status === "recorder_unavailable" ? a.value.noRecorder : null), C = [
			"day",
			"week",
			"month",
			"year"
		], w = Z(() => v.data.value?.selected.buckets ?? []), T = /* @__PURE__ */ z(null), E = /* @__PURE__ */ z(720);
		V(T, (e, t, n) => {
			if (!e) return;
			let r = (e) => {
				Number.isFinite(e) && e > 0 && (E.value = e);
			};
			if (r(e.getBoundingClientRect().width), typeof ResizeObserver > "u") return;
			let i = new ResizeObserver((e) => {
				for (let t of e) r(t.contentRect.width);
			});
			i.observe(e), n(() => i.disconnect());
		});
		let D = Z(() => {
			let e = w.value.map((e) => Q(e.change)), n = Math.max(0, ...e.map((e) => e ?? 0)), r = Math.min(0, ...e.map((e) => e ?? 0)), i = n - r || 1, a = (e) => 20 + (n - e) / i * 180, o = v.data.value?.selected, s = Date.parse(o?.start ?? ""), c = Date.parse(o?.end ?? ""), l = c - s, u = _o(n, t.hass) ?? "", d = _o(r, t.hass) ?? "", f = Math.max(56, Math.max(u.length, d.length) * 7.1 + 12), p = E.value - 24, m = Math.max(1, p - f), g = (e) => f + Math.max(0, Math.min(1, (Date.parse(e) - s) / l)) * m;
			return {
				zero: a(0),
				high: n,
				low: r,
				highLabel: u,
				lowLabel: d,
				left: f,
				right: p,
				start: o?.start ?? "",
				end: Number.isFinite(c) ? (/* @__PURE__ */ new Date(c - 1)).toISOString() : "",
				bars: w.value.map((t, n) => {
					let r = g(t.end) - g(t.start);
					return {
						...t,
						value: e[n],
						x: g(t.start) + Math.min(2, r / 8),
						y: e[n] === null ? a(0) : a(Math.max(0, e[n])),
						height: e[n] === null ? 0 : Math.abs(a(e[n]) - a(0)),
						width: Math.max(0, r - Math.min(4, r / 4)),
						label: h(t.start)
					};
				})
			};
		}), O = Z(() => w.value.some((e) => Q(e.change) !== null)), k = (e) => vo(e, t.hass, v.data.value?.selected.period === "hour" ? { timeStyle: "short" } : v.data.value?.selected.period === "month" ? {
			month: "short",
			year: "numeric"
		} : {
			day: "2-digit",
			month: "short"
		}) ?? e;
		return (t, i) => (W(), G("div", Em, [
			q("div", Dm, [o.value?.available && o.value.state?.state === "off" ? (W(), G("section", {
				key: 0,
				class: "savings-card savings-payback",
				"aria-labelledby": `${B(r)}-investment`
			}, [q("h2", { id: `${B(r)}-investment` }, F(a.value.payback), 9, km), q("p", null, F(a.value.investment), 1)], 8, Om)) : o.value?.available && o.value.state?.state === "on" && (s.value || c.value || l.value || u.value || d.value) ? (W(), G("section", {
				key: 1,
				class: "savings-card savings-payback",
				"aria-labelledby": `${B(r)}-payback`
			}, [
				q("h2", { id: `${B(r)}-payback` }, F(a.value.payback), 9, jm),
				s.value ? (W(), G("div", Mm, [
					q("h3", { id: `${B(r)}-progress` }, F(s.value.name), 9, Nm),
					q("p", Pm, F(f.value === null ? a.value.unavailable : `${B(_o)(f.value, e.hass)} %`), 1),
					q("div", {
						class: "savings-progress__track",
						role: p.value === null ? void 0 : "meter",
						"aria-labelledby": `${B(r)}-progress`,
						"aria-valuemin": p.value === null ? void 0 : 0,
						"aria-valuemax": p.value === null ? void 0 : 100,
						"aria-valuenow": p.value ?? void 0
					}, [p.value === null ? X("", !0) : (W(), G("span", {
						key: 0,
						style: se({ width: `${p.value}%` })
					}, null, 4))], 8, Fm)
				])) : X("", !0),
				c.value || l.value || u.value || d.value ? (W(), G("dl", Im, [
					c.value ? (W(), G("div", Lm, [q("dt", null, F(c.value.name), 1), q("dd", null, F(m(c.value.available ? c.value.state?.state : null)), 1)])) : X("", !0),
					l.value ? (W(), G("div", Rm, [q("dt", null, F(a.value.prior), 1), q("dd", null, F(m(l.value.available ? l.value.state?.attributes.prior_result_eur ?? l.value.state?.attributes.prior_result_eur_formatted : null)), 1)])) : X("", !0),
					u.value ? (W(), G("div", zm, [q("dt", null, F(a.value.net), 1), q("dd", null, F(m(u.value.available ? u.value.state?.state : null)), 1)])) : X("", !0),
					d.value ? (W(), G("div", Bm, [q("dt", null, F(a.value.started), 1), q("dd", null, F(h(d.value.available ? d.value.state?.attributes.economics_started_at : null)), 1)])) : X("", !0)
				])) : X("", !0)
			], 8, Am)) : X("", !0), u.value ? (W(), G("section", {
				key: 2,
				class: "savings-periods",
				"aria-label": a.value.periods
			}, [(W(), G(U, null, H(C, (e) => q("article", {
				key: e,
				class: "savings-card"
			}, [q("h2", null, F(a.value[e]), 1), q("p", Hm, F(B(v).loading.value ? "…" : m(B(v).data.value?.periods[e].change)), 1)])), 64))], 8, Vm)) : X("", !0)]),
			J(eu, {
				hass: e.hass,
				class: "savings-tariff"
			}, null, 8, ["hass"]),
			u.value ? (W(), G("section", {
				key: 0,
				class: "savings-card savings-range",
				"aria-labelledby": `${B(r)}-range`
			}, [
				q("h2", { id: `${B(r)}-range` }, F(a.value.range), 9, Wm),
				q("form", {
					class: "savings-dates",
					onSubmit: i[3] ||= io((e) => B(v).select(y.value, b.value), ["prevent"])
				}, [
					q("label", { for: `${B(r)}-from` }, [Y(F(a.value.from), 1), jn(q("input", {
						id: `${B(r)}-from`,
						"onUpdate:modelValue": i[0] ||= (e) => y.value = e,
						type: "date",
						required: "",
						max: b.value || void 0
					}, null, 8, Km), [[Xa, y.value]])], 8, Gm),
					q("label", { for: `${B(r)}-to` }, [Y(F(a.value.to), 1), jn(q("input", {
						id: `${B(r)}-to`,
						"onUpdate:modelValue": i[1] ||= (e) => b.value = e,
						type: "date",
						required: "",
						min: y.value || void 0
					}, null, 8, Jm), [[Xa, b.value]])], 8, qm),
					q("button", Ym, F(a.value.apply), 1),
					q("button", {
						type: "button",
						disabled: B(v).loading.value,
						onClick: i[2] ||= (...e) => B(v).refresh && B(v).refresh(...e)
					}, F(a.value.refresh), 9, Xm)
				], 32),
				B(v).loading.value ? (W(), G("p", Zm, F(a.value.loading), 1)) : S.value ? (W(), G("p", Qm, F(S.value), 1)) : B(v).data.value ? (W(), G(U, { key: 2 }, [
					q("p", $m, F(g(B(v).data.value.selected.start_date)) + " – " + F(g(B(v).data.value.selected.end_date)), 1),
					q("h3", null, F(a.value.selected), 1),
					q("p", eh, F(m(B(v).data.value.selected.change)), 1),
					q("h3", { id: `${B(r)}-chart` }, F(a.value.chart), 9, th),
					q("p", nh, F(a.value.chartHint), 1),
					O.value ? (W(), G(U, { key: 0 }, [(W(), G("svg", {
						ref_key: "chartElement",
						ref: T,
						class: "savings-chart",
						viewBox: `0 0 ${E.value} 240`,
						role: "img",
						"aria-labelledby": `${B(r)}-chart`,
						"aria-describedby": `${B(r)}-chart-description`
					}, [
						q("desc", { id: `${B(r)}-chart-description` }, F(a.value.net) + ": " + F(m(B(v).data.value.selected.change)) + ". " + F(a.value.table) + ". ", 9, ih),
						q("line", {
							x1: D.value.left - 2,
							x2: D.value.right + 2,
							y1: D.value.zero,
							y2: D.value.zero,
							class: "savings-chart__axis"
						}, null, 8, ah),
						q("text", {
							x: D.value.left - 8,
							y: "24",
							"text-anchor": "end"
						}, F(D.value.highLabel), 9, oh),
						q("text", {
							x: D.value.left - 8,
							y: "204",
							"text-anchor": "end"
						}, F(D.value.lowLabel), 9, sh),
						i[4] ||= q("text", {
							x: "10",
							y: "226"
						}, "EUR", -1),
						w.value.length ? (W(), G("text", {
							key: 0,
							x: D.value.left,
							y: "226"
						}, F(k(D.value.start)), 9, ch)) : X("", !0),
						w.value.length > 1 ? (W(), G("text", {
							key: 1,
							x: D.value.right,
							y: "226",
							"text-anchor": "end"
						}, F(k(D.value.end)), 9, lh)) : X("", !0),
						(W(!0), G(U, null, H(D.value.bars, (e, t) => (W(), G("rect", {
							key: t,
							x: e.x,
							y: e.y,
							width: e.width,
							height: e.height,
							class: P(["savings-chart__bar", { "savings-chart__bar--negative": (e.value ?? 0) < 0 }])
						}, [q("title", null, F(e.label) + ": " + F(m(e.value)), 1)], 10, uh))), 128))
					], 8, rh)), q("details", dh, [q("summary", null, F(a.value.table), 1), q("div", fh, [q("table", ph, [q("thead", null, [q("tr", null, [
						q("th", null, F(a.value.from), 1),
						q("th", null, F(a.value.to), 1),
						q("th", null, F(a.value.net), 1)
					])]), q("tbody", null, [(W(!0), G(U, null, H(D.value.bars, (e, t) => (W(), G("tr", { key: t }, [
						q("td", null, F(e.label), 1),
						q("td", null, F(h(e.end)), 1),
						q("td", null, F(m(e.value)), 1)
					]))), 128))])])])])], 64)) : X("", !0),
					!O.value || B(v).data.value.selected.change === null ? (W(), G("p", mh, F(B(v).data.value.selected.change === null ? a.value.noData : a.value.noChartData), 1)) : X("", !0)
				], 64)) : X("", !0)
			], 8, Um)) : X("", !0),
			q("details", hh, [
				q("summary", null, F(a.value.explain), 1),
				q("p", null, F(a.value.netHint), 1),
				q("p", null, F(a.value.calendarHint), 1),
				q("p", null, F(a.value.rangeHint), 1)
			]),
			_.value && B(n)?.ready.value ? (W(), G("p", gh, F(_.value), 1)) : X("", !0)
		]));
	}
}), [["styles", [".savings-view{gap:20px;min-width:0;margin-top:24px;display:grid}.savings-overview{display:contents}.savings-card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.savings-card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.savings-card h3{margin:20px 0 8px;font-size:16px;font-weight:500}.savings-card p{overflow-wrap:anywhere;line-height:1.6}.savings-card p:last-child{margin-bottom:0}.savings-large{font-variant-numeric:tabular-nums;margin:0 0 12px;font-size:28px;font-weight:500}.savings-progress__track{background:var(--divider-color,#e0e0e0);border-radius:8px;height:16px;overflow:hidden}.savings-progress__track span{background:var(--info-color,#039be5);height:100%;display:block}.savings-rows{margin:20px 0 0}.savings-rows>div{border-bottom:1px solid var(--divider-color,#e0e0e0);justify-content:space-between;gap:16px;padding:12px 0;line-height:1.5;display:flex}.savings-rows>div:last-child{border-bottom:0;padding-bottom:0}.savings-rows dd{text-align:right;font-variant-numeric:tabular-nums;margin:0}.savings-periods{grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:16px;display:grid}.savings-periods h2{font-size:16px}.savings-table-scroll{overflow-x:auto}.savings-table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%;line-height:1.5}.savings-table th,.savings-table td{text-align:left;border-bottom:1px solid var(--divider-color,#e0e0e0);padding:10px 8px}.savings-table th:last-child,.savings-table td:last-child{text-align:right}.savings-dates{flex-wrap:wrap;align-items:end;gap:16px;display:flex}.savings-dates label{flex:180px;gap:8px;min-width:0;display:grid}.savings-dates input,.savings-dates button{box-sizing:border-box;font:inherit;border:1px solid var(--divider-color,#bdbdbd);background:var(--ha-card-background,var(--card-background-color,#fff));min-height:44px;color:var(--primary-text-color,#212121);border-radius:6px;padding:10px 12px}.savings-dates input{--lightningcss-light:initial;--lightningcss-dark: ;color-scheme:light dark;width:100%}@media (prefers-color-scheme:dark){.savings-dates input{--lightningcss-light: ;--lightningcss-dark:initial}}.savings-dates button{cursor:pointer;color:var(--primary-color,#0288d1)}.savings-dates button:disabled{opacity:.6;cursor:default}.savings-dates :focus-visible,.savings-card summary:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:3px}.savings-selected-dates,.savings-empty{color:var(--secondary-text-color,#666)}.savings-chart{width:100%;height:auto;display:block;overflow:visible}.savings-chart text{fill:var(--secondary-text-color,#666);font-size:12px}.savings-chart__axis{stroke:var(--primary-text-color,#212121);stroke-width:1px}.savings-chart__bar{fill:var(--info-color,#039be5)}.savings-chart__bar--negative{fill:var(--error-color,#db4437)}.savings-card summary{cursor:pointer;min-height:24px;font-weight:500;line-height:1.6}.savings-chart-table{margin-top:16px}.savings-status{margin:0;line-height:1.6}@container sax-content (width>=860px){.savings-view{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;gap:16px;margin-top:16px}.savings-view>*{grid-column:1/-1}.savings-overview{gap:16px;min-width:0;display:grid}.savings-overview:empty{display:none}.savings-view:has(>.savings-overview>section):has(>.savings-tariff)>:is(.savings-overview,.savings-tariff){grid-column:auto}.savings-card{padding:18px}.savings-card h2{margin-bottom:12px;font-size:16px}.savings-card h3{margin-top:16px;font-size:14px}.savings-card p{margin-top:10px;line-height:1.5}.savings-progress h3{margin-top:0}.savings-card .savings-large{margin-top:0;margin-bottom:8px;font-size:24px}.savings-rows{margin-top:12px}.savings-rows>div{gap:12px;padding:8px 0}.savings-rows dt{min-width:0}.savings-rows dd{flex-shrink:0;max-width:58%}.savings-periods{grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.savings-view:has(>.savings-tariff) .savings-periods{grid-template-columns:repeat(2,minmax(0,1fr))}.savings-periods .savings-card{padding:14px 16px}.savings-periods h2{margin-bottom:6px;font-size:14px}.savings-periods .savings-large{margin-bottom:0;font-size:22px}.savings-table th,.savings-table td{padding:7px 8px}.savings-dates{gap:12px}.savings-dates label{flex:0 220px;gap:6px}.savings-range .savings-selected-dates{margin-bottom:8px}.savings-range .savings-chart-hint{margin-top:0;margin-bottom:8px}.savings-chart-table{margin-top:12px}}@media (max-width:600px){.savings-view{gap:16px}.savings-card{padding:20px}.savings-rows>div{flex-wrap:wrap;gap:4px 16px}.savings-rows dd{margin-left:auto}}"]]]), vh = ["lang"], yh = { class: "header" }, bh = ["aria-label"], xh = ["aria-label"], Sh = [
	"href",
	"aria-current",
	"onClick"
], Ch = {
	key: 0,
	class: "status",
	role: "alert"
}, wh = {
	key: 1,
	class: "introduction"
}, Th = {
	key: 0,
	class: "status",
	role: "status"
}, Eh = {
	key: 1,
	class: "status",
	role: "status"
}, Dh = {
	key: 6,
	class: "status"
}, Oh = ["href"], kh = /* @__PURE__ */ Ba(/* @__PURE__ */ ko(/* @__PURE__ */ Gn({
	__name: "Panel.ce",
	props: {
		hass: { type: Object },
		narrow: { type: Boolean },
		panel: { type: Object },
		route: { type: Object }
	},
	setup(e) {
		let t = e, n = Ua(), r = Do(() => t.hass, () => t.panel?.config?.entry_id);
		Nn(Co, r);
		let i = Z(() => t.hass?.language.toLowerCase().startsWith("de") ? "de" : "en"), a = Z(() => ho[i.value]), o = Z(() => !t.hass?.kioskMode && (t.narrow || t.hass?.dockedSidebar === "always_hidden")), s = Z(() => `/${t.panel?.url_path || "sax-power-vue"}`), c = /* @__PURE__ */ z(t.route?.path ?? window.location.pathname), l = po, u = Z(() => mo(c.value, s.value)), d = Z(() => ["dynamisches-laden", "ladeautomatik"].includes(u.value) ? "stromtarif" : u.value), f = Z(() => d.value === "tarifvergleich");
		V([() => r.ready.value, () => {
			let e = r.entity("sensor", "economics_current_import_price")?.state?.attributes ?? {};
			return JSON.stringify([
				e.tariff_type,
				e.base_price_eur_kwh,
				e.feed_in_price_eur_kwh,
				e.windows,
				e.price_sensor_entity_id
			]);
		}], ([e]) => {
			e && r.loadTariff().catch(() => {});
		}, { immediate: !0 });
		let p = Z(() => po.find((e) => e.path === d.value)), m = /* @__PURE__ */ z();
		V(() => t.route?.path, (e) => {
			e !== void 0 && (c.value = e);
		}), V([u, d], ([e, t]) => {
			if (e === t) return;
			let n = `${s.value}/${t}`;
			c.value = n, window.history.replaceState(null, "", n), window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: !0 } })), vn(() => m.value?.focus());
		}, { immediate: !0 });
		function h() {
			c.value = window.location.pathname;
		}
		or(() => {
			window.addEventListener("popstate", h), window.addEventListener("location-changed", h);
		}), cr(() => {
			window.removeEventListener("popstate", h), window.removeEventListener("location-changed", h);
		});
		function g(e, t) {
			e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || (e.preventDefault(), window.location.pathname !== t && (window.history.pushState(null, "", t), window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: !1 } }))), h(), vn(() => m.value?.focus()));
		}
		function _() {
			n?.dispatchEvent(new CustomEvent("hass-toggle-menu", {
				bubbles: !0,
				composed: !0
			}));
		}
		return (t, n) => (W(), G("div", {
			class: P(["dashboard", { narrow: e.narrow }]),
			lang: i.value
		}, [
			q("header", yh, [o.value ? (W(), G("button", {
				key: 0,
				class: "menu-button",
				type: "button",
				"aria-label": a.value.menu,
				onClick: _
			}, [...n[1] ||= [q("svg", {
				viewBox: "0 0 24 24",
				"aria-hidden": "true"
			}, [q("path", { d: "M4 6h16M4 12h16M4 18h16" })], -1)]], 8, bh)) : X("", !0), n[2] ||= q("div", { class: "brand" }, [q("svg", {
				class: "brand-icon",
				viewBox: "0 0 24 24",
				"aria-hidden": "true"
			}, [q("path", { d: "M9 3h6M8 5h8a1 1 0 0 1 1 1v14H7V6a1 1 0 0 1 1-1Z" }), q("path", { d: "m13 8-3 5h4l-3 5" })]), q("span", null, "SAX Power")], -1)]),
			q("nav", {
				class: "navigation",
				"aria-label": a.value.navigation
			}, [(W(!0), G(U, null, H(B(l), (e) => (W(), G("a", {
				key: e.path,
				href: `${s.value}/${e.path}`,
				"aria-current": d.value === e.path ? "page" : void 0,
				onClick: (t) => g(t, `${s.value}/${e.path}`)
			}, F(e[i.value]), 9, Sh))), 128))], 8, xh),
			q("main", null, [
				B(r).error.value && !f.value ? (W(), G("p", Ch, F(B(r).error.value), 1)) : X("", !0),
				d.value !== "stromtarif" && !f.value ? (W(), G("p", wh, F(a.value.introduction), 1)) : X("", !0),
				(W(), G("section", {
					key: e.panel?.config?.entry_id,
					class: P(["section", { "section--tariff": d.value === "stromtarif" }]),
					"aria-labelledby": "section-heading"
				}, [
					q("h1", {
						id: "section-heading",
						ref_key: "heading",
						ref: m,
						tabindex: "-1"
					}, F(p.value?.[i.value] ?? a.value.notFound), 513),
					(W(), K(er, null, [f.value ? (W(), K(Tm, {
						key: 0,
						language: i.value
					}, null, 8, ["language"])) : X("", !0)], 1024)),
					f.value ? X("", !0) : (W(), G(U, { key: 0 }, [e.hass ? e.panel?.config?.entry_id ? d.value === "allgemein" ? (W(), K(ys, { key: 2 })) : d.value === "netzdienliches-laden" ? (W(), K(Ac, {
						key: 3,
						hass: e.hass
					}, null, 8, ["hass"])) : d.value === "stromtarif" ? (W(), K(Zf, {
						key: 4,
						hass: e.hass
					}, null, 8, ["hass"])) : d.value === "ersparnis" ? (W(), K(_h, {
						key: 5,
						hass: e.hass,
						"entry-id": e.panel?.config?.entry_id
					}, null, 8, ["hass", "entry-id"])) : (W(), G("div", Dh, [q("p", null, F(a.value.notFoundDescription), 1), q("a", {
						href: `${s.value}/allgemein`,
						onClick: n[0] ||= (e) => g(e, `${s.value}/allgemein`)
					}, F(a.value.returnToOverview), 9, Oh)])) : (W(), G("p", Eh, F(a.value.missingEntry), 1)) : (W(), G("p", Th, F(a.value.loading), 1))], 64))
				], 2))
			])
		], 10, vh));
	}
}), [["styles", [":host{height:100%;color:var(--primary-text-color,#212121);background:var(--primary-background-color,#fafafa);font-family:var(--paper-font-body1_-_font-family,Roboto, sans-serif);font-size:14px;display:block}*{box-sizing:border-box}.dashboard{min-height:100%;container:sax-panel/inline-size}.header{background:var(--app-header-background-color,var(--primary-color,#03a9f4));min-height:64px;color:var(--app-header-text-color,#fff);align-items:center;gap:14px;padding:8px 24px;display:flex}.brand{align-items:center;gap:10px;font-size:20px;font-weight:500;display:flex}.header svg{fill:none;stroke:currentColor;stroke-width:1.7px;stroke-linecap:round;stroke-linejoin:round}.brand-icon{width:30px;height:30px}.menu-button{width:44px;height:44px;color:inherit;cursor:pointer;background:0 0;border:0;border-radius:50%;place-items:center;margin-left:-10px;display:grid}.menu-button svg{width:24px;height:24px}.navigation{border-bottom:1px solid var(--divider-color,#e0e0e0);background:var(--card-background-color,#fff);padding:0 16px;display:flex;overflow-x:auto}.navigation a{min-height:56px;color:var(--secondary-text-color,#666);white-space:nowrap;border-bottom:3px solid #0000;align-items:center;padding:12px 16px;text-decoration:none;display:flex}.navigation a[aria-current=page]{border-color:var(--primary-color,#03a9f4);color:var(--primary-text-color,#212121);font-weight:600}a{color:var(--primary-text-color,#212121);text-underline-offset:3px}a:focus-visible,button:focus-visible{outline-offset:-4px;outline:2px solid}main{max-width:1120px;margin:0 auto;padding:28px 24px 48px}.introduction{color:var(--secondary-text-color,#666);margin:0 0 24px;line-height:1.6}.section{overflow-wrap:anywhere;border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));box-shadow:var(--ha-card-box-shadow,none);padding:28px;container:sax-content/inline-size}.section.section--tariff{box-shadow:none;background:0 0;border:0;padding:0}h1{margin:0;font-size:24px;font-weight:500;line-height:1.35}h1:focus{outline:none}h2{margin:0 0 12px;font-size:18px;font-weight:500;line-height:1.5}.status{margin-top:24px;line-height:1.7}.narrow .header{padding-left:16px;padding-right:16px}.narrow main{padding:16px 12px 32px}@container sax-panel (width>=940px){.header{min-height:56px;padding:6px 20px}.navigation a{min-height:48px;padding:8px 14px}main{max-width:1360px;padding:16px 20px 20px}.introduction{margin-bottom:12px}.section{padding:20px}h1{font-size:22px}}@media (max-width:600px){.header{gap:8px;padding:8px 16px}.brand{gap:6px;font-size:18px}.brand-icon{display:none}.navigation{padding:0 4px}main{padding:16px 12px 32px}.introduction{margin-bottom:16px}.section{padding:20px}h1{font-size:22px}}"]]]));
customElements.get("sax-power-vue-panel") || customElements.define("sax-power-vue-panel", kh);
//#endregion
export { kh as SaxPowerVuePanel };
