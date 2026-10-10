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
}, l = Object.prototype.hasOwnProperty, u = (e, t) => l.call(e, t), d = Array.isArray, f = (e) => x(e) === "[object Map]", p = (e) => x(e) === "[object Set]", m = (e) => x(e) === "[object Date]", h = (e) => typeof e == "function", g = (e) => typeof e == "string", _ = (e) => typeof e == "symbol", v = (e) => typeof e == "object" && !!e, y = (e) => (v(e) || h(e)) && h(e.then) && h(e.catch), b = Object.prototype.toString, x = (e) => b.call(e), S = (e) => x(e).slice(8, -1), C = (e) => x(e) === "[object Object]", w = (e) => g(e) && e !== "NaN" && e[0] !== "-" && "" + parseInt(e, 10) === e, T = /* @__PURE__ */ e(",key,ref,ref_for,ref_key,onVnodeBeforeMount,onVnodeMounted,onVnodeBeforeUpdate,onVnodeUpdated,onVnodeBeforeUnmount,onVnodeUnmounted"), ee = (e) => {
	let t = /* @__PURE__ */ Object.create(null);
	return ((n) => t[n] || (t[n] = e(n)));
}, E = /-\w/g, D = ee((e) => e.replace(E, (e) => e.slice(1).toUpperCase())), te = /\B([A-Z])/g, O = ee((e) => e.replace(te, "-$1").toLowerCase()), ne = ee((e) => e.charAt(0).toUpperCase() + e.slice(1)), re = ee((e) => e ? `on${ne(e)}` : ""), k = (e, t) => !Object.is(e, t), ie = (e, ...t) => {
	for (let n = 0; n < e.length; n++) e[n](...t);
}, A = (e, t, n, r = !1) => {
	Object.defineProperty(e, t, {
		configurable: !0,
		enumerable: !1,
		writable: r,
		value: n
	});
}, j = (e) => {
	let t = parseFloat(e);
	return isNaN(t) ? e : t;
}, ae = (e) => {
	let t = g(e) ? Number(e) : NaN;
	return isNaN(t) ? e : t;
}, oe, se = () => oe ||= typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : typeof global < "u" ? global : {};
function M(e) {
	if (d(e)) {
		let t = {};
		for (let n = 0; n < e.length; n++) {
			let r = e[n], i = g(r) ? de(r) : M(r);
			if (i) for (let e in i) t[e] = i[e];
		}
		return t;
	}
	if (g(e) || v(e)) return e;
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
function N(e) {
	let t = "";
	if (g(e)) t = e;
	else if (d(e)) for (let n = 0; n < e.length; n++) {
		let r = N(e[n]);
		r && (t += r + " ");
	}
	else if (v(e)) for (let n in e) e[n] && (t += n + " ");
	return t.trim();
}
var fe = "itemscope,allowfullscreen,formnovalidate,ismap,nomodule,novalidate,readonly", pe = /* @__PURE__ */ e(fe);
fe + "";
function P(e) {
	return !!e || e === "";
}
function F(e, t) {
	if (e.length !== t.length) return !1;
	let n = !0;
	for (let r = 0; n && r < e.length; r++) n = he(e[r], t[r]);
	return n;
}
function me(e, t) {
	if (e.size !== t.size) return !1;
	let n = Array.from(t), r = new Uint8Array(n.length);
	for (let t of e) {
		let e = -1;
		for (let i = 0; i < n.length; i++) if (!r[i] && he(t, n[i])) {
			e = i;
			break;
		}
		if (e < 0) return !1;
		r[e] = 1;
	}
	return !0;
}
function he(e, t) {
	if (e === t) return !0;
	let n = m(e), r = m(t);
	if (n || r) return n && r ? e.getTime() === t.getTime() : !1;
	if (n = _(e), r = _(t), n || r) return e === t;
	if (n = d(e), r = d(t), n || r) return n && r ? F(e, t) : !1;
	if (n = v(e), r = v(t), n || r) {
		if (!n || !r) return !1;
		if (n = f(e), r = f(t), n || r || (n = p(e), r = p(t), n || r)) return n && r ? me(e, t) : !1;
		if (Object.keys(e).length !== Object.keys(t).length) return !1;
		for (let n in e) {
			let r = e.hasOwnProperty(n), i = t.hasOwnProperty(n);
			if (r && !i || !r && i || !he(e[n], t[n])) return !1;
		}
	}
	return String(e) === String(t);
}
function ge(e, t) {
	return e.findIndex((e) => he(e, t));
}
var _e = (e) => !!(e && e.__v_isRef === !0), I = (e) => g(e) ? e : e == null ? "" : d(e) || v(e) && (e.toString === b || !h(e.toString)) ? _e(e) ? I(e.value) : JSON.stringify(e, ve, 2) : String(e), ve = (e, t) => _e(t) ? ve(e, t.value) : f(t) ? { [`Map(${t.size})`]: [...t.entries()].reduce((e, [t, n], r) => (e[ye(t, r) + " =>"] = n, e), {}) } : p(t) ? { [`Set(${t.size})`]: [...t.values()].map((e) => ye(e)) } : _(t) ? ye(t) : v(t) && !d(t) && !C(t) ? String(t) : t, ye = (e, t = "") => _(e) ? `Symbol(${e.description ?? t})` : e, L, be = class {
	constructor(e = !1) {
		this.detached = e, this._active = !0, this._on = 0, this.effects = [], this.cleanups = [], this._isPaused = !1, this._warnOnRun = !0, this.__v_skip = !0, !e && L && (L.active ? (this.parent = L, this.index = (L.scopes || (L.scopes = [])).push(this) - 1) : (this._active = !1, this._warnOnRun = !1));
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
			let t = L;
			try {
				return L = this, e();
			} finally {
				L = t;
			}
		}
	}
	on() {
		++this._on === 1 && (this.prevScope = L, L = this);
	}
	off() {
		if (this._on > 0 && --this._on === 0) {
			if (L === this) L = this.prevScope;
			else {
				let e = L;
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
function xe() {
	return L;
}
function Se(e, t = !1) {
	L && L.cleanups.push(e);
}
var R, Ce = /* @__PURE__ */ new WeakSet(), we = class {
	constructor(e) {
		this.fn = e, this.deps = void 0, this.depsTail = void 0, this.flags = 5, this.next = void 0, this.cleanup = void 0, this.scheduler = void 0, L && (L.active ? L.effects.push(this) : this.flags &= -2);
	}
	pause() {
		this.flags |= 64;
	}
	resume() {
		this.flags & 64 && (this.flags &= -65, Ce.has(this) && (Ce.delete(this), this.trigger()));
	}
	notify() {
		this.flags & 2 && !(this.flags & 32) || this.flags & 8 || Oe(this);
	}
	run() {
		if (!(this.flags & 1)) return this.fn();
		this.flags |= 2, Ve(this), je(this);
		let e = R, t = Le;
		R = this, Le = !0;
		try {
			return this.fn();
		} finally {
			Me(this), R = e, Le = t, this.flags &= -3;
		}
	}
	stop() {
		if (this.flags & 1) {
			for (let e = this.deps; e; e = e.nextDep) Fe(e);
			this.deps = this.depsTail = void 0, Ve(this), this.onStop && this.onStop(), this.flags &= -2;
		}
	}
	trigger() {
		this.flags & 64 ? Ce.add(this) : this.scheduler ? this.scheduler() : this.runIfDirty();
	}
	runIfDirty() {
		Ne(this) && this.run();
	}
	get dirty() {
		return Ne(this);
	}
}, Te = 0, Ee, De;
function Oe(e, t = !1) {
	if (e.flags |= 8, t) {
		e.next = De, De = e;
		return;
	}
	e.next = Ee, Ee = e;
}
function ke() {
	Te++;
}
function Ae() {
	if (--Te > 0) return;
	if (De) {
		let e = De;
		for (De = void 0; e;) {
			let t = e.next;
			e.next = void 0, e.flags &= -9, e = t;
		}
	}
	let e;
	for (; Ee;) {
		let t = Ee;
		for (Ee = void 0; t;) {
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
function je(e) {
	for (let t = e.deps; t; t = t.nextDep) t.version = -1, t.prevActiveLink = t.dep.activeLink, t.dep.activeLink = t;
}
function Me(e) {
	let t, n = e.depsTail, r = n;
	for (; r;) {
		let e = r.prevDep;
		r.version === -1 ? (r === n && (n = e), Fe(r), Ie(r)) : t = r, r.dep.activeLink = r.prevActiveLink, r.prevActiveLink = void 0, r = e;
	}
	e.deps = t, e.depsTail = n;
}
function Ne(e) {
	for (let t = e.deps; t; t = t.nextDep) if (t.dep.version !== t.version || t.dep.computed && (Pe(t.dep.computed) || t.dep.version !== t.version)) return !0;
	return !!e._dirty;
}
function Pe(e) {
	if (e.flags & 4 && !(e.flags & 16) || (e.flags &= -17, e.globalVersion === He) || (e.globalVersion = He, !e.isSSR && e.flags & 128 && (!e.deps && !e._dirty || !Ne(e)))) return;
	e.flags |= 2;
	let t = e.dep, n = R, r = Le;
	R = e, Le = !0;
	try {
		je(e);
		let n = e.fn(e._value);
		(t.version === 0 || k(n, e._value)) && (e.flags |= 128, e._value = n, t.version++);
	} catch (e) {
		throw t.version++, e;
	} finally {
		R = n, Le = r, Me(e), e.flags &= -3;
	}
}
function Fe(e, t = !1) {
	let { dep: n, prevSub: r, nextSub: i } = e;
	if (r && (r.nextSub = i, e.prevSub = void 0), i && (i.prevSub = r, e.nextSub = void 0), n.subs === e && (n.subs = r, !r && n.computed)) {
		n.computed.flags &= -5;
		for (let e = n.computed.deps; e; e = e.nextDep) Fe(e, !0);
	}
	!t && !--n.sc && n.map && n.map.delete(n.key);
}
function Ie(e) {
	let { prevDep: t, nextDep: n } = e;
	t && (t.nextDep = n, e.prevDep = void 0), n && (n.prevDep = t, e.nextDep = void 0);
}
var Le = !0, Re = [];
function ze() {
	Re.push(Le), Le = !1;
}
function Be() {
	let e = Re.pop();
	Le = e === void 0 || e;
}
function Ve(e) {
	let { cleanup: t } = e;
	if (e.cleanup = void 0, t) {
		let e = R;
		R = void 0;
		try {
			t();
		} finally {
			R = e;
		}
	}
}
var He = 0, Ue = class {
	constructor(e, t) {
		this.sub = e, this.dep = t, this.version = t.version, this.nextDep = this.prevDep = this.nextSub = this.prevSub = this.prevActiveLink = void 0;
	}
}, We = class {
	constructor(e) {
		this.computed = e, this.version = 0, this.activeLink = void 0, this.subs = void 0, this.map = void 0, this.key = void 0, this.sc = 0, this.__v_skip = !0;
	}
	track(e) {
		if (!R || !Le || R === this.computed) return;
		let t = this.activeLink;
		if (t === void 0 || t.sub !== R) t = this.activeLink = new Ue(R, this), R.deps ? (t.prevDep = R.depsTail, R.depsTail.nextDep = t, R.depsTail = t) : R.deps = R.depsTail = t, Ge(t);
		else if (t.version === -1 && (t.version = this.version, t.nextDep)) {
			let e = t.nextDep;
			e.prevDep = t.prevDep, t.prevDep && (t.prevDep.nextDep = e), t.prevDep = R.depsTail, t.nextDep = void 0, R.depsTail.nextDep = t, R.depsTail = t, R.deps === t && (R.deps = e);
		}
		return t;
	}
	trigger(e) {
		this.version++, He++, this.notify(e);
	}
	notify(e) {
		ke();
		try {
			for (let e = this.subs; e; e = e.prevSub) e.sub.notify() && e.sub.dep.notify();
		} finally {
			Ae();
		}
	}
};
function Ge(e) {
	if (e.dep.sc++, e.sub.flags & 4) {
		let t = e.dep.computed;
		if (t && !e.dep.subs) {
			t.flags |= 20;
			for (let e = t.deps; e; e = e.nextDep) Ge(e);
		}
		let n = e.dep.subs;
		n !== e && (e.prevSub = n, n && (n.nextSub = e)), e.dep.subs = e;
	}
}
var Ke = /* @__PURE__ */ new WeakMap(), qe = /* @__PURE__ */ Symbol(""), Je = /* @__PURE__ */ Symbol(""), Ye = /* @__PURE__ */ Symbol("");
function Xe(e, t, n) {
	if (Le && R) {
		let t = Ke.get(e);
		t || Ke.set(e, t = /* @__PURE__ */ new Map());
		let r = t.get(n);
		r || (t.set(n, r = new We()), r.map = t, r.key = n), r.track();
	}
}
function Ze(e, t, n, r, i, a) {
	let o = Ke.get(e);
	if (!o) {
		He++;
		return;
	}
	let s = (e) => {
		e && e.trigger();
	};
	if (ke(), t === "clear") o.forEach(s);
	else {
		let i = d(e), a = i && w(n);
		if (i && n === "length") {
			let e = Number(r);
			o.forEach((t, n) => {
				(n === "length" || n === Ye || !_(n) && n >= e) && s(t);
			});
		} else switch ((n !== void 0 || o.has(void 0)) && s(o.get(n)), a && s(o.get(Ye)), t) {
			case "add":
				i ? a && s(o.get("length")) : (s(o.get(qe)), f(e) && s(o.get(Je)));
				break;
			case "delete":
				i || (s(o.get(qe)), f(e) && s(o.get(Je)));
				break;
			case "set": f(e) && s(o.get(qe));
		}
	}
	Ae();
}
function Qe(e) {
	let t = /* @__PURE__ */ z(e);
	return t === e ? t : (Xe(t, "iterate", Ye), /* @__PURE__ */ Lt(e) ? t : t.map(Bt));
}
function $e(e) {
	return Xe(e = /* @__PURE__ */ z(e), "iterate", Ye), e;
}
function et(e, t) {
	return /* @__PURE__ */ It(e) ? Vt(/* @__PURE__ */ Ft(e) ? Bt(t) : t) : Bt(t);
}
var tt = {
	__proto__: null,
	[Symbol.iterator]() {
		return nt(this, Symbol.iterator, (e) => et(this, e));
	},
	concat(...e) {
		return Qe(this).concat(...e.map((e) => d(e) ? Qe(e) : e));
	},
	entries() {
		return nt(this, "entries", (e) => (e[1] = et(this, e[1]), e));
	},
	every(e, t) {
		return it(this, "every", e, t, void 0, arguments);
	},
	filter(e, t) {
		return it(this, "filter", e, t, (e) => e.map((e) => et(this, e)), arguments);
	},
	find(e, t) {
		return it(this, "find", e, t, (e) => et(this, e), arguments);
	},
	findIndex(e, t) {
		return it(this, "findIndex", e, t, void 0, arguments);
	},
	findLast(e, t) {
		return it(this, "findLast", e, t, (e) => et(this, e), arguments);
	},
	findLastIndex(e, t) {
		return it(this, "findLastIndex", e, t, void 0, arguments);
	},
	forEach(e, t) {
		return it(this, "forEach", e, t, void 0, arguments);
	},
	includes(...e) {
		return ot(this, "includes", e);
	},
	indexOf(...e) {
		return ot(this, "indexOf", e);
	},
	join(e) {
		return Qe(this).join(e);
	},
	lastIndexOf(...e) {
		return ot(this, "lastIndexOf", e);
	},
	map(e, t) {
		return it(this, "map", e, t, void 0, arguments);
	},
	pop() {
		return st(this, "pop");
	},
	push(...e) {
		return st(this, "push", e);
	},
	reduce(e, ...t) {
		return at(this, "reduce", e, t);
	},
	reduceRight(e, ...t) {
		return at(this, "reduceRight", e, t);
	},
	shift() {
		return st(this, "shift");
	},
	some(e, t) {
		return it(this, "some", e, t, void 0, arguments);
	},
	splice(...e) {
		return st(this, "splice", e);
	},
	toReversed() {
		return Qe(this).toReversed();
	},
	toSorted(e) {
		return Qe(this).toSorted(e);
	},
	toSpliced(...e) {
		return Qe(this).toSpliced(...e);
	},
	unshift(...e) {
		return st(this, "unshift", e);
	},
	values() {
		return nt(this, "values", (e) => et(this, e));
	}
};
function nt(e, t, n) {
	let r = $e(e), i = r[t]();
	return r !== e && !/* @__PURE__ */ Lt(e) && (i._next = i.next, i.next = () => {
		let e = i._next();
		return e.done || (e.value = n(e.value)), e;
	}), i;
}
var rt = Array.prototype;
function it(e, t, n, r, i, a) {
	let o = $e(e), s = o !== e && !/* @__PURE__ */ Lt(e), c = o[t];
	if (c !== rt[t]) {
		let t = c.apply(e, a);
		return s ? Bt(t) : t;
	}
	let l = n;
	o !== e && (s ? l = function(t, r) {
		return n.call(this, et(e, t), r, e);
	} : n.length > 2 && (l = function(t, r) {
		return n.call(this, t, r, e);
	}));
	let u = c.call(o, l, r);
	return s && i ? i(u) : u;
}
function at(e, t, n, r) {
	let i = $e(e), a = i !== e && !/* @__PURE__ */ Lt(e), o = n, s = !1;
	i !== e && (a ? (s = r.length === 0, o = function(t, r, i) {
		return s && (s = !1, t = et(e, t)), n.call(this, t, et(e, r), i, e);
	}) : n.length > 3 && (o = function(t, r, i) {
		return n.call(this, t, r, i, e);
	}));
	let c = i[t](o, ...r);
	return s ? et(e, c) : c;
}
function ot(e, t, n) {
	let r = /* @__PURE__ */ z(e);
	Xe(r, "iterate", Ye);
	let i = r[t](...n);
	return (i === -1 || i === !1) && /* @__PURE__ */ Rt(n[0]) ? (n[0] = /* @__PURE__ */ z(n[0]), r[t](...n)) : i;
}
function st(e, t, n = []) {
	ze(), ke();
	let r = (/* @__PURE__ */ z(e))[t].apply(e, n);
	return Ae(), Be(), r;
}
var ct = /* @__PURE__ */ e("__proto__,__v_isRef,__isVue"), lt = new Set(/* @__PURE__ */ Object.getOwnPropertyNames(Symbol).filter((e) => e !== "arguments" && e !== "caller").map((e) => Symbol[e]).filter(_));
function ut(e) {
	_(e) || (e = String(e));
	let t = /* @__PURE__ */ z(this);
	return Xe(t, "has", e), t.hasOwnProperty(e);
}
var dt = class {
	constructor(e = !1, t = !1) {
		this._isReadonly = e, this._isShallow = t;
	}
	get(e, t, n) {
		if (t === "__v_skip") return e.__v_skip;
		let r = this._isReadonly, i = this._isShallow;
		if (t === "__v_isReactive") return !r;
		if (t === "__v_isReadonly") return r;
		if (t === "__v_isShallow") return i;
		if (t === "__v_raw") return n === (r ? i ? kt : Ot : i ? Dt : Et).get(e) || Object.getPrototypeOf(e) === Object.getPrototypeOf(n) ? e : void 0;
		let a = d(e);
		if (!r) {
			let e;
			if (a && (e = tt[t])) return e;
			if (t === "hasOwnProperty") return ut;
		}
		let o = Reflect.get(e, t, /* @__PURE__ */ Ht(e) ? e : n);
		if ((_(t) ? lt.has(t) : ct(t)) || (r || Xe(e, "get", t), i)) return o;
		if (/* @__PURE__ */ Ht(o)) {
			let e = a && w(t) ? o : o.value;
			return r && v(e) ? /* @__PURE__ */ Nt(e) : e;
		}
		return v(o) ? r ? /* @__PURE__ */ Nt(o) : /* @__PURE__ */ jt(o) : o;
	}
}, ft = class extends dt {
	constructor(e = !1) {
		super(!1, e);
	}
	set(e, t, n, r) {
		let i = e[t], a = d(e) && w(t);
		if (!this._isShallow) {
			let e = /* @__PURE__ */ It(i);
			if (!/* @__PURE__ */ Lt(n) && !/* @__PURE__ */ It(n) && (i = /* @__PURE__ */ z(i), n = /* @__PURE__ */ z(n)), !a && /* @__PURE__ */ Ht(i) && !/* @__PURE__ */ Ht(n)) return e || (i.value = n), !0;
		}
		let o = a ? Number(t) < e.length : u(e, t), s = Reflect.set(e, t, n, /* @__PURE__ */ Ht(e) ? e : r);
		return e === /* @__PURE__ */ z(r) && s && (o ? k(n, i) && Ze(e, "set", t, n, i) : Ze(e, "add", t, n)), s;
	}
	deleteProperty(e, t) {
		let n = u(e, t), r = e[t], i = Reflect.deleteProperty(e, t);
		return i && n && Ze(e, "delete", t, void 0, r), i;
	}
	has(e, t) {
		let n = Reflect.has(e, t);
		return (!_(t) || !lt.has(t)) && Xe(e, "has", t), n;
	}
	ownKeys(e) {
		return Xe(e, "iterate", d(e) ? "length" : qe), Reflect.ownKeys(e);
	}
}, pt = class extends dt {
	constructor(e = !1) {
		super(!0, e);
	}
	set(e, t) {
		return !0;
	}
	deleteProperty(e, t) {
		return !0;
	}
}, mt = /* @__PURE__ */ new ft(), ht = /* @__PURE__ */ new pt(), gt = /* @__PURE__ */ new ft(!0), _t = (e) => e, vt = (e) => Reflect.getPrototypeOf(e);
function yt(e, t, n) {
	return function(...r) {
		let i = this.__v_raw, a = /* @__PURE__ */ z(i), o = f(a), c = e === "entries" || e === Symbol.iterator && o, l = e === "keys" && o, u = i[e](...r), d = n ? _t : t ? Vt : Bt;
		return !t && Xe(a, "iterate", l ? Je : qe), s(Object.create(u), { next() {
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
function bt(e) {
	return function(...t) {
		return e === "delete" ? !1 : e === "clear" ? void 0 : this;
	};
}
function xt(e, t) {
	let n = {
		get(n) {
			let r = this.__v_raw, i = /* @__PURE__ */ z(r), a = /* @__PURE__ */ z(n);
			e || (k(n, a) && Xe(i, "get", n), Xe(i, "get", a));
			let { has: o } = vt(i), s = t ? _t : e ? Vt : Bt;
			if (o.call(i, n)) return s(r.get(n));
			if (o.call(i, a)) return s(r.get(a));
			r !== i && r.get(n);
		},
		get size() {
			let t = this.__v_raw;
			return !e && Xe(/* @__PURE__ */ z(t), "iterate", qe), t.size;
		},
		has(t) {
			let n = this.__v_raw, r = /* @__PURE__ */ z(n), i = /* @__PURE__ */ z(t);
			return e || (k(t, i) && Xe(r, "has", t), Xe(r, "has", i)), t === i ? n.has(t) : n.has(t) || n.has(i);
		},
		forEach(n, r) {
			let i = this, a = i.__v_raw, o = /* @__PURE__ */ z(a), s = t ? _t : e ? Vt : Bt;
			return !e && Xe(o, "iterate", qe), a.forEach((e, t) => n.call(r, s(e), s(t), i));
		}
	};
	return s(n, e ? {
		add: bt("add"),
		set: bt("set"),
		delete: bt("delete"),
		clear: bt("clear")
	} : {
		add(e) {
			let n = /* @__PURE__ */ z(this), r = vt(n), i = /* @__PURE__ */ z(e), a = !t && !/* @__PURE__ */ Lt(e) && !/* @__PURE__ */ It(e) ? i : e;
			return r.has.call(n, a) || k(e, a) && r.has.call(n, e) || k(i, a) && r.has.call(n, i) || (n.add(a), Ze(n, "add", a, a)), this;
		},
		set(e, n) {
			!t && !/* @__PURE__ */ Lt(n) && !/* @__PURE__ */ It(n) && (n = /* @__PURE__ */ z(n));
			let r = /* @__PURE__ */ z(this), { has: i, get: a } = vt(r), o = i.call(r, e);
			o ||= (e = /* @__PURE__ */ z(e), i.call(r, e));
			let s = a.call(r, e);
			return r.set(e, n), o ? k(n, s) && Ze(r, "set", e, n, s) : Ze(r, "add", e, n), this;
		},
		delete(e) {
			let t = /* @__PURE__ */ z(this), { has: n, get: r } = vt(t), i = n.call(t, e);
			i ||= (e = /* @__PURE__ */ z(e), n.call(t, e));
			let a = r ? r.call(t, e) : void 0, o = t.delete(e);
			return i && Ze(t, "delete", e, void 0, a), o;
		},
		clear() {
			let e = /* @__PURE__ */ z(this), t = e.size !== 0, n = e.clear();
			return t && Ze(e, "clear", void 0, void 0, void 0), n;
		}
	}), [
		"keys",
		"values",
		"entries",
		Symbol.iterator
	].forEach((r) => {
		n[r] = yt(r, e, t);
	}), n;
}
function St(e, t) {
	let n = xt(e, t);
	return (t, r, i) => r === "__v_isReactive" ? !e : r === "__v_isReadonly" ? e : r === "__v_raw" ? t : Reflect.get(u(n, r) && r in t ? n : t, r, i);
}
var Ct = { get: /* @__PURE__ */ St(!1, !1) }, wt = { get: /* @__PURE__ */ St(!1, !0) }, Tt = { get: /* @__PURE__ */ St(!0, !1) }, Et = /* @__PURE__ */ new WeakMap(), Dt = /* @__PURE__ */ new WeakMap(), Ot = /* @__PURE__ */ new WeakMap(), kt = /* @__PURE__ */ new WeakMap();
function At(e) {
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
function jt(e) {
	return /* @__PURE__ */ It(e) ? e : Pt(e, !1, mt, Ct, Et);
}
// @__NO_SIDE_EFFECTS__
function Mt(e) {
	return Pt(e, !1, gt, wt, Dt);
}
// @__NO_SIDE_EFFECTS__
function Nt(e) {
	return Pt(e, !0, ht, Tt, Ot);
}
function Pt(e, t, n, r, i) {
	if (!v(e) || e.__v_raw && !(t && e.__v_isReactive) || e.__v_skip || !Object.isExtensible(e)) return e;
	let a = i.get(e);
	if (a) return a;
	let o = At(S(e));
	if (o === 0) return e;
	let s = new Proxy(e, o === 2 ? r : n);
	return i.set(e, s), s;
}
// @__NO_SIDE_EFFECTS__
function Ft(e) {
	return /* @__PURE__ */ It(e) ? /* @__PURE__ */ Ft(e.__v_raw) : !!(e && e.__v_isReactive);
}
// @__NO_SIDE_EFFECTS__
function It(e) {
	return !!(e && e.__v_isReadonly);
}
// @__NO_SIDE_EFFECTS__
function Lt(e) {
	return !!(e && e.__v_isShallow);
}
// @__NO_SIDE_EFFECTS__
function Rt(e) {
	return e ? !!e.__v_raw : !1;
}
// @__NO_SIDE_EFFECTS__
function z(e) {
	let t = e && e.__v_raw;
	return t ? /* @__PURE__ */ z(t) : e;
}
function zt(e) {
	return !u(e, "__v_skip") && Object.isExtensible(e) && A(e, "__v_skip", !0), e;
}
var Bt = (e) => v(e) ? /* @__PURE__ */ jt(e) : e, Vt = (e) => v(e) ? /* @__PURE__ */ Nt(e) : e;
// @__NO_SIDE_EFFECTS__
function Ht(e) {
	return e ? e.__v_isRef === !0 : !1;
}
// @__NO_SIDE_EFFECTS__
function B(e) {
	return Wt(e, !1);
}
// @__NO_SIDE_EFFECTS__
function Ut(e) {
	return Wt(e, !0);
}
function Wt(e, t) {
	return /* @__PURE__ */ Ht(e) ? e : new Gt(e, t);
}
var Gt = class {
	constructor(e, t) {
		this.dep = new We(), this.__v_isRef = !0, this.__v_isShallow = !1, this._rawValue = t ? e : /* @__PURE__ */ z(e), this._value = t ? e : Bt(e), this.__v_isShallow = t;
	}
	get value() {
		return this.dep.track(), this._value;
	}
	set value(e) {
		let t = this._rawValue, n = this.__v_isShallow || /* @__PURE__ */ Lt(e) || /* @__PURE__ */ It(e);
		e = n ? e : /* @__PURE__ */ z(e), k(e, t) && (this._rawValue = e, this._value = n ? e : Bt(e), this.dep.trigger());
	}
};
function V(e) {
	return /* @__PURE__ */ Ht(e) ? e.value : e;
}
var Kt = {
	get: (e, t, n) => t === "__v_raw" ? e : V(Reflect.get(e, t, n)),
	set: (e, t, n, r) => {
		let i = e[t];
		return /* @__PURE__ */ Ht(i) && !/* @__PURE__ */ Ht(n) ? (i.value = n, !0) : Reflect.set(e, t, n, r);
	}
};
function qt(e) {
	return /* @__PURE__ */ Ft(e) ? e : new Proxy(e, Kt);
}
var Jt = class {
	constructor(e, t, n) {
		this.fn = e, this.setter = t, this._value = void 0, this.dep = new We(this), this.__v_isRef = !0, this.deps = void 0, this.depsTail = void 0, this.flags = 16, this.globalVersion = He - 1, this.next = void 0, this.effect = this, this.__v_isReadonly = !t, this.isSSR = n;
	}
	notify() {
		if (this.flags |= 16, !(this.flags & 8) && R !== this) return Oe(this, !0), !0;
	}
	get value() {
		let e = this.dep.track();
		return Pe(this), e && (e.version = this.dep.version), this._value;
	}
	set value(e) {
		this.setter && this.setter(e);
	}
};
// @__NO_SIDE_EFFECTS__
function Yt(e, t, n = !1) {
	let r, i;
	return h(e) ? r = e : (r = e.get, i = e.set), new Jt(r, i, n);
}
var Xt = {}, Zt = /* @__PURE__ */ new WeakMap(), Qt = void 0;
function $t(e, t = !1, n = Qt) {
	if (n) {
		let t = Zt.get(n);
		t || Zt.set(n, t = []), t.push(e);
	}
}
function en(e, n, i = t) {
	let { immediate: a, deep: o, once: s, scheduler: l, augmentJob: u, call: f } = i, p = (e) => o ? e : /* @__PURE__ */ Lt(e) || o === !1 || o === 0 ? tn(e, 1) : tn(e), m, g, _, v, y = !1, b = !1;
	if (/* @__PURE__ */ Ht(e) ? (g = () => e.value, y = /* @__PURE__ */ Lt(e)) : /* @__PURE__ */ Ft(e) ? (g = () => p(e), y = !0) : d(e) ? (b = !0, y = e.some((e) => /* @__PURE__ */ Ft(e) || /* @__PURE__ */ Lt(e)), g = () => e.map((e) => {
		if (/* @__PURE__ */ Ht(e)) return e.value;
		if (/* @__PURE__ */ Ft(e)) return p(e);
		if (h(e)) return f ? f(e, 2) : e();
	})) : g = h(e) ? n ? f ? () => f(e, 2) : e : () => {
		if (_) {
			ze();
			try {
				_();
			} finally {
				Be();
			}
		}
		let t = Qt;
		Qt = m;
		try {
			return f ? f(e, 3, [v]) : e(v);
		} finally {
			Qt = t;
		}
	} : r, n && o) {
		let e = g, t = o === !0 ? Infinity : o;
		g = () => tn(e(), t);
	}
	let x = xe(), S = () => {
		m.stop(), x && x.active && c(x.effects, m);
	};
	if (s && n) {
		let e = n;
		n = (...t) => {
			let n = e(...t);
			return S(), n;
		};
	}
	let C = b ? Array(e.length).fill(Xt) : Xt, w = (e) => {
		if (m.flags & 1 && (m.dirty || e)) {
			if (n) {
				let t = m.run();
				if (e || o || y || (b ? t.some((e, t) => k(e, C[t])) : k(t, C))) {
					_ && _();
					let e = Qt;
					Qt = m;
					try {
						let e = [
							t,
							C === Xt ? void 0 : b && C[0] === Xt ? [] : C,
							v
						];
						C = t, f ? f(n, 3, e) : n(...e);
					} finally {
						Qt = e;
					}
				}
			} else m.run();
		}
	};
	return u && u(w), m = new we(g), m.scheduler = l ? () => l(w, !1) : w, v = (e) => $t(e, !1, m), _ = m.onStop = () => {
		let e = Zt.get(m);
		if (e) {
			if (f) f(e, 4);
			else for (let t of e) t();
			Zt.delete(m);
		}
	}, n ? a ? w(!0) : C = m.run() : l ? l(w.bind(null, !0), !0) : m.run(), S.pause = m.pause.bind(m), S.resume = m.resume.bind(m), S.stop = S, S;
}
function tn(e, t = Infinity, n) {
	if (t <= 0 || !v(e) || e.__v_skip || (n ||= /* @__PURE__ */ new Map(), (n.get(e) || 0) >= t)) return e;
	if (n.set(e, t), t--, /* @__PURE__ */ Ht(e)) tn(e.value, t, n);
	else if (d(e)) for (let r = 0; r < e.length; r++) tn(e[r], t, n);
	else if (p(e) || f(e)) e.forEach((e) => {
		tn(e, t, n);
	});
	else if (C(e)) {
		for (let r in e) tn(e[r], t, n);
		for (let r of Object.getOwnPropertySymbols(e)) Object.prototype.propertyIsEnumerable.call(e, r) && tn(e[r], t, n);
	}
	return e;
}
//#endregion
//#region node_modules/@vue/runtime-core/dist/runtime-core.esm-bundler.js
function nn(e, t, n, r) {
	try {
		return r ? e(...r) : e();
	} catch (e) {
		an(e, t, n);
	}
}
function rn(e, t, n, r) {
	if (h(e)) {
		let i = nn(e, t, n, r);
		return i && y(i) && i.catch((e) => {
			an(e, t, n);
		}), i;
	}
	if (d(e)) {
		let i = [];
		for (let a = 0; a < e.length; a++) i.push(rn(e[a], t, n, r));
		return i;
	}
}
function an(e, n, r, i = !0) {
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
			ze(), nn(o, null, 10, [
				e,
				i,
				a
			]), Be();
			return;
		}
	}
	on(e, r, a, i, s);
}
function on(e, t, n, r = !0, i = !1) {
	if (i) throw e;
	console.error(e);
}
var sn = [], cn = -1, ln = [], un = null, dn = 0, fn = /* @__PURE__ */ Promise.resolve(), pn = null;
function mn(e) {
	let t = pn || fn;
	return e ? t.then(this ? e.bind(this) : e) : t;
}
function hn(e) {
	let t = cn + 1, n = sn.length;
	for (; t < n;) {
		let r = t + n >>> 1, i = sn[r], a = xn(i);
		a < e || a === e && i.flags & 2 ? t = r + 1 : n = r;
	}
	return t;
}
function gn(e) {
	if (!(e.flags & 1)) {
		let t = xn(e), n = sn[sn.length - 1];
		!n || !(e.flags & 2) && t >= xn(n) ? sn.push(e) : sn.splice(hn(t), 0, e), e.flags |= 1, _n();
	}
}
function _n() {
	pn ||= fn.then(Sn);
}
function vn(e) {
	if (!d(e)) un && e.id === -1 ? un.splice(dn + 1, 0, e) : e.flags & 1 || (ln.push(e), e.flags |= 1);
	else for (let t = 0; t < e.length; t++) ln.push(e[t]);
	_n();
}
function yn(e, t, n = cn + 1) {
	for (; n < sn.length; n++) {
		let t = sn[n];
		if (t && t.flags & 2) {
			if (e && t.id !== e.uid) continue;
			sn.splice(n, 1), n--, t.flags & 4 && (t.flags &= -2), t(), t.flags & 4 || (t.flags &= -2);
		}
	}
}
function bn(e) {
	if (ln.length) {
		let e = [...new Set(ln)].sort((e, t) => xn(e) - xn(t));
		if (ln.length = 0, un) {
			for (let t = 0; t < e.length; t++) un.push(e[t]);
			return;
		}
		for (un = e, dn = 0; dn < un.length; dn++) {
			let e = un[dn];
			e.flags & 4 && (e.flags &= -2), e.flags & 8 || e(), e.flags &= -2;
		}
		un = null, dn = 0;
	}
}
var xn = (e) => e.id == null ? e.flags & 2 ? -1 : Infinity : e.id;
function Sn(e) {
	try {
		for (cn = 0; cn < sn.length; cn++) {
			let e = sn[cn];
			e && !(e.flags & 8) && (e.flags & 4 && (e.flags &= -2), nn(e, e.i, e.i ? 15 : 14), e.flags & 4 || (e.flags &= -2));
		}
	} finally {
		for (; cn < sn.length; cn++) {
			let e = sn[cn];
			e && (e.flags &= -2);
		}
		cn = -1, sn.length = 0, bn(e), pn = null, (sn.length || ln.length) && Sn(e);
	}
}
var Cn = null, wn = null;
function Tn(e) {
	let t = Cn;
	return Cn = e, wn = e && e.type.__scopeId || null, t;
}
function En(e, t = Cn, n) {
	if (!t || e._n) return e;
	let r = (...n) => {
		r._d && ii(-1);
		let i = Tn(t), a = ei.length, o;
		try {
			o = e(...n);
		} finally {
			for (let e = ei.length; e > a; e--) ni();
			Tn(i), r._d && ii(1);
		}
		return o;
	};
	return r._n = !0, r._c = !0, r._d = !0, r;
}
function Dn(e, n) {
	if (Cn === null) return e;
	let r = Ii(Cn), i = e.dirs ||= [];
	for (let e = 0; e < n.length; e++) {
		let [a, o, s, c = t] = n[e];
		a && (h(a) && (a = {
			mounted: a,
			updated: a
		}), a.deep && tn(o), i.push({
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
function On(e, t, n, r) {
	let i = e.dirs, a = t && t.dirs;
	for (let o = 0; o < i.length; o++) {
		let s = i[o];
		a && (s.oldValue = a[o].value);
		let c = s.dir[r];
		c && (ze(), rn(c, n, 8, [
			e.el,
			s,
			e,
			t
		]), Be());
	}
}
function kn(e, t) {
	if (Si) {
		let n = Si.provides, r = Si.parent && Si.parent.provides;
		r === n && (n = Si.provides = Object.create(r)), n[e] = t;
	}
}
function An(e, t, n = !1) {
	let r = Ci();
	if (r || lr) {
		let i = lr ? lr._context.provides : r ? r.parent == null || r.ce ? r.vnode.appContext && r.vnode.appContext.provides : r.parent.provides : void 0;
		if (i && e in i) return i[e];
		if (arguments.length > 1) return n && h(t) ? t.call(r && r.proxy) : t;
	}
}
var jn = /* @__PURE__ */ Symbol.for("v-scx"), Mn = () => An(jn);
function H(e, t, n) {
	return Nn(e, t, n);
}
function Nn(e, n, i = t) {
	let { immediate: a, deep: o, flush: c, once: l } = i, u = s({}, i), d = n && a || !n && c !== "post", f;
	if (ki) {
		if (c === "sync") {
			let e = Mn();
			f = e.__watcherHandles ||= [];
		} else if (!d) {
			let e = () => {};
			return e.stop = r, e.resume = r, e.pause = r, e;
		}
	}
	let p = Si;
	u.call = (e, t, n) => rn(e, p, t, n);
	let m = !1;
	c === "post" ? u.scheduler = (e) => {
		Rr(e, p && p.suspense);
	} : c !== "sync" && (m = !0, u.scheduler = (e, t) => {
		t ? e() : gn(e);
	}), u.augmentJob = (e) => {
		n && (e.flags |= 4), m && (e.flags |= 2, p && (e.id = p.uid, e.i = p));
	};
	let h = en(e, n, u);
	return ki && (f ? f.push(h) : d && h()), h;
}
var Pn = /* @__PURE__ */ Symbol("_vte"), Fn = (e) => e.__isTeleport, In = /* @__PURE__ */ Symbol("_leaveCb");
function Ln(e) {
	let t = e[0];
	if (e.length > 1) {
		for (let n of e) if (n.type !== Qr) {
			t = n;
			break;
		}
	}
	return t;
}
function Rn(e) {
	if (!Jn(e)) return Fn(e.type) && e.children ? Ln(e.children) : e;
	if (e.component) return e.component.subTree;
	let { shapeFlag: t, children: n } = e;
	if (n) {
		if (t & 16) return n[0];
		if (t & 32 && h(n.default)) return n.default();
	}
}
function zn(e, t) {
	if (e.shapeFlag & 6 && e.component) {
		e.transition = t;
		let n = e.component.subTree;
		zn(Fn(n.type) && Rn(n) || n, t);
	} else e.shapeFlag & 128 ? (e.ssContent.transition = t.clone(e.ssContent), e.ssFallback.transition = t.clone(e.ssFallback)) : e.transition = t;
}
// @__NO_SIDE_EFFECTS__
function Bn(e, t) {
	return h(e) ? /* @__PURE__ */ s({ name: e.name }, t, { setup: e }) : e;
}
function Vn() {
	let e = Ci();
	return e ? (e.appContext.config.idPrefix || "v") + "-" + e.ids[0] + e.ids[1]++ : "";
}
function Hn(e) {
	e.ids = [
		e.ids[0] + e.ids[2]++ + "-",
		0,
		0
	];
}
function Un(e, t) {
	let n;
	return !!((n = Object.getOwnPropertyDescriptor(e, t)) && !n.configurable);
}
var Wn = /* @__PURE__ */ new WeakMap();
function Gn(e, n, r, a, o = !1) {
	if (d(e)) {
		e.forEach((e, t) => Gn(e, n && (d(n) ? n[t] : n), r, a, o));
		return;
	}
	if (qn(a) && !o) {
		a.shapeFlag & 512 && a.type.__asyncResolved && a.component.subTree.component && Gn(e, n, r, a.component.subTree);
		return;
	}
	let s = a.shapeFlag & 4 ? Ii(a.component) : a.el, l = o ? null : s, { i: f, r: p } = e, m = n && n.r, _ = f.refs === t ? f.refs = {} : f.refs, v = f.setupState, y = /* @__PURE__ */ z(v), b = v === t ? i : (e) => !Un(_, e) && u(y, e), x = (e, t) => !(t && Un(_, t));
	if (m != null && m !== p) {
		if (Kn(n), g(m)) _[m] = null, b(m) && (v[m] = null);
		else if (/* @__PURE__ */ Ht(m)) {
			let e = n;
			x(m, e.k) && (m.value = null), e.k && (_[e.k] = null);
		}
	}
	if (h(p)) nn(p, f, 12, [l, _]);
	else {
		let t = g(p), n = /* @__PURE__ */ Ht(p);
		if (t || n) {
			let i = () => {
				if (e.f) {
					let n = t ? b(p) ? v[p] : _[p] : x(p) || !e.k ? p.value : _[e.k];
					if (o) d(n) && c(n, s);
					else if (d(n)) n.includes(s) || n.push(s);
					else if (t) _[p] = [s], b(p) && (v[p] = _[p]);
					else {
						let t = [s];
						x(p, e.k) && (p.value = t), e.k && (_[e.k] = t);
					}
				} else t ? (_[p] = l, b(p) && (v[p] = l)) : n && (x(p, e.k) && (p.value = l), e.k && (_[e.k] = l));
			};
			if (l) {
				let t = () => {
					i(), Wn.delete(e);
				};
				t.id = -1, Wn.set(e, t), Rr(t, r);
			} else Kn(e), i();
		}
	}
}
function Kn(e) {
	let t = Wn.get(e);
	t && (t.flags |= 8, Wn.delete(e));
}
se().requestIdleCallback, se().cancelIdleCallback;
var qn = (e) => !!e.type.__asyncLoader, Jn = (e) => e.type.__isKeepAlive;
function Yn(e, t, n = Si, r = !1) {
	if (n) {
		let i = n[e] || (n[e] = []), a = t.__weh ||= (...r) => {
			ze();
			let i = Ei(n), a = rn(t, n, e, r);
			return i(), Be(), a;
		};
		return r ? i.unshift(a) : i.push(a), a;
	}
}
var Xn = (e) => (t, n = Si) => {
	(!ki || e === "sp") && Yn(e, (...e) => t(...e), n);
}, Zn = Xn("m"), Qn = Xn("bum"), $n = /* @__PURE__ */ Symbol.for("v-ndc");
function U(e, t, n, r) {
	let i, a = n && n[r], o = d(e);
	if (o || g(e)) {
		let n = o && /* @__PURE__ */ Ft(e), r = !1, s = !1;
		n && (r = !/* @__PURE__ */ Lt(e), s = /* @__PURE__ */ It(e), e = $e(e)), i = Array(e.length);
		for (let n = 0, o = e.length; n < o; n++) i[n] = t(r ? s ? Vt(Bt(e[n])) : Bt(e[n]) : e[n], n, void 0, a && a[n]);
	} else if (typeof e == "number") {
		i = Array(e);
		for (let n = 0; n < e; n++) i[n] = t(n + 1, n, void 0, a && a[n]);
	} else if (v(e)) {
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
function er(e, t, n, r, i, a) {
	if (n ??= {}, Cn.ce || Cn.parent && qn(Cn.parent) && Cn.parent.ce) {
		let e = a != null && n.key == null ? s({}, n, { key: a }) : n, i = Object.keys(e).length > 0;
		return t !== "default" && (e.name = t), G(), oi(W, null, [J("slot", e, r && r())], i ? -2 : 64);
	}
	let o = e[t];
	o && o._c && (o._d = !1);
	let c = ei.length;
	G();
	let l;
	try {
		let i = o && tr(o(n)), s = n.key || a || i && i.key;
		l = oi(W, { key: (s && !_(s) ? s : `_${t}`) + (!i && r ? "_fb" : "") }, i || (r ? r() : []), i && e._ === 1 ? 64 : -2);
	} catch (e) {
		for (let e = ei.length; e > c; e--) ni();
		throw e;
	} finally {
		o && o._c && (o._d = !0);
	}
	return !i && l.scopeId && (l.slotScopeIds = [l.scopeId + "-s"]), l;
}
function tr(e) {
	return e.some((e) => !si(e) || !(e.type === Qr || e.type === W && !tr(e.children))) ? e : null;
}
var nr = (e) => e ? Oi(e) ? Ii(e) : nr(e.parent) : null, rr = /* @__PURE__ */ s(/* @__PURE__ */ Object.create(null), {
	$: (e) => e,
	$el: (e) => e.vnode.el,
	$data: (e) => e.data,
	$props: (e) => e.props,
	$attrs: (e) => e.attrs,
	$slots: (e) => e.slots,
	$refs: (e) => e.refs,
	$parent: (e) => nr(e.parent),
	$root: (e) => nr(e.root),
	$host: (e) => e.ce,
	$emit: (e) => e.emit,
	$options: (e) => e.type,
	$forceUpdate: (e) => e.f ||= () => {
		gn(e.update);
	},
	$nextTick: (e) => e.n ||= mn.bind(e.proxy),
	$watch: (e) => r
}), ir = (e, n) => e !== t && !e.__isScriptSetup && u(e, n), ar = {
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
			else if (ir(i, n)) return s[n] = 1, i[n];
			else if (u(o, n)) return s[n] = 3, o[n];
			else if (r !== t && u(r, n)) return s[n] = 4, r[n];
			else s[n] = 0;
		}
		let d = rr[n], f, p;
		if (d) return n === "$attrs" && Xe(e.attrs, "get", ""), d(e);
		if ((f = c.__cssModules) && (f = f[n])) return f;
		if (r !== t && u(r, n)) return s[n] = 4, r[n];
		if (p = l.config.globalProperties, u(p, n)) return p[n];
	},
	set({ _: e }, t, n) {
		let { data: r, setupState: i, ctx: a } = e;
		return ir(i, t) ? (i[t] = n, !0) : u(e.props, t) || t[0] === "$" && t.slice(1) in e ? !1 : (a[t] = n, !0);
	},
	has({ _: { data: e, setupState: t, accessCache: n, ctx: r, appContext: i, props: a, type: o } }, s) {
		let c;
		return !!(n[s] || ir(t, s) || u(a, s) || u(r, s) || u(rr, s) || u(i.config.globalProperties, s) || (c = o.__cssModules) && c[s]);
	},
	defineProperty(e, t, n) {
		return n.get == null ? u(n, "value") && this.set(e, t, n.value, null) : e._.accessCache[t] = 0, Reflect.defineProperty(e, t, n);
	}
};
function or() {
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
var sr = 0;
function cr(e, t) {
	return function(n, r = null) {
		h(n) || (n = s({}, n)), r != null && !v(r) && (r = null);
		let i = or(), a = /* @__PURE__ */ new WeakSet(), o = [], c = !1, l = i.app = {
			_uid: sr++,
			_component: n,
			_props: r,
			_container: null,
			_context: i,
			_instance: null,
			version: Ri,
			get config() {
				return i.config;
			},
			set config(e) {},
			use(e, ...t) {
				return a.has(e) || (e && h(e.install) ? (a.add(e), e.install(l, ...t)) : h(e) && (a.add(e), e(l, ...t))), l;
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
					return u.appContext = i, s === !0 ? s = "svg" : s === !1 && (s = void 0), o && t ? t(u, a) : e(u, a, s), c = !0, l._container = a, a.__vue_app__ = l, Ii(u.component);
				}
			},
			onUnmount(e) {
				o.push(e);
			},
			unmount() {
				c && (rn(o, l._instance, 16), e(null, l._container), delete l._container.__vue_app__);
			},
			provide(e, t) {
				return i.provides[e] = t, l;
			},
			runWithContext(e) {
				let t = lr;
				lr = l;
				try {
					return e();
				} finally {
					lr = t;
				}
			}
		};
		return l;
	};
}
var lr = null, ur = (e, t) => t === "modelValue" || t === "model-value" ? e.modelModifiers : e[`${t}Modifiers`] || e[`${D(t)}Modifiers`] || e[`${O(t)}Modifiers`];
function dr(e, n, ...r) {
	if (e.isUnmounted) return;
	let i = e.vnode.props || t, a = r, o = n.startsWith("update:"), s = o && ur(i, n.slice(7));
	s && (s.trim && (a = r.map((e) => g(e) ? e.trim() : e)), s.number && (a = a.map(j)));
	let c, l = i[c = re(n)] || i[c = re(D(n))];
	!l && o && (l = i[c = re(O(n))]), l && rn(l, e, 6, a);
	let u = i[c + "Once"];
	if (u) {
		if (!e.emitted) e.emitted = {};
		else if (e.emitted[c]) return;
		e.emitted[c] = !0, rn(u, e, 6, a);
	}
}
function fr(e, t, n = !1) {
	let r = t.emitsCache, i = r.get(e);
	if (i !== void 0) return i;
	let a = e.emits, o = {};
	return a ? (d(a) ? a.forEach((e) => o[e] = null) : s(o, a), v(e) && r.set(e, o), o) : (v(e) && r.set(e, null), null);
}
function pr(e, t) {
	return !e || !a(t) ? !1 : (t = t.slice(2), t = t === "Once" ? t : t.replace(/Once$/, ""), u(e, t[0].toLowerCase() + t.slice(1)) || u(e, O(t)) || u(e, t));
}
function mr(e) {
	let { type: t, vnode: n, proxy: r, withProxy: i, propsOptions: [a], slots: s, attrs: c, emit: l, render: u, renderCache: d, props: f, data: p, setupState: m, ctx: h, inheritAttrs: g } = e, _ = Tn(e), v, y;
	try {
		if (n.shapeFlag & 4) {
			let e = i || r, t = e;
			v = mi(u.call(t, e, d, f, m, p, h)), y = c;
		} else {
			let e = t;
			v = mi(e.length > 1 ? e(f, {
				attrs: c,
				slots: s,
				emit: l
			}) : e(f, null)), y = t.props ? c : hr(c);
		}
	} catch (t) {
		ei.length = 0, an(t, e, 1), v = J(Qr);
	}
	let b = v;
	if (y && g !== !1) {
		let e = Object.keys(y), { shapeFlag: t } = b;
		e.length && t & 7 && (a && e.some(o) && (y = gr(y, a)), b = pi(b, y, !1, !0));
	}
	return n.dirs && (b = pi(b, null, !1, !0), b.dirs = b.dirs ? b.dirs.concat(n.dirs) : n.dirs), n.transition && zn(Fn(b.type) && Rn(b) || b, n.transition), v = b, Tn(_), v;
}
var hr = (e) => {
	let t;
	for (let n in e) (n === "class" || n === "style" || a(n)) && ((t ||= {})[n] = e[n]);
	return t;
}, gr = (e, t) => {
	let n = {};
	for (let r in e) (!o(r) || !(r.slice(9) in t)) && (n[r] = e[r]);
	return n;
};
function _r(e, t, n) {
	let { props: r, children: i, component: a } = e, { props: o, children: s, patchFlag: c } = t, l = a.emitsOptions;
	if (t.dirs || t.transition) return !0;
	if (n && c >= 0) {
		if (c & 1024) return !0;
		if (c & 16) return r ? vr(r, o, l) : !!o;
		if (c & 8) {
			let e = t.dynamicProps;
			for (let t = 0; t < e.length; t++) {
				let n = e[t];
				if (yr(o, r, n) && !pr(l, n)) return !0;
			}
		}
	} else return (i || s) && (!s || !s.$stable) ? !0 : r === o ? !1 : r ? !o || vr(r, o, l) : !!o;
	return !1;
}
function vr(e, t, n) {
	let r = Object.keys(t);
	if (r.length !== Object.keys(e).length) return !0;
	for (let i = 0; i < r.length; i++) {
		let a = r[i];
		if (yr(t, e, a) && !pr(n, a)) return !0;
	}
	return !1;
}
function yr(e, t, n) {
	let r = e[n], i = t[n];
	return n === "style" && v(r) && v(i) ? !he(r, i) : r !== i;
}
function br({ vnode: e, parent: t, suspense: n }, r) {
	for (; t;) {
		let n = t.subTree;
		if (n.suspense && n.suspense.activeBranch === e && (n.suspense.vnode.el = n.el = r, e = n), n === e) (e = t.vnode).el = r, t = t.parent;
		else break;
	}
	n && n.activeBranch === e && (n.vnode.el = r);
}
var xr = {}, Sr = () => Object.create(xr), Cr = (e) => Object.getPrototypeOf(e) === xr;
function wr(e, t, n, r = !1) {
	let i = {}, a = Sr();
	e.propsDefaults = /* @__PURE__ */ Object.create(null), Er(e, t, i, a);
	for (let t in e.propsOptions[0]) t in i || (i[t] = void 0);
	e.props = n ? r ? i : /* @__PURE__ */ Mt(i) : e.type.props ? i : a, e.attrs = a;
}
function Tr(e, t, n, r) {
	let { props: i, attrs: a, vnode: { patchFlag: o } } = e, s = /* @__PURE__ */ z(i), [c] = e.propsOptions, l = !1;
	if ((r || o > 0) && !(o & 16)) {
		if (o & 8) {
			let n = e.vnode.dynamicProps;
			for (let r = 0; r < n.length; r++) {
				let o = n[r];
				if (pr(e.emitsOptions, o)) continue;
				let d = t[o];
				if (c) {
					if (u(a, o)) d !== a[o] && (a[o] = d, l = !0);
					else {
						let t = D(o);
						i[t] = Dr(c, s, t, d, e, !1);
					}
				} else d !== a[o] && (a[o] = d, l = !0);
			}
		}
	} else {
		Er(e, t, i, a) && (l = !0);
		let r;
		for (let a in s) (!t || !u(t, a) && ((r = O(a)) === a || !u(t, r))) && (c ? n && (n[a] !== void 0 || n[r] !== void 0) && (i[a] = Dr(c, s, a, void 0, e, !0)) : delete i[a]);
		if (a !== s) for (let e in a) (!t || !u(t, e)) && (delete a[e], l = !0);
	}
	l && Ze(e.attrs, "set", "");
}
function Er(e, n, r, i) {
	let [a, o] = e.propsOptions, s = !1, c;
	if (n) for (let t in n) {
		if (T(t)) continue;
		let l = n[t], d;
		a && u(a, d = D(t)) ? !o || !o.includes(d) ? r[d] = l : (c ||= {})[d] = l : pr(e.emitsOptions, t) || (!(t in i) || l !== i[t]) && (i[t] = l, s = !0);
	}
	if (o) {
		let n = /* @__PURE__ */ z(r), i = c || t;
		for (let t = 0; t < o.length; t++) {
			let s = o[t];
			r[s] = Dr(a, n, s, i[s], e, !u(i, s));
		}
	}
	return s;
}
function Dr(e, t, n, r, i, a) {
	let o = e[n];
	if (o != null) {
		let e = u(o, "default");
		if (e && r === void 0) {
			let e = o.default;
			if (o.type !== Function && !o.skipFactory && h(e)) {
				let { propsDefaults: a } = i;
				if (n in a) r = a[n];
				else {
					let o = Ei(i);
					r = a[n] = e.call(null, t), o();
				}
			} else r = e;
			i.ce && i.ce._setProp(n, r);
		}
		o[0] && (a && !e ? r = !1 : o[1] && (r === "" || r === O(n)) && (r = !0));
	}
	return r;
}
function Or(e, r, i = !1) {
	let a = r.propsCache, o = a.get(e);
	if (o) return o;
	let c = e.props, l = {}, f = [];
	if (!c) return v(e) && a.set(e, n), n;
	if (d(c)) for (let e = 0; e < c.length; e++) {
		let n = D(c[e]);
		kr(n) && (l[n] = t);
	}
	else if (c) for (let e in c) {
		let t = D(e);
		if (kr(t)) {
			let n = c[e], r = l[t] = d(n) || h(n) ? { type: n } : s({}, n), i = r.type, a = !1, o = !0;
			if (d(i)) for (let e = 0; e < i.length; ++e) {
				let t = i[e], n = h(t) && t.name;
				if (n === "Boolean") {
					a = !0;
					break;
				}
				n === "String" && (o = !1);
			}
			else a = h(i) && i.name === "Boolean";
			r[0] = a, r[1] = o, (a || u(r, "default")) && f.push(t);
		}
	}
	let p = [l, f];
	return v(e) && a.set(e, p), p;
}
function kr(e) {
	return e[0] !== "$" && !T(e);
}
var Ar = (e) => e === "_" || e === "_ctx" || e === "$stable", jr = (e) => d(e) ? e.map(mi) : [mi(e)], Mr = (e, t, n) => {
	if (t._n) return t;
	let r = En((...e) => jr(t(...e)), n);
	return r._c = !1, r;
}, Nr = (e, t, n) => {
	let r = e._ctx;
	for (let n in e) {
		if (Ar(n)) continue;
		let i = e[n];
		if (h(i)) t[n] = Mr(n, i, r);
		else if (i != null) {
			let e = jr(i);
			t[n] = () => e;
		}
	}
}, Pr = (e, t) => {
	let n = jr(t);
	e.slots.default = () => n;
}, Fr = (e, t, n) => {
	for (let r in t) (n || !Ar(r)) && (e[r] = t[r]);
}, Ir = (e, t, n) => {
	let r = e.slots = Sr();
	if (e.vnode.shapeFlag & 32) {
		let e = t._;
		e ? (Fr(r, t, n), n && A(r, "_", e, !0)) : Nr(t, r);
	} else t && Pr(e, t);
}, Lr = (e, n, r) => {
	let { vnode: i, slots: a } = e, o = !0, s = t;
	if (i.shapeFlag & 32) {
		let e = n._;
		e ? r && e === 1 ? o = !1 : Fr(a, n, r) : (o = !n.$stable, Nr(n, a)), s = n;
	} else n && (Pr(e, n), s = { default: 1 });
	if (o) for (let e in a) !Ar(e) && s[e] == null && delete a[e];
}, Rr = Xr;
function zr(e) {
	return Br(e);
}
function Br(e, i) {
	let a = se();
	a.__VUE__ = !0;
	let { insert: o, remove: s, patchProp: c, createElement: l, createText: u, createComment: d, setText: f, setElementText: p, parentNode: m, nextSibling: h, setScopeId: g = r, insertStaticContent: _ } = e, v = (e, t, n, r = null, i = null, a = null, o = void 0, s = null, c = !!t.dynamicChildren) => {
		if (e === t) return;
		e && !ci(e, t) && (r = F(e), de(e, i, a, !0), e = null), t.patchFlag === -2 && (c = !1, t.dynamicChildren = null);
		let { type: l, ref: u, shapeFlag: d } = t;
		switch (l) {
			case Zr:
				y(e, t, n, r);
				break;
			case Qr:
				b(e, t, n, r);
				break;
			case $r:
				e ?? x(t, n, r, o);
				break;
			case W:
				re(e, t, n, r, i, a, o, s, c);
				break;
			default: d & 1 ? w(e, t, n, r, i, a, o, s, c) : d & 6 ? k(e, t, n, r, i, a, o, s, c) : (d & 64 || d & 128) && l.process(e, t, n, r, i, a, o, s, c, ge);
		}
		u != null && i ? Gn(u, e && e.ref, a, t || e, !t) : u == null && e && e.ref != null && Gn(e.ref, null, a, e, !0);
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
		if (t.type === "svg" ? o = "svg" : t.type === "math" && (o = "mathml"), e == null) ee(t, n, r, i, a, o, s, c);
		else {
			let n = e.el && e.el._isVueCE ? e.el : null;
			try {
				n && n._beginPatch(), te(e, t, i, a, o, s, c);
			} finally {
				n && n._endPatch();
			}
		}
	}, ee = (e, t, n, r, i, a, s, u) => {
		let d, f, { props: m, shapeFlag: h, transition: g, dirs: _ } = e;
		if (d = e.el = l(e.type, a, m && m.is, m), h & 8 ? p(d, e.children) : h & 16 && D(e.children, d, null, r, i, Vr(e, a), s, u), _ && On(e, null, r, "created"), E(d, e, e.scopeId, s, r), m) {
			for (let e in m) e !== "value" && !T(e) && c(d, e, null, m[e], a, r);
			"value" in m && c(d, "value", null, m.value, a), (f = m.onVnodeBeforeMount) && vi(f, r, e);
		}
		_ && On(e, null, r, "beforeMount");
		let v = Ur(i, g);
		v && g.beforeEnter(d), o(d, t, n), ((f = m && m.onVnodeMounted) || v || _) && Rr(() => {
			try {
				f && vi(f, r, e), v && g.enter(d), _ && On(e, null, r, "mounted");
			} finally {}
		}, i);
	}, E = (e, t, n, r, i) => {
		if (n && g(e, n), r) for (let t = 0; t < r.length; t++) g(e, r[t]);
		if (i) {
			let n = i.subTree;
			if (t === n || Yr(n.type) && (n.ssContent === t || n.ssFallback === t)) {
				let t = i.vnode;
				E(e, t, t.scopeId, t.slotScopeIds, i.parent);
			}
		}
	}, D = (e, t, n, r, i, a, o, s, c = 0) => {
		for (let l = c; l < e.length; l++) {
			let c = e[l] = s ? hi(e[l]) : mi(e[l]);
			v(null, c, t, n, r, i, a, o, s);
		}
	}, te = (e, n, r, i, a, o, s) => {
		let l = n.el = e.el, { patchFlag: u, dynamicChildren: d, dirs: f } = n;
		u |= e.patchFlag & 16;
		let m = e.props || t, h = n.props || t, g;
		if (r && Hr(r, !1), (g = h.onVnodeBeforeUpdate) && vi(g, r, n, e), f && On(n, e, r, "beforeUpdate"), r && Hr(r, !0), d && (!e.dynamicChildren || e.dynamicChildren.length !== d.length) && (u = 0, s = !1, d = null), (m.innerHTML && h.innerHTML == null || m.textContent && h.textContent == null) && p(l, ""), d ? O(e.dynamicChildren, d, l, r, i, Vr(n, a), o) : s || M(e, n, l, null, r, i, Vr(n, a), o, !1), u > 0) {
			if (u & 16) ne(l, m, h, r, a);
			else if (u & 2 && m.class !== h.class && c(l, "class", null, h.class, a), u & 4 && c(l, "style", m.style, h.style, a), u & 8) {
				let e = n.dynamicProps;
				for (let t = 0; t < e.length; t++) {
					let n = e[t], i = m[n], o = h[n];
					(o !== i || n === "value") && c(l, n, i, o, a, r);
				}
			}
			u & 1 && e.children !== n.children && p(l, n.children);
		} else !s && d == null && ne(l, m, h, r, a);
		((g = h.onVnodeUpdated) || f) && Rr(() => {
			g && vi(g, r, n, e), f && On(n, e, r, "updated");
		}, i);
	}, O = (e, t, n, r, i, a, o) => {
		for (let s = 0; s < t.length; s++) {
			let c = e[s], l = t[s], u = c.el && (c.type === W || !ci(c, l) || c.shapeFlag & 198) ? m(c.el) : n;
			v(c, l, u, null, r, i, a, o, !0);
		}
	}, ne = (e, n, r, i, a) => {
		if (n !== r) {
			if (n !== t) for (let t in n) !T(t) && !(t in r) && c(e, t, n[t], null, a, i);
			for (let t in r) {
				if (T(t)) continue;
				let o = r[t], s = n[t];
				o !== s && t !== "value" && c(e, t, s, o, a, i);
			}
			"value" in r && c(e, "value", n.value, r.value, a);
		}
	}, re = (e, t, n, r, i, a, s, c, l) => {
		let d = t.el = e ? e.el : u(""), f = t.anchor = e ? e.anchor : u(""), { patchFlag: p, dynamicChildren: m, slotScopeIds: h } = t;
		h && (c = c ? c.concat(h) : h), e == null ? (o(d, n, r), o(f, n, r), D(t.children || [], n, f, i, a, s, c, l)) : p > 0 && p & 64 && m && e.dynamicChildren && e.dynamicChildren.length === m.length ? (O(e.dynamicChildren, m, n, i, a, s, c), (t.key != null || i && t === i.subTree) && Wr(e, t, !0)) : M(e, t, n, f, i, a, s, c, l);
	}, k = (e, t, n, r, i, a, o, s, c) => {
		t.slotScopeIds = s, e == null ? t.shapeFlag & 512 ? i.ctx.activate(t, n, r, o, c) : A(t, n, r, i, a, o, c) : j(e, t, c);
	}, A = (e, t, n, r, i, a, o) => {
		let s = e.component = xi(e, r, i);
		if (Jn(e) && (s.ctx.renderer = ge), Ai(s, !1, o), s.asyncDep) {
			if (i && i.registerDep(s, ae, o), !e.el) {
				let r = s.subTree = J(Qr);
				b(null, r, t, n), e.placeholder = r.el;
			}
		} else ae(s, e, t, n, i, a, o);
	}, j = (e, t, n) => {
		let r = t.component = e.component;
		if (_r(e, t, n)) {
			if (r.asyncDep && !r.asyncResolved) {
				oe(r, t, n);
				return;
			}
			r.next = t, r.update();
		} else t.el = e.el, r.vnode = t;
	}, ae = (e, t, n, r, i, a, o) => {
		let s = () => {
			if (e.isMounted) {
				let { next: t, bu: n, u: r, parent: s, vnode: c } = e;
				{
					let n = Kr(e);
					if (n) {
						t && (t.el = c.el, oe(e, t, o)), n.asyncDep.then(() => {
							Rr(() => {
								e.isUnmounted || l();
							}, i);
						});
						return;
					}
				}
				let u = t, d;
				Hr(e, !1), t ? (t.el = c.el, oe(e, t, o)) : t = c, n && ie(n), (d = t.props && t.props.onVnodeBeforeUpdate) && vi(d, s, t, c), Hr(e, !0);
				let f = mr(e), p = e.subTree;
				e.subTree = f, v(p, f, m(p.el), F(p), e, i, a), t.el = f.el, u === null && br(e, f.el), r && Rr(r, i), (d = t.props && t.props.onVnodeUpdated) && Rr(() => vi(d, s, t, c), i);
			} else {
				let o, { el: s, props: c } = t, { bm: l, m: u, parent: d, root: f, type: p } = e, m = qn(t);
				if (Hr(e, !1), l && ie(l), !m && (o = c && c.onVnodeBeforeMount) && vi(o, d, t), Hr(e, !0), s && I) {
					let t = () => {
						e.subTree = mr(e), I(s, e.subTree, e, i, null);
					};
					m && p.__asyncHydrate ? p.__asyncHydrate(s, e, t) : t();
				} else {
					f.ce && f.ce._hasShadowRoot() && f.ce._injectChildStyle(p, e.parent ? e.parent.type : void 0);
					let o = e.subTree = mr(e);
					v(null, o, n, r, e, i, a), t.el = o.el;
				}
				if (u && Rr(u, i), !m && (o = c && c.onVnodeMounted)) {
					let e = t;
					Rr(() => vi(o, d, e), i);
				}
				(t.shapeFlag & 256 || d && qn(d.vnode) && d.vnode.shapeFlag & 256) && e.a && Rr(e.a, i), e.isMounted = !0, t = n = r = null;
			}
		};
		e.scope.on();
		let c = e.effect = new we(s);
		e.scope.off();
		let l = e.update = c.run.bind(c), u = e.job = c.runIfDirty.bind(c);
		u.i = e, u.id = e.uid, c.scheduler = () => gn(u), Hr(e, !0), l();
	}, oe = (e, t, n) => {
		t.component = e;
		let r = e.vnode.props;
		e.vnode = t, e.next = null, Tr(e, t.props, r, n), Lr(e, t.children, n), ze(), yn(e), Be();
	}, M = (e, t, n, r, i, a, o, s, c = !1) => {
		let l = e && e.children, u = e ? e.shapeFlag : 0, d = t.children, { patchFlag: f, shapeFlag: m } = t;
		if (f > 0) {
			if (f & 128) {
				le(l, d, n, r, i, a, o, s, c);
				return;
			}
			if (f & 256) {
				ce(l, d, n, r, i, a, o, s, c);
				return;
			}
		}
		m & 8 ? (u & 16 && P(l, i, a), d !== l && p(n, d)) : u & 16 ? m & 16 ? le(l, d, n, r, i, a, o, s, c) : P(l, i, a, !0) : (u & 8 && p(n, ""), m & 16 && D(d, n, r, i, a, o, s, c));
	}, ce = (e, t, r, i, a, o, s, c, l) => {
		e ||= n, t ||= n;
		let u = e.length, d = t.length, f = Math.min(u, d), p = 0;
		for (; p < f; p++) {
			let n = t[p] = l ? hi(t[p]) : mi(t[p]);
			v(e[p], n, r, null, a, o, s, c, l);
		}
		u > d ? P(e, a, o, !0, !1, f) : D(t, r, i, a, o, s, c, l, f);
	}, le = (e, t, r, i, a, o, s, c, l) => {
		let u = 0, d = t.length, f = e.length - 1, p = d - 1;
		for (; u <= f && u <= p;) {
			let n = e[u], i = t[u] = l ? hi(t[u]) : mi(t[u]);
			if (ci(n, i)) v(n, i, r, null, a, o, s, c, l);
			else break;
			u++;
		}
		for (; u <= f && u <= p;) {
			let n = e[f], i = t[p] = l ? hi(t[p]) : mi(t[p]);
			if (ci(n, i)) v(n, i, r, null, a, o, s, c, l);
			else break;
			f--, p--;
		}
		if (u > f) {
			if (u <= p) {
				let e = p + 1, n = e < d ? t[e].el : i;
				for (; u <= p;) v(null, t[u] = l ? hi(t[u]) : mi(t[u]), r, n, a, o, s, c, l), u++;
			}
		} else if (u > p) for (; u <= f;) de(e[u], a, o, !0), u++;
		else {
			let m = u, h = u, g = /* @__PURE__ */ new Map();
			for (u = h; u <= p; u++) {
				let e = t[u] = l ? hi(t[u]) : mi(t[u]);
				e.key != null && g.set(e.key, u);
			}
			let _, y = 0, b = p - h + 1, x = !1, S = 0, C = Array(b);
			for (u = 0; u < b; u++) C[u] = 0;
			for (u = m; u <= f; u++) {
				let n = e[u];
				if (y >= b) {
					de(n, a, o, !0);
					continue;
				}
				let i;
				if (n.key != null) i = g.get(n.key);
				else for (_ = h; _ <= p; _++) if (C[_ - h] === 0 && ci(n, t[_])) {
					i = _;
					break;
				}
				i === void 0 ? de(n, a, o, !0) : (C[i - h] = u + 1, i >= S ? S = i : x = !0, v(n, t[i], r, null, a, o, s, c, l), y++);
			}
			let w = x ? Gr(C) : n;
			for (_ = w.length - 1, u = b - 1; u >= 0; u--) {
				let e = h + u, n = t[e], f = t[e + 1], p = e + 1 < d ? f.el || Jr(f) : i;
				C[u] === 0 ? v(null, n, r, p, a, o, s, c, l) : x && (_ < 0 || u !== w[_] ? ue(n, r, p, 2) : _--);
			}
		}
	}, ue = (e, t, n, r, i = null) => {
		let { el: a, type: c, transition: l, children: u, shapeFlag: d } = e;
		if (d & 6) {
			ue(e.component.subTree, t, n, r);
			return;
		}
		if (d & 128) {
			e.suspense.move(t, n, r);
			return;
		}
		if (d & 64) {
			c.move(e, t, n, ge);
			return;
		}
		if (c === W) {
			o(a, t, n);
			for (let e = 0; e < u.length; e++) ue(u[e], t, n, r);
			o(e.anchor, t, n);
			return;
		}
		if (c === $r) {
			S(e, t, n);
			return;
		}
		if (r !== 2 && d & 1 && l) {
			if (r === 0) l.persisted && !a[In] ? o(a, t, n) : (l.beforeEnter(a), o(a, t, n), Rr(() => l.enter(a), i));
			else {
				let { leave: r, delayLeave: i, afterLeave: c } = l, u = () => {
					e.ctx.isUnmounted ? s(a) : o(a, t, n);
				}, d = () => {
					let e = a._isLeaving || !!a[In];
					a._isLeaving && a[In](!0), l.persisted && !e ? u() : r(a, () => {
						u(), c && c();
					});
				};
				i ? i(a, u, d) : d();
			}
		} else o(a, t, n);
	}, de = (e, t, n, r = !1, i = !1) => {
		let { type: a, props: o, ref: s, children: c, dynamicChildren: l, shapeFlag: u, patchFlag: d, dirs: f, cacheIndex: p, memo: m } = e;
		if (d === -2 && (i = !1), s != null && (ze(), Gn(s, null, n, e, !0), Be()), p != null && (t.renderCache[p] = void 0), u & 256) {
			t.ctx.deactivate(e);
			return;
		}
		let h = u & 1 && f, g = !qn(e), _;
		if (g && (_ = o && o.onVnodeBeforeUnmount) && vi(_, t, e), u & 6) pe(e.component, n, r);
		else {
			if (u & 128) {
				e.suspense.unmount(n, r);
				return;
			}
			h && On(e, null, t, "beforeUnmount"), u & 64 ? e.type.remove(e, t, n, ge, r) : l && !l.hasOnce && (a !== W || d > 0 && d & 64) ? P(l, t, n, !1, !0) : (a === W && d & 384 || !i && u & 16) && P(c, t, n), r && N(e);
		}
		let v = m != null && p == null;
		(g && (_ = o && o.onVnodeUnmounted) || h || v) && Rr(() => {
			_ && vi(_, t, e), h && On(e, null, t, "unmounted"), v && (e.el = null);
		}, n);
	}, N = (e) => {
		let { type: t, el: n, anchor: r, transition: i } = e;
		if (t === W) {
			fe(n, r);
			return;
		}
		if (t === $r) {
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
	}, fe = (e, t) => {
		let n;
		for (; e !== t;) n = h(e), s(e), e = n;
		s(t);
	}, pe = (e, t, n) => {
		let { bum: r, scope: i, job: a, subTree: o, um: s, m: c, a: l } = e;
		qr(c), qr(l), r && ie(r), i.stop(), a && (a.flags |= 8, de(o, e, t, n)), s && Rr(s, t), Rr(() => {
			e.isUnmounted = !0;
		}, t);
	}, P = (e, t, n, r = !1, i = !1, a = 0) => {
		for (let o = a; o < e.length; o++) de(e[o], t, n, r, i);
	}, F = (e) => {
		if (e.shapeFlag & 6) return F(e.component.subTree);
		if (e.shapeFlag & 128) return e.suspense.next();
		let t = h(e.anchor || e.el), n = t && t[Pn];
		return n ? h(n) : t;
	}, me = !1, he = (e, t, n) => {
		let r;
		e == null ? t._vnode && (de(t._vnode, null, null, !0), r = t._vnode.component) : v(t._vnode || null, e, t, null, null, null, n), t._vnode = e, me ||= (me = !0, yn(r), bn(), !1);
	}, ge = {
		p: v,
		um: de,
		m: ue,
		r: N,
		mt: A,
		mc: D,
		pc: M,
		pbc: O,
		n: F,
		o: e
	}, _e, I;
	return i && ([_e, I] = i(ge)), {
		render: he,
		hydrate: _e,
		createApp: cr(he, _e)
	};
}
function Vr({ type: e, props: t }, n) {
	return n === "svg" && e === "foreignObject" || n === "mathml" && e === "annotation-xml" && t && t.encoding && t.encoding.includes("html") ? void 0 : n;
}
function Hr({ effect: e, job: t }, n) {
	n ? (e.flags |= 32, t.flags |= 4) : (e.flags &= -33, t.flags &= -5);
}
function Ur(e, t) {
	return (!e || e && !e.pendingBranch) && t && !t.persisted;
}
function Wr(e, t, n = !1) {
	let r = e.children, i = t.children;
	if (d(r) && d(i)) for (let e = 0; e < r.length; e++) {
		let t = r[e], a = i[e];
		a.shapeFlag & 1 && !a.dynamicChildren && ((a.patchFlag <= 0 || a.patchFlag === 32) && (a = i[e] = hi(i[e]), a.el = t.el), !n && a.patchFlag !== -2 && Wr(t, a)), a.type === Zr && (a.patchFlag === -1 && (a = i[e] = hi(a)), a.el = t.el), a.type === Qr && !a.el && (a.el = t.el);
	}
}
function Gr(e) {
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
function Kr(e) {
	let t = e.subTree.component;
	if (t) return t.asyncDep && !t.asyncResolved ? t : Kr(t);
}
function qr(e) {
	if (e) for (let t = 0; t < e.length; t++) e[t].flags |= 8;
}
function Jr(e) {
	if (e.placeholder) return e.placeholder;
	let t = e.component;
	return t ? Jr(t.subTree) : null;
}
var Yr = (e) => e.__isSuspense;
function Xr(e, t) {
	t && t.pendingBranch ? d(e) ? t.effects.push(...e) : t.effects.push(e) : vn(e);
}
var W = /* @__PURE__ */ Symbol.for("v-fgt"), Zr = /* @__PURE__ */ Symbol.for("v-txt"), Qr = /* @__PURE__ */ Symbol.for("v-cmt"), $r = /* @__PURE__ */ Symbol.for("v-stc"), ei = [], ti = null;
function G(e = !1) {
	ei.push(ti = e ? null : []);
}
function ni() {
	ei.pop(), ti = ei[ei.length - 1] || null;
}
var ri = 1;
function ii(e, t = !1) {
	ri += e, e < 0 && ti && t && (ti.hasOnce = !0);
}
function ai(e) {
	return e.dynamicChildren = ri > 0 ? ti || n : null, ni(), ri > 0 && ti && ti.push(e), e;
}
function K(e, t, n, r, i, a) {
	return ai(q(e, t, n, r, i, a, !0));
}
function oi(e, t, n, r, i) {
	return ai(J(e, t, n, r, i, !0));
}
function si(e) {
	return e ? e.__v_isVNode === !0 : !1;
}
function ci(e, t) {
	return e.type === t.type && e.key === t.key;
}
var li = ({ key: e }) => e ?? null, ui = ({ ref: e, ref_key: t, ref_for: n }) => (typeof e == "number" && (e = "" + e), e == null ? null : g(e) || /* @__PURE__ */ Ht(e) || h(e) ? {
	i: Cn,
	r: e,
	k: t,
	f: !!n
} : e);
function q(e, t = null, n = null, r = 0, i = null, a = e === W ? 0 : 1, o = !1, s = !1) {
	let c = {
		__v_isVNode: !0,
		__v_skip: !0,
		type: e,
		props: t,
		key: t && li(t),
		ref: t && ui(t),
		scopeId: wn,
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
		ctx: Cn
	};
	return s ? (gi(c, n), a & 128 && e.normalize(c)) : n && (c.shapeFlag |= g(n) ? 8 : 16), ri > 0 && !o && ti && (c.patchFlag > 0 || a & 6) && c.patchFlag !== 32 && ti.push(c), c;
}
var J = di;
function di(e, t = null, n = null, r = 0, i = null, a = !1) {
	if ((!e || e === $n) && (e = Qr), si(e)) {
		let r = pi(e, t, !0);
		return n && gi(r, n), ri > 0 && !a && ti && (r.shapeFlag & 6 ? ti[ti.indexOf(e)] = r : ti.push(r)), r.patchFlag = -2, r;
	}
	if (Li(e) && (e = e.__vccOpts), t) {
		t = fi(t);
		let { class: e, style: n } = t;
		e && !g(e) && (t.class = N(e)), v(n) && (/* @__PURE__ */ Rt(n) && !d(n) && (n = s({}, n)), t.style = M(n));
	}
	let o = g(e) ? 1 : Yr(e) ? 128 : Fn(e) ? 64 : v(e) ? 4 : h(e) ? 2 : 0;
	return q(e, t, n, r, i, o, a, !0);
}
function fi(e) {
	return e ? /* @__PURE__ */ Rt(e) || Cr(e) ? s({}, e) : e : null;
}
function pi(e, t, n = !1, r = !1) {
	let { props: i, ref: a, patchFlag: o, children: s, transition: c } = e, l = t ? _i(i || {}, t) : i, u = {
		__v_isVNode: !0,
		__v_skip: !0,
		type: e.type,
		props: l,
		key: l && li(l),
		ref: t && t.ref ? n && a ? d(a) ? a.concat(ui(t)) : [a, ui(t)] : ui(t) : a,
		scopeId: e.scopeId,
		slotScopeIds: e.slotScopeIds,
		children: s,
		target: e.target,
		targetStart: e.targetStart,
		targetAnchor: e.targetAnchor,
		staticCount: e.staticCount,
		shapeFlag: e.shapeFlag,
		patchFlag: t && e.type !== W ? o === -1 ? 16 : o | 16 : o,
		dynamicProps: e.dynamicProps,
		dynamicChildren: e.dynamicChildren,
		appContext: e.appContext,
		dirs: e.dirs,
		transition: c,
		component: e.component,
		suspense: e.suspense,
		ssContent: e.ssContent && pi(e.ssContent),
		ssFallback: e.ssFallback && pi(e.ssFallback),
		placeholder: e.placeholder,
		el: e.el,
		anchor: e.anchor,
		ctx: e.ctx,
		ce: e.ce
	};
	return c && r && zn(u, c.clone(u)), u;
}
function Y(e = " ", t = 0) {
	return J(Zr, null, e, t);
}
function X(e = "", t = !1) {
	return t ? (G(), oi(Qr, null, e)) : J(Qr, null, e);
}
function mi(e) {
	return e == null || typeof e == "boolean" ? J(Qr) : d(e) ? J(W, null, e.slice()) : si(e) ? hi(e) : J(Zr, null, String(e));
}
function hi(e) {
	return e.el === null && e.patchFlag !== -1 || e.memo ? e : pi(e);
}
function gi(e, t) {
	let n = 0, { shapeFlag: r } = e;
	if (t == null) t = null;
	else if (d(t)) n = 16;
	else if (typeof t == "object") {
		if (r & 65) {
			let n = t.default;
			n && (n._c && (n._d = !1), gi(e, n()), n._c && (n._d = !0));
			return;
		}
		{
			n = 32;
			let r = t._;
			!r && !Cr(t) ? t._ctx = Cn : r === 3 && Cn && (Cn.slots._ === 1 ? t._ = 1 : (t._ = 2, e.patchFlag |= 1024));
		}
	} else if (h(t)) {
		if (r & 65) {
			gi(e, { default: t });
			return;
		}
		t = {
			default: t,
			_ctx: Cn
		}, n = 32;
	} else t = String(t), r & 64 ? (n = 16, t = [Y(t)]) : n = 8;
	e.children = t, e.shapeFlag |= n;
}
function _i(...e) {
	let t = {};
	for (let n = 0; n < e.length; n++) {
		let r = e[n];
		for (let e in r) if (e === "class") t.class !== r.class && (t.class = N([t.class, r.class]));
		else if (e === "style") t.style = M([t.style, r.style]);
		else if (a(e)) {
			let n = t[e], i = r[e];
			i && n !== i && !(d(n) && n.includes(i)) ? t[e] = n ? [].concat(n, i) : i : i == null && n == null && !o(e) && (t[e] = i);
		} else e !== "" && (t[e] = r[e]);
	}
	return t;
}
function vi(e, t, n, r = null) {
	rn(e, t, 7, [n, r]);
}
var yi = or(), bi = 0;
function xi(e, n, r) {
	let i = e.type, a = (n ? n.appContext : e.appContext) || yi, o = {
		uid: bi++,
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
		scope: new be(!0),
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
		propsOptions: Or(i, a),
		emitsOptions: fr(i, a),
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
	return o.ctx = { _: o }, o.root = n ? n.root : o, o.emit = dr.bind(null, o), e.ce && e.ce(o), o;
}
var Si = null, Ci = () => Si || Cn, wi, Ti;
{
	let e = se(), t = (t, n) => {
		let r;
		return (r = e[t]) || (r = e[t] = []), r.push(n), (e) => {
			r.length > 1 ? r.forEach((t) => t(e)) : r[0](e);
		};
	};
	wi = t("__VUE_INSTANCE_SETTERS__", (e) => Si = e), Ti = t("__VUE_SSR_SETTERS__", (e) => ki = e);
}
var Ei = (e) => {
	let t = Si;
	return wi(e), e.scope.on(), () => {
		e.scope.off(), wi(t);
	};
}, Di = () => {
	Si && Si.scope.off(), wi(null);
};
function Oi(e) {
	return e.vnode.shapeFlag & 4;
}
var ki = !1;
function Ai(e, t = !1, n = !1) {
	t && Ti(t);
	let { props: r, children: i } = e.vnode, a = Oi(e);
	wr(e, r, a, t), Ir(e, i, n || t);
	let o = a ? ji(e, t) : void 0;
	return t && Ti(!1), o;
}
function ji(e, t) {
	let n = e.type;
	e.accessCache = /* @__PURE__ */ Object.create(null), e.proxy = new Proxy(e.ctx, ar);
	let { setup: r } = n;
	if (r) {
		ze();
		let n = e.setupContext = r.length > 1 ? Fi(e) : null, i = Ei(e), a = nn(r, e, 0, [e.props, n]), o = y(a);
		if (Be(), i(), (o || e.sp) && !qn(e) && Hn(e), o) {
			if (a.then(Di, Di), t) return a.then((n) => {
				Ti(!0);
				try {
					Mi(e, n, t);
				} finally {
					Ti(!1);
				}
			}).catch((t) => {
				an(t, e, 0);
			});
			e.asyncDep = a;
		} else Mi(e, a, t);
	} else Ni(e, t);
}
function Mi(e, t, n) {
	h(t) ? e.type.__ssrInlineRender ? e.ssrRender = t : e.render = t : v(t) && (e.setupState = qt(t)), Ni(e, n);
}
function Ni(e, t, n) {
	let i = e.type;
	e.render ||= i.render || r;
}
var Pi = { get(e, t) {
	return Xe(e, "get", ""), e[t];
} };
function Fi(e) {
	return {
		attrs: new Proxy(e.attrs, Pi),
		slots: e.slots,
		emit: e.emit,
		expose: (t) => {
			e.exposed = t || {};
		}
	};
}
function Ii(e) {
	return e.exposed ? e.exposeProxy ||= new Proxy(qt(zt(e.exposed)), {
		get(t, n) {
			if (n in t) return t[n];
			if (n in rr) return rr[n](e);
		},
		has(e, t) {
			return t in e || t in rr;
		}
	}) : e.proxy;
}
function Li(e) {
	return h(e) && "__vccOpts" in e;
}
var Z = (e, t) => /* @__PURE__ */ Yt(e, t, ki), Ri = "3.5.42", zi = void 0, Bi = typeof window < "u" && window.trustedTypes;
if (Bi) try {
	zi = /* @__PURE__ */ Bi.createPolicy("vue", { createHTML: (e) => e });
} catch {}
var Vi = zi ? (e) => zi.createHTML(e) : (e) => e, Hi = "http://www.w3.org/2000/svg", Ui = "http://www.w3.org/1998/Math/MathML", Wi = typeof document < "u" ? document : null, Gi = Wi && /* @__PURE__ */ Wi.createElement("template"), Ki = {
	insert: (e, t, n) => {
		t.insertBefore(e, n || null);
	},
	remove: (e) => {
		let t = e.parentNode;
		t && t.removeChild(e);
	},
	createElement: (e, t, n, r) => {
		let i = t === "svg" ? Wi.createElementNS(Hi, e) : t === "mathml" ? Wi.createElementNS(Ui, e) : n ? Wi.createElement(e, { is: n }) : Wi.createElement(e);
		return e === "select" && r && r.multiple != null && i.setAttribute("multiple", r.multiple), i;
	},
	createText: (e) => Wi.createTextNode(e),
	createComment: (e) => Wi.createComment(e),
	setText: (e, t) => {
		e.nodeValue = t;
	},
	setElementText: (e, t) => {
		e.textContent = t;
	},
	parentNode: (e) => e.parentNode,
	nextSibling: (e) => e.nextSibling,
	querySelector: (e) => Wi.querySelector(e),
	setScopeId(e, t) {
		e.setAttribute(t, "");
	},
	insertStaticContent(e, t, n, r, i, a) {
		let o = n ? n.previousSibling : t.lastChild;
		if (i && (i === a || i.nextSibling)) for (; t.insertBefore(i.cloneNode(!0), n), i !== a && (i = i.nextSibling););
		else {
			Gi.innerHTML = Vi(r === "svg" ? `<svg>${e}</svg>` : r === "mathml" ? `<math>${e}</math>` : e);
			let i = Gi.content;
			if (r === "svg" || r === "mathml") {
				let e = i.firstChild;
				for (; e.firstChild;) i.appendChild(e.firstChild);
				i.removeChild(e);
			}
			t.insertBefore(i, n);
		}
		return [o ? o.nextSibling : t.firstChild, n ? n.previousSibling : t.lastChild];
	}
}, qi = /* @__PURE__ */ Symbol("_vtc");
function Ji(e, t, n) {
	let r = e[qi];
	r && (t = (t ? [t, ...r] : [...r]).join(" ")), t == null ? e.removeAttribute("class") : n ? e.setAttribute("class", t) : e.className = t;
}
var Yi = /* @__PURE__ */ Symbol("_vod"), Xi = /* @__PURE__ */ Symbol("_vsh"), Zi = {
	name: "show",
	beforeMount(e, { value: t }, { transition: n }) {
		e[Yi] = e.style.display === "none" ? "" : e.style.display, n && t ? n.beforeEnter(e) : Qi(e, t);
	},
	mounted(e, { value: t }, { transition: n }) {
		n && t && n.enter(e);
	},
	updated(e, { value: t, oldValue: n }, { transition: r }) {
		!t != !n && (r ? t ? (r.beforeEnter(e), Qi(e, !0), r.enter(e)) : r.leave(e, () => {
			Qi(e, !1);
		}) : Qi(e, t));
	},
	beforeUnmount(e, { value: t }) {
		Qi(e, t);
	}
};
function Qi(e, t) {
	e.style.display = t ? e[Yi] : "none", e[Xi] = !t;
}
var $i = /* @__PURE__ */ Symbol(""), ea = /(?:^|;)\s*display\s*:/;
function ta(e, t, n) {
	let r = e.style, i = g(n), a = !1;
	if (n && !i) {
		if (t) {
			if (g(t)) for (let e of t.split(";")) {
				let t = e.slice(0, e.indexOf(":")).trim();
				n[t] ?? ra(r, t, "");
			}
			else for (let e in t) n[e] ?? ra(r, e, "");
		}
		for (let i in n) {
			i === "display" && (a = !0);
			let o = n[i];
			o == null ? ra(r, i, "") : sa(e, i, !g(t) && t ? t[i] : void 0, o) || ra(r, i, o);
		}
	} else if (i) {
		if (t !== n) {
			let e = r[$i];
			e && (n += ";" + e), r.cssText = n, a = ea.test(n);
		}
	} else t && e.removeAttribute("style");
	Yi in e && (e[Yi] = a ? r.display : "", e[Xi] && (r.display = "none"));
}
var na = /\s*!important$/;
function ra(e, t, n) {
	if (d(n)) n.forEach((n) => ra(e, t, n));
	else if (n ??= "", t.startsWith("--")) na.test(n) ? e.setProperty(t, n.replace(na, ""), "important") : e.setProperty(t, n);
	else {
		let r = oa(e, t);
		na.test(n) ? e.setProperty(O(r), n.replace(na, ""), "important") : e[r] = n;
	}
}
var ia = [
	"Webkit",
	"Moz",
	"ms"
], aa = {};
function oa(e, t) {
	let n = aa[t];
	if (n) return n;
	let r = D(t);
	if (r !== "filter" && r in e) return aa[t] = r;
	r = ne(r);
	for (let n = 0; n < ia.length; n++) {
		let i = ia[n] + r;
		if (i in e) return aa[t] = i;
	}
	return t;
}
function sa(e, t, n, r) {
	return e.tagName === "TEXTAREA" && (t === "width" || t === "height") && g(r) && n === r;
}
var ca = "http://www.w3.org/1999/xlink";
function la(e, t, n, r, i, a = pe(t)) {
	r && t.startsWith("xlink:") ? n == null ? e.removeAttributeNS(ca, t.slice(6, t.length)) : e.setAttributeNS(ca, t, n) : n == null || a && !P(n) ? e.removeAttribute(t) : e.setAttribute(t, a ? "" : _(n) ? String(n) : n);
}
function ua(e, t, n, r, i) {
	if (t === "innerHTML" || t === "textContent") {
		n != null && (e[t] = t === "innerHTML" ? Vi(n) : n);
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
		r === "boolean" ? n = P(n) : n == null && r === "string" ? (n = "", o = !0) : r === "number" && (n = 0, o = !0);
	}
	try {
		e[t] = n;
	} catch {}
	o && e.removeAttribute(i || t);
}
function da(e, t, n, r) {
	e.addEventListener(t, n, r);
}
function fa(e, t, n, r) {
	e.removeEventListener(t, n, r);
}
var pa = /* @__PURE__ */ Symbol("_vei");
function ma(e, t, n, r, i = null) {
	let a = e[pa] || (e[pa] = {}), o = a[t];
	if (r && o) o.value = r;
	else {
		let [n, s] = _a(t);
		r ? da(e, n, a[t] = xa(r, i), s) : o && (fa(e, n, o, s), a[t] = void 0);
	}
}
var ha = /(Once|Passive|Capture)$/, ga = /^on:?(?:Once|Passive|Capture)$/;
function _a(e) {
	let t, n;
	for (; (n = e.match(ha)) && !ga.test(e);) t ||= {}, e = e.slice(0, e.length - n[1].length), t[n[1].toLowerCase()] = !0;
	return [e[2] === ":" ? e.slice(3) : O(e.slice(2)), t];
}
var va = 0, ya = /* @__PURE__ */ Promise.resolve(), ba = () => va ||= (ya.then(() => va = 0), Date.now());
function xa(e, t) {
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
				e && rn(e, t, 5, a);
			}
		} else rn(r, t, 5, [e]);
	};
	return n.value = e, n.attached = ba(), n;
}
var Sa = (e) => e.charCodeAt(0) === 111 && e.charCodeAt(1) === 110 && e.charCodeAt(2) > 96 && e.charCodeAt(2) < 123, Ca = (e, t, n, r, i, s) => {
	let c = i === "svg";
	t === "class" ? Ji(e, r, c) : t === "style" ? ta(e, n, r) : a(t) ? o(t) || ma(e, t, n, r, s) : (t[0] === "." ? (t = t.slice(1), 1) : t[0] === "^" ? (t = t.slice(1), 0) : wa(e, t, r, c)) ? (ua(e, t, r), !e.tagName.includes("-") && (t === "value" || t === "checked" || t === "selected") && la(e, t, r, c, s, t !== "value")) : e._isVueCE && (Ta(e, t) || e._def.__asyncLoader && (/[A-Z]/.test(t) || !g(r))) ? ua(e, D(t), r, s, t) : (t === "true-value" ? e._trueValue = r : t === "false-value" && (e._falseValue = r), la(e, t, r, c));
};
function wa(e, t, n, r) {
	if (r) return !!(t === "innerHTML" || t === "textContent" || t in e && Sa(t) && h(n));
	if (t === "spellcheck" || t === "draggable" || t === "translate" || t === "autocorrect" || t === "sandbox" && e.tagName === "IFRAME" || t === "form" || t === "list" && e.tagName === "INPUT" || t === "type" && e.tagName === "TEXTAREA") return !1;
	if (t === "width" || t === "height") {
		let t = e.tagName;
		if (t === "IMG" || t === "VIDEO" || t === "CANVAS" || t === "SOURCE") return !1;
	}
	return Sa(t) && g(n) ? !1 : t in e;
}
function Ta(e, t) {
	let n = e._def.props;
	if (!n) return !1;
	let r = D(t);
	return Array.isArray(n) ? n.some((e) => D(e) === r) : Object.keys(n).some((e) => D(e) === r);
}
var Ea = {};
// @__NO_SIDE_EFFECTS__
function Da(e, t, n) {
	let r = /* @__PURE__ */ Bn(e, t);
	C(r) && (r = s({}, r, t));
	class i extends ka {
		constructor(e) {
			super(r, e, n);
		}
	}
	return i.def = r, i;
}
var Oa = typeof HTMLElement < "u" ? HTMLElement : class {}, ka = class e extends Oa {
	constructor(e, t = {}, n = Xa) {
		super(), this._def = e, this._props = t, this._createApp = n, this._isVueCE = !0, this._instance = null, this._app = null, this._nonce = this._def.nonce, this._connected = !1, this._resolved = !1, this._patching = !1, this._dirty = !1, this._numberProps = null, this._styleChildren = /* @__PURE__ */ new WeakSet(), this._styleAnchors = /* @__PURE__ */ new WeakMap(), this._ob = null, this.shadowRoot && n !== Xa ? this._root = this.shadowRoot : e.shadowRoot === !1 ? this._root = this : (this.attachShadow(s({}, e.shadowRootOptions, { mode: "open" })), this._root = this.shadowRoot);
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
		this._connected = !1, mn(() => {
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
				(t === Number || t && t.type === Number) && (e in this._props && (this._props[e] = ae(this._props[e])), (i ||= /* @__PURE__ */ Object.create(null))[D(e)] = !0);
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
		if (t) for (let e in t) u(this, e) || Object.defineProperty(this, e, { get: () => V(t[e]) });
	}
	_resolveProps(e) {
		let { props: t } = e, n = d(t) ? t : Object.keys(t || {});
		for (let e of Object.keys(this)) e[0] !== "_" && n.includes(e) && this._setProp(e, this[e]);
		for (let e of n.map(D)) Object.defineProperty(this, e, {
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
		let t = this.hasAttribute(e), n = t ? this.getAttribute(e) : Ea, r = D(e);
		t && this._numberProps && this._numberProps[r] && (n = ae(n)), this._setProp(r, n, !1, !0);
	}
	_getProp(e) {
		return this._props[e];
	}
	_setProp(e, t, n = !0, r = !1) {
		if (t !== this._props[e] && (this._dirty = !0, t === Ea ? delete this._props[e] : (this._props[e] = t, e === "key" && this._app && (this._app._ceVNode.key = t)), r && this._instance && this._update(), n)) {
			let n = this._ob;
			n && (this._processMutations(n.takeRecords()), n.disconnect()), t === !0 ? this.setAttribute(O(e), "") : typeof t == "string" || typeof t == "number" ? this.setAttribute(O(e), t + "") : t || this.removeAttribute(O(e)), n && n.observe(this, { attributes: !0 });
		}
	}
	_update() {
		let e = this._createVNode();
		this._app && (e.appContext = this._app._context), Ya(e, this._root);
	}
	_createVNode() {
		let e = {};
		this.shadowRoot || (e.onVnodeMounted = e.onVnodeUpdated = this._renderSlots.bind(this));
		let t = J(this._def, s(e, this._props));
		return this._instance || (t.ce = (e) => {
			this._instance = e, e.ce = this, e.isCE = !0;
			let t = (e, t) => {
				this.dispatchEvent(new CustomEvent(e, C(t[0]) ? s({ detail: t }, t[0]) : { detail: t }));
			};
			e.emit = (e, ...n) => {
				t(e, n), O(e) !== e && t(O(e), n);
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
function Aa(e) {
	let t = Ci();
	return t && t.ce || null;
}
var ja = (e) => {
	let t = e.props["onUpdate:modelValue"] || !1;
	return d(t) ? (e) => ie(t, e) : t;
};
function Ma(e) {
	e.target.composing = !0;
}
function Na(e) {
	let t = e.target;
	t.composing && (t.composing = !1, t.dispatchEvent(new Event("input")));
}
var Pa = /* @__PURE__ */ Symbol("_assign"), Fa = /* @__PURE__ */ Symbol("_initialValue");
function Ia(e, t, n) {
	return t && (e = e.trim()), n && (e = j(e)), e;
}
var La = {
	created(e, { modifiers: { lazy: t, trim: n, number: r } }, i) {
		e.parentNode && (e.type === "text" ? e[Fa] = e.defaultValue.replace(/[\r\n]/g, "") : e.type === "textarea" && (e[Fa] = e.defaultValue.replace(/\r\n?/g, "\n"))), e[Pa] = ja(i);
		let a = r || i.props && i.props.type === "number";
		da(e, t ? "change" : "input", (t) => {
			t.target.composing || e[Pa](Ia(e.value, n, a));
		}), (n || a) && da(e, "change", () => {
			e.value = Ia(e.value, n, a);
		}), t || (da(e, "compositionstart", Ma), da(e, "compositionend", Na), da(e, "change", Na));
	},
	mounted(e, { value: t, modifiers: { trim: n, number: r } }) {
		let i = t ?? "", a = e[Fa];
		delete e[Fa], a !== void 0 && (e.type === "text" || e.type === "textarea") && e.value !== a ? e[Pa](Ia(e.value, n, r)) : e.value = i;
	},
	beforeUpdate(e, { value: t, oldValue: n, modifiers: { lazy: r, trim: i, number: a } }, o) {
		if (e[Pa] = ja(o), e.composing) return;
		let s = (a || e.type === "number") && !/^0\d/.test(e.value) ? j(e.value) : e.value, c = t ?? "";
		if (s === c) return;
		let l = e.getRootNode();
		(l instanceof Document || l instanceof ShadowRoot) && l.activeElement === e && e.type !== "range" && (r && t === n || i && e.value.trim() === c) || (e.value = c);
	}
}, Ra = {
	created(e, { value: t }, n) {
		e.checked = he(t, n.props.value), e[Pa] = ja(n), da(e, "change", () => {
			e[Pa](Ha(e));
		});
	},
	beforeUpdate(e, { value: t, oldValue: n }, r) {
		e[Pa] = ja(r), t !== n && (e.checked = he(t, r.props.value));
	}
}, za = {
	deep: !0,
	created(e, { value: t, modifiers: { number: n } }, r) {
		e._modelValue = t, da(e, "change", () => {
			let t = Array.prototype.filter.call(e.options, (e) => e.selected).map((e) => n ? j(Ha(e)) : Ha(e)), r = e.multiple, i = r ? p(e._modelValue) ? new Set(t) : t : t[0], a = e._pendingValue = [r, r ? d(i) ? t.slice() : t : i];
			try {
				e[Pa](i);
			} finally {
				mn(() => {
					e._pendingValue === a && (e._pendingValue = void 0);
				});
			}
		}), e[Pa] = ja(r);
	},
	mounted(e, { value: t }) {
		Va(e, t);
	},
	beforeUpdate(e, { value: t }, n) {
		e._modelValue = t, e[Pa] = ja(n);
	},
	updated(e, { value: t }) {
		let n = e._pendingValue;
		e._pendingValue = void 0, (!n || n[0] !== e.multiple || !Ba(t, n[1], n[0])) && Va(e, t);
	}
};
function Ba(e, t, n) {
	if (!n || d(e)) return he(e, t);
	if (p(e)) {
		if (e.size !== t.length) return !1;
		for (let n of t) if (!e.has(n)) return !1;
		return !0;
	}
	return !1;
}
function Va(e, t) {
	let n = e.multiple, r = d(t);
	if (!n || r || p(t)) {
		for (let i = 0, a = e.options.length; i < a; i++) {
			let a = e.options[i], o = Ha(a);
			if (n) {
				if (r) {
					let e = typeof o;
					a.selected = e === "string" || e === "number" ? t.some((e) => String(e) === String(o)) : ge(t, o) > -1;
				} else a.selected = t.has(o);
			} else if (he(Ha(a), t)) {
				e.selectedIndex !== i && (e.selectedIndex = i);
				return;
			}
		}
		!n && e.selectedIndex !== -1 && (e.selectedIndex = -1);
	}
}
function Ha(e) {
	return "_value" in e ? e._value : e.value;
}
var Ua = [
	"ctrl",
	"shift",
	"alt",
	"meta"
], Wa = {
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
	exact: (e, t) => Ua.some((n) => e[`${n}Key`] && !t.includes(n))
}, Ga = (e, t) => {
	if (!e) return e;
	let n = e._withMods ||= {}, r = t.join(".");
	return n[r] || (n[r] = ((n, ...r) => {
		for (let e = 0; e < t.length; e++) {
			let r = Wa[t[e]];
			if (r && r(n, t)) return;
		}
		return e(n, ...r);
	}));
}, Ka = /* @__PURE__ */ s({ patchProp: Ca }, Ki), qa;
function Ja() {
	return qa ||= zr(Ka);
}
var Ya = ((...e) => {
	Ja().render(...e);
}), Xa = ((...e) => {
	let t = Ja().createApp(...e), { mount: n } = t;
	return t.mount = (e) => {
		let r = Qa(e);
		if (!r) return;
		let i = t._component;
		!h(i) && !i.render && !i.template && (i.template = r.innerHTML), r.nodeType === 1 && (r.textContent = "");
		let a = n(r, !1, Za(r));
		return r instanceof Element && (r.removeAttribute("v-cloak"), r.setAttribute("data-v-app", "")), a;
	}, t;
});
function Za(e) {
	if (e instanceof SVGElement) return "svg";
	if (typeof MathMLElement == "function" && e instanceof MathMLElement) return "mathml";
}
function Qa(e) {
	return g(e) ? document.querySelector(e) : e;
}
//#endregion
//#region src/tabs.ts
var $a = [
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
function eo(e, t) {
	let n = e.split(/[?#]/, 1)[0].replace(/\/+$/, "");
	return (n.startsWith(`${t}/`) ? n.slice(t.length) : n === t ? "" : n).replace(/^\//, "") || $a[0].path;
}
var to = {
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
function no(e) {
	return {
		comma_decimal: "en-US",
		decimal_comma: "de-DE",
		space_comma: "fr-FR"
	}[e?.locale?.number_format ?? ""] ?? e?.locale?.language ?? e?.language ?? "en";
}
function ro(e, t, n = 2) {
	let r = Q(e);
	return r === null ? null : new Intl.NumberFormat(no(t), {
		minimumFractionDigits: n,
		maximumFractionDigits: n,
		useGrouping: t?.locale?.number_format !== "none"
	}).format(r);
}
function io(e, t, n = {
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
function ao(e, t) {
	let n = (e) => /^\d{4}-\d{2}-\d{2}$/.test(e) && Number(e.slice(0, 4)) > 0 && Number.isFinite(Date.parse(`${e}T00:00:00Z`)) && (/* @__PURE__ */ new Date(`${e}T00:00:00Z`)).toISOString().slice(0, 10) === e;
	return n(e) && n(t) && e <= t;
}
function oo(e) {
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
function so(e, t, n) {
	let r = /* @__PURE__ */ Ut(null), i = /* @__PURE__ */ B(!1), a = /* @__PURE__ */ B(null), o, s = 0, c = !1;
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
					first_weekday: oo(u),
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
		if (!ao(e, t)) {
			a.value = "invalid";
			return;
		}
		o = {
			start_date: e,
			end_date: t
		}, l();
	}
	return H([
		() => e()?.connection,
		t,
		n,
		() => oo(e()),
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
	}, { immediate: !0 }), Se(() => {
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
var co = {
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
}, lo = Symbol("sax-dashboard");
function uo(e) {
	return typeof e != "string" || e.length !== 5 && e.length !== 8 || !/^([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(e) ? null : e.length === 5 ? `${e}:00` : e;
}
function fo(e, t, n, r, i) {
	let a = co[r];
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
function po(e, t) {
	let n = e.state?.attributes ?? {};
	switch (e.metadata.domain) {
		case "switch": return typeof t == "boolean" ? {
			service: t ? "turn_on" : "turn_off",
			data: {}
		} : null;
		case "number": {
			if (typeof t != "number" && typeof t != "string" || typeof t == "string" && t.trim() === "") return null;
			let e = Number(t), { min: r, max: i, step: a } = n;
			if (!Number.isFinite(e) || typeof r != "number" || !Number.isFinite(r) || typeof i != "number" || !Number.isFinite(i) || typeof a != "number" || !Number.isFinite(a) || a <= 0 || r > i || e < r || e > i) return null;
			let o = (e - r) / a;
			return !Number.isFinite(o) || Math.abs(o - Math.round(o)) > 1e-7 ? null : {
				service: "set_value",
				data: { value: e }
			};
		}
		case "time": {
			let e = uo(t);
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
function mo(e, t) {
	let n = Z(() => e()?.language.toLowerCase().startsWith("de") ? "de" : "en"), r = /* @__PURE__ */ Ut(null), i = /* @__PURE__ */ B(!1), a = /* @__PURE__ */ B(!1), o = /* @__PURE__ */ B(null), s = Z(() => o.value ? co[n.value][o.value] : null), c = /* @__PURE__ */ Ut([]), l = /* @__PURE__ */ jt(/* @__PURE__ */ new Map()), u = /* @__PURE__ */ jt(/* @__PURE__ */ new Map()), d = (e, n) => JSON.stringify([
		t(),
		e,
		n
	]), f = 0;
	function p(e = !0) {
		e && (f += 1), i.value = !1, r.value = null, c.value = [];
		for (let [e, t] of l) t.pending ? t.error = null : l.delete(e);
	}
	let m = H([
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
	Se(() => {
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
			displayValue: fo(o, i, s, n.value, a.value),
			canControl: f && i.can_control && !!o?.callService,
			pending: p?.pending ?? !1,
			error: p?.error ? co[n.value][p.error] : null
		};
	}
	async function g(t, n, r) {
		let a = h(t, n);
		if (!a || a.pending) return !1;
		let o = /* @__PURE__ */ jt({
			pending: !1,
			error: null
		});
		l.set(a.metadata.entity_id, o);
		let s = e();
		if (!a.canControl || !s?.callService || !i.value) return o.error = "forbidden", !1;
		let c = po(a, r);
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
		let s = /* @__PURE__ */ jt({
			pending: !1,
			error: null
		});
		for (let e of o) e && l.set(e.metadata.entity_id, s);
		let c = o[0]?.metadata.device_id, p = e();
		if (!i.value || !p?.callService || !c || o.some((e) => !e?.canControl || e.metadata.device_id !== c)) return s.error = "forbidden", !1;
		let m = uo(n), g = uo(r);
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
			"price_charge_max_price",
			"price_charge_hours",
			"price_charge_neutral_price"
		]), r = Object.keys(t);
		if (!r.length || r.some((e) => !n.has(e))) return !1;
		let a = r.map((e) => h("number", e));
		if (a.some((e) => e?.pending)) return !1;
		let o = /* @__PURE__ */ jt({
			pending: !1,
			error: null
		});
		for (let e of a) e && l.set(e.metadata.entity_id, o);
		let s = a[0]?.metadata.device_id, c = e();
		if (!i.value || !c?.callService || !s || a.some((e) => !e?.canControl || e.metadata.device_id !== s)) return o.error = "forbidden", !1;
		let p = {}, m = t.max_soc === void 0 ? Q(h("number", "max_soc")?.state?.state) : Q(t.max_soc);
		for (let e = 0; e < r.length; e++) {
			let n = r[e], i = a[e], s = po(n === "timed_charge_max_soc" && m !== null ? {
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
					for (let e = 0; e < r.length; e++) l.set(g[e], /* @__PURE__ */ jt({
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
	H([
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
		ready: /* @__PURE__ */ Nt(i),
		connected: /* @__PURE__ */ Nt(a),
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
var ho = ".editor-actions{flex-wrap:nowrap;align-items:center;gap:8px;max-width:100%;display:flex}.editor-actions>button{white-space:nowrap;flex:none}.editor-actions>button:first-child:not(:only-child){background:var(--primary-color,#03a9f4);color:var(--text-primary-color,#fff)}", go = (e, t) => {
	let n = e.__vccOpts || e;
	for (let [e, r] of t) n[e] = r;
	return n;
}, _o = {}, vo = { class: "editor-actions" };
function yo(e, t) {
	return G(), K("div", vo, [er(e.$slots, "default")]);
}
var bo = /*#__PURE__*/ go(_o, [["render", yo], ["styles", [ho]]]), xo = ["aria-busy"], So = { class: "entity-control__name" }, Co = [
	"checked",
	"indeterminate",
	"disabled"
], wo = { class: "entity-control__description" }, To = { key: 0 }, Eo = { class: "entity-control__input" }, Do = [
	"checked",
	"disabled",
	"aria-describedby"
], Oo = [
	"value",
	"disabled",
	"aria-describedby"
], ko = {
	key: 0,
	value: "",
	disabled: ""
}, Ao = ["value"], jo = [
	"value",
	"type",
	"min",
	"max",
	"step",
	"disabled",
	"aria-describedby",
	"aria-invalid"
], Mo = ["disabled"], No = ["disabled"], Po = {
	key: 0,
	class: "entity-control__error",
	role: "alert"
}, Fo = {
	key: 1,
	role: "status"
}, Io = ["aria-labelledby", "aria-describedby"], Lo = ["id"], Ro = ["id"], zo = ["disabled"], Bo = /*#__PURE__*/ go(/* @__PURE__ */ Bn({
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
		let t = e, n = An(lo), r = Z(() => n?.entity(t.domain, t.entityKey)), i = Vn(), a = `sax-control-${i}`, o = `sax-status-${i}`, s = `sax-value-${i}`, c = /* @__PURE__ */ B(""), l = /* @__PURE__ */ B(), u = /* @__PURE__ */ B(), d = /* @__PURE__ */ Ut(null), f = Z(() => r.value?.state?.state ?? ""), p = Z(() => r.value?.state?.attributes ?? {}), m = Z(() => {
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
		H([() => r.value?.metadata.entity_id, () => f.value], ([, e]) => {
			c.value = x(e);
		}, { immediate: !0 });
		function w(e) {
			let t = p.value[e];
			return typeof t == "number" && Number.isFinite(t) ? t : void 0;
		}
		function T(e) {
			return r.value?.metadata.states[e] ?? e;
		}
		function ee() {
			r.value?.pending || (c.value = x(f.value), u.value && (u.value.value = c.value), n?.clearControlError(t.domain, t.entityKey));
		}
		async function E() {
			y.value || !n || t.domain !== "number" && t.domain !== "time" || await n.perform(t.domain, t.entityKey, t.domain === "time" && c.value ? `${c.value}:00` : c.value);
		}
		function D() {
			d.value = null, l.value?.open && l.value.close();
		}
		function te() {
			l.value?.open || (d.value = null);
		}
		H([
			() => r.value?.metadata.entity_id,
			f,
			y,
			() => t.domain,
			() => t.entityKey,
			() => t.confirmSwitch
		], D, { flush: "sync" }), Qn(D);
		async function O() {
			let e = d.value;
			D(), e && !y.value && n && e.entityId === r.value?.metadata.entity_id && e.sourceState === f.value && e.domain === t.domain && e.key === t.entityKey && await n.perform(t.domain, t.entityKey, e.desired);
		}
		async function ne(e) {
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
					d.value = e, await mn(), d.value === e && !y.value && l.value?.showModal();
					return;
				}
				await n.perform(t.domain, t.entityKey, a);
			}
		}
		async function re(e) {
			let r = e.target, i = r.value;
			r.value = f.value, !y.value && n && await n.perform(t.domain, t.entityKey, i);
		}
		return (t, n) => r.value ? (G(), K("form", {
			key: 0,
			class: N(["entity-control", {
				"entity-control--month": e.monthTile,
				"entity-control--selected": e.monthTile && r.value.available && f.value === "on"
			}]),
			"aria-busy": r.value.pending,
			onSubmit: Ga(E, ["prevent"])
		}, [
			e.monthTile && e.domain === "switch" ? (G(), K("label", {
				key: 0,
				for: a,
				class: "entity-control__switch-target entity-control__month-target"
			}, [q("span", So, I(e.label ?? r.value.name), 1), q("input", {
				id: a,
				type: "checkbox",
				role: "switch",
				checked: r.value.available && f.value === "on",
				indeterminate: !r.value.available || f.value !== "on" && f.value !== "off",
				disabled: y.value,
				"aria-describedby": o,
				onChange: ne
			}, null, 40, Co)])) : (G(), K(W, { key: 1 }, [q("div", wo, [q("label", {
				for: a,
				class: "entity-control__name"
			}, I(e.label ?? r.value.name), 1), e.domain === "switch" ? X("", !0) : (G(), K("p", {
				key: 0,
				id: s,
				class: "entity-control__value"
			}, [e.hideConfirmedLabel ? X("", !0) : (G(), K("span", To, I(v.value.confirmed) + ":", 1)), Y(" " + I(_.value), 1)]))]), q("div", Eo, [e.domain === "switch" ? (G(), K("label", {
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
				onChange: ne
			}, null, 40, Do)])) : e.domain === "select" ? (G(), K("select", {
				key: 1,
				id: a,
				value: r.value.available ? f.value : "",
				disabled: y.value,
				"aria-describedby": g.value,
				onChange: re
			}, [r.value.available ? X("", !0) : (G(), K("option", ko, I(v.value.unavailable), 1)), (G(!0), K(W, null, U(m.value, (e) => (G(), K("option", {
				key: e,
				value: e
			}, I(T(e)), 9, Ao))), 128))], 40, Oo)) : (G(), K(W, { key: 2 }, [q("input", {
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
				onInvalid: Ga(E, ["prevent"])
			}, null, 40, jo), J(bo, null, {
				default: En(() => [q("button", {
					type: "submit",
					disabled: y.value || e.domain === "time" && c.value === ""
				}, I(v.value.apply), 9, Mo), q("button", {
					type: "button",
					disabled: r.value.pending,
					onClick: ee
				}, I(v.value.cancel), 9, No)]),
				_: 1
			})], 64))])], 64)),
			q("div", {
				id: o,
				class: "entity-control__feedback"
			}, [r.value.error ? (G(), K("p", Po, I(r.value.error), 1)) : b.value ? (G(), K("p", Fo, I(b.value), 1)) : X("", !0)]),
			e.confirmSwitch ? (G(), K("dialog", {
				key: 2,
				ref_key: "dialog",
				ref: l,
				class: "entity-control__confirmation",
				"aria-labelledby": `${V(i)}-confirmation-title`,
				"aria-describedby": `${V(i)}-confirmation-question`,
				onCancel: Ga(D, ["prevent"]),
				onClose: te
			}, [
				q("h3", { id: `${V(i)}-confirmation-title` }, I(v.value.confirmationTitle), 9, Lo),
				q("p", { id: `${V(i)}-confirmation-question` }, I(v.value.confirmationQuestion), 9, Ro),
				J(bo, { class: "entity-control__confirmation-actions" }, {
					default: En(() => [q("button", {
						type: "button",
						disabled: y.value || !d.value,
						onClick: O
					}, I(v.value.apply), 9, zo), q("button", {
						type: "button",
						autofocus: "",
						onClick: D
					}, I(v.value.cancel), 1)]),
					_: 1
				})
			], 40, Io)) : X("", !0)
		], 42, xo)) : X("", !0);
	}
}), [["styles", [".entity-control{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));color:var(--primary-text-color,#212121);box-shadow:var(--ha-card-box-shadow,none);flex-wrap:wrap;align-items:center;gap:12px 24px;padding:20px;display:flex}.entity-control__description{overflow-wrap:anywhere;flex:200px;min-width:0}.entity-control__name{font-weight:500;line-height:1.5;display:block}.entity-control__value{color:var(--secondary-text-color,#666);margin:4px 0 0;font-size:.9em;line-height:1.5}.entity-control__input{flex-wrap:wrap;align-items:center;gap:8px;max-width:100%;display:flex}.entity-control__switch-target{cursor:pointer;justify-content:center;align-items:center;min-width:44px;min-height:44px;display:flex}.entity-control__switch-target:has(:disabled){cursor:not-allowed}.entity-control input,.entity-control select,.entity-control button{border:1px solid var(--divider-color,#767676);max-width:100%;min-height:44px;color:inherit;background:var(--card-background-color,#fff);font:inherit;border-radius:6px;padding:8px 12px}.entity-control input[type=number]{width:120px}.entity-control input[type=checkbox]{width:22px;height:22px;min-height:22px;accent-color:var(--primary-color,#03a9f4);cursor:pointer;flex-shrink:0;margin:0;padding:0}.entity-control button{border-color:var(--primary-color,#03a9f4);color:var(--primary-text-color,#212121);cursor:pointer}.entity-control :disabled{cursor:not-allowed;opacity:.6}.entity-control input:focus-visible,.entity-control select:focus-visible,.entity-control button:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.entity-control__feedback{color:var(--secondary-text-color,#666);flex-basis:100%;line-height:1.5}.entity-control__feedback:empty{display:none}.entity-control__feedback p{margin:0}.entity-control__error{color:var(--error-color,#b71c1c)}.entity-control__confirmation{border:1px solid var(--divider-color,#767676);background:var(--card-background-color,#fff);width:min(440px,100vw - 32px);max-height:calc(100vh - 32px);color:var(--primary-text-color,#212121);border-radius:12px;padding:24px;overflow:auto}.entity-control__confirmation::backdrop{background:#0000008c}.entity-control__confirmation h3{margin:0;font-size:20px;line-height:1.4}.entity-control__confirmation p{margin:16px 0 24px;line-height:1.6}.entity-control__confirmation-actions{justify-content:flex-end}@container sax-content (width>=860px){.entity-control{gap:8px 12px;padding:14px}.entity-control__description{flex-basis:140px}.entity-control__value{margin-top:2px;font-size:14px}.entity-control input[type=number]{width:104px}}"]]]), Vo = [
	"role",
	"aria-labelledby",
	"aria-valuemin",
	"aria-valuemax",
	"aria-valuenow",
	"aria-valuetext"
], Ho = {
	viewBox: "0 0 240 124",
	"aria-hidden": "true"
}, Uo = ["stroke-dasharray", "stroke-dashoffset"], Wo = ["transform"], Go = {
	class: "entity-gauge__scale",
	"aria-hidden": "true"
}, Ko = { class: "entity-gauge__value" }, qo = {
	key: 0,
	class: "entity-gauge__range"
}, Jo = /*#__PURE__*/ go(/* @__PURE__ */ Bn({
	__name: "EntityGauge",
	props: {
		entityKey: { type: String },
		maximum: { type: Number },
		segments: { type: Array }
	},
	setup(e) {
		let t = e, n = An(lo), r = Z(() => n?.entity("sensor", t.entityKey)), i = `sax-gauge-${Vn()}`, a = Z(() => {
			let e = r.value?.state?.state.trim();
			if (!r.value?.available || !e) return null;
			let t = Number(e);
			return Number.isFinite(t) ? t : null;
		}), o = Z(() => a.value === null ? null : Math.max(0, Math.min(t.maximum, a.value))), s = Z(() => a.value === null ? null : [...t.segments].reverse().find((e) => a.value >= e.from)?.label ?? t.segments[0]?.label), c = Z(() => r.value?.available && a.value === null ? n?.language.value === "de" ? "Unbekannt" : "Unknown" : r.value?.displayValue), l = Z(() => t.segments.map((e, n) => ({
			...e,
			offset: -(e.from / t.maximum) * 100,
			length: ((t.segments[n + 1]?.from ?? t.maximum) - e.from) / t.maximum * 100
		})));
		return (t, n) => r.value ? (G(), K("section", {
			key: 0,
			class: "entity-gauge",
			"aria-labelledby": i
		}, [q("h2", { id: i }, I(r.value.name), 1), q("div", {
			class: "entity-gauge__meter",
			role: o.value === null ? void 0 : "meter",
			"aria-labelledby": o.value === null ? void 0 : i,
			"aria-valuemin": o.value === null ? void 0 : 0,
			"aria-valuemax": o.value === null ? void 0 : e.maximum,
			"aria-valuenow": o.value ?? void 0,
			"aria-valuetext": o.value === null ? void 0 : `${c.value} · ${s.value}`
		}, [
			(G(), K("svg", Ho, [n[1] ||= q("path", {
				class: "entity-gauge__track",
				d: "M20 110 A100 100 0 0 1 220 110"
			}, null, -1), o.value === null ? X("", !0) : (G(), K(W, { key: 0 }, [
				(G(!0), K(W, null, U(l.value, (e) => (G(), K("path", {
					key: e.from,
					class: N(["entity-gauge__segment", `entity-gauge__segment--${e.color}`]),
					d: "M20 110 A100 100 0 0 1 220 110",
					pathLength: "100",
					"stroke-dasharray": `${e.length} 100`,
					"stroke-dashoffset": e.offset
				}, null, 10, Uo))), 128)),
				q("line", {
					class: "entity-gauge__needle",
					x1: "120",
					y1: "110",
					x2: "120",
					y2: "33",
					transform: `rotate(${o.value / e.maximum * 180 - 90} 120 110)`
				}, null, 8, Wo),
				n[0] ||= q("circle", {
					class: "entity-gauge__pivot",
					cx: "120",
					cy: "110",
					r: "5"
				}, null, -1)
			], 64))])),
			q("div", Go, [n[2] ||= q("span", null, "0", -1), q("span", null, I(e.maximum), 1)]),
			q("p", Ko, I(c.value), 1),
			s.value ? (G(), K("p", qo, I(s.value), 1)) : X("", !0)
		], 8, Vo)])) : X("", !0);
	}
}), [["styles", [".entity-gauge{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);text-align:center;padding:24px}.entity-gauge h2{overflow-wrap:anywhere;margin:0 0 20px;font-size:16px;font-weight:500;line-height:1.5}.entity-gauge__meter{max-width:260px;margin:0 auto}.entity-gauge svg{fill:none;width:100%;display:block}.entity-gauge__track,.entity-gauge__segment{stroke-width:15px;stroke-linecap:butt}.entity-gauge__track{stroke:var(--divider-color,#e0e0e0)}.entity-gauge__segment--red{stroke:var(--error-color,#db4437)}.entity-gauge__segment--yellow{stroke:var(--warning-color,#f4b400)}.entity-gauge__segment--green{stroke:var(--success-color,#0f9d58)}.entity-gauge__needle{stroke:var(--primary-text-color,#212121);stroke-width:3px;stroke-linecap:round}.entity-gauge__pivot{stroke:none;fill:var(--primary-text-color,#212121)}.entity-gauge__scale{color:var(--secondary-text-color,#666);justify-content:space-between;padding:2px 7px;font-size:12px;display:flex}.entity-gauge__value{overflow-wrap:anywhere;margin:10px 0 0;font-size:28px;font-weight:500;line-height:1.4}.entity-gauge__range{color:var(--secondary-text-color,#666);margin:4px 0 0;font-size:14px;line-height:1.5}@container sax-content (width>=860px){.entity-gauge{padding:16px}.entity-gauge h2{margin-bottom:8px}.entity-gauge__meter{max-width:180px}.entity-gauge__value{margin-top:6px;font-size:24px}.entity-gauge__range{margin-top:2px}}"]]]), Yo = {
	key: 0,
	class: "entity-value"
}, Xo = { class: "entity-value__name" }, Zo = { class: "entity-value__state" }, Qo = /*#__PURE__*/ go(/* @__PURE__ */ Bn({
	__name: "EntityValue",
	props: {
		domain: { type: null },
		entityKey: { type: String }
	},
	setup(e) {
		let t = e, n = An(lo), r = Z(() => n?.entity(t.domain, t.entityKey));
		return (e, t) => r.value ? (G(), K("div", Yo, [q("span", Xo, I(r.value.name), 1), q("span", Zo, I(r.value.displayValue), 1)])) : X("", !0);
	}
}), [["styles", [".entity-value{color:var(--primary-text-color,#212121);overflow-wrap:anywhere;flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:8px 20px;line-height:1.5;display:flex}.entity-value__name{color:var(--secondary-text-color,#666)}.entity-value__state{font-weight:500}"]]]), $o = { class: "general-view" }, es = {
	key: 0,
	class: "general-view__status",
	role: "status"
}, ts = {
	key: 1,
	class: "general-view__status",
	role: "status"
}, ns = {
	key: 2,
	class: "general-view__gauges"
}, rs = ["aria-labelledby"], is = ["id"], as = { class: "general-view__rows" }, os = /*#__PURE__*/ go(/* @__PURE__ */ Bn({
	__name: "GeneralView",
	setup(e) {
		let t = An(lo), n = Vn(), r = Z(() => t?.language.value === "de" ? {
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
		return (e, i) => (G(), K("div", $o, [
			!V(t)?.ready.value && !V(t)?.error.value ? (G(), K("p", es, I(r.value.loading), 1)) : V(t)?.ready.value && !s.value ? (G(), K("p", ts, I(r.value.empty), 1)) : X("", !0),
			o.value ? (G(), K("div", ns, [J(Jo, {
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
			}, null, 8, ["segments"]), J(Jo, {
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
			(G(!0), K(W, null, U(a.value, (e) => (G(), K("section", {
				key: e.title,
				class: N(["general-view__card", `general-view__card--${e.title}`]),
				"aria-labelledby": `${V(n)}-${e.title}`
			}, [q("h2", { id: `${V(n)}-${e.title}` }, I(r.value[e.title]), 9, is), q("div", as, [(G(!0), K(W, null, U(e.entities, ([e, t]) => (G(), K(W, { key: `${e}.${t}` }, [e === "number" || e === "switch" ? (G(), oi(Bo, {
				key: 0,
				domain: e,
				"entity-key": t,
				"confirm-switch": e === "switch" && t === "storage_switch"
			}, null, 8, [
				"domain",
				"entity-key",
				"confirm-switch"
			])) : (G(), oi(Qo, {
				key: 1,
				domain: e,
				"entity-key": t
			}, null, 8, ["domain", "entity-key"]))], 64))), 128))])], 10, rs))), 128))
		]));
	}
}), [["styles", [".general-view{gap:20px;min-width:0;margin-top:24px;display:grid}.general-view__gauges{grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr));gap:20px;display:grid}.general-view__card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.general-view__card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.general-view__rows{gap:16px;display:grid}.general-view__rows .entity-control{border:0;border-bottom:1px solid var(--divider-color,#e0e0e0);box-shadow:none;border-radius:0;padding:0 0 16px}.general-view__rows .entity-control:last-child{border-bottom:0;padding-bottom:0}.general-view__status{color:var(--secondary-text-color,#666);margin:0;line-height:1.6}@container sax-content (width>=860px){.general-view{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;gap:16px;margin-top:16px}.general-view__gauges{grid-column:1;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.general-view__gauges:has(>:only-child){grid-template-columns:minmax(0,1fr)}.general-view__card{padding:18px}.general-view__card--power{grid-column:1}.general-view__card--device{grid-area:1/2/span 2}:is(.general-view:not(:has(.general-view__gauges)) .general-view__card--device,.general-view:not(:has(.general-view__card--power)) .general-view__card--device){grid-row:1}:is(.general-view:has(>:only-child),.general-view:not(:has(.general-view__card--device))){grid-template-columns:minmax(0,1fr)}.general-view__card:only-child{grid-area:auto}.general-view__card h2{margin-bottom:12px;font-size:16px}.general-view__rows{gap:10px}.general-view__rows .entity-control{padding:0 0 10px}.general-view__rows .entity-control:last-child{padding-bottom:0}.general-view__status{grid-column:1/-1}}@media (max-width:600px){.general-view,.general-view__gauges{gap:16px}.general-view__card{padding:20px}}"]]]), ss = ["aria-busy"], cs = { class: "month-selection__header" }, ls = {
	class: "month-selection__overview",
	"aria-live": "polite",
	"aria-atomic": "true"
}, us = { class: "month-selection__summary" }, ds = { class: "month-selection__count" }, fs = ["aria-expanded"], ps = { class: "month-selection__feedback" }, ms = {
	key: 0,
	role: "status"
}, hs = {
	key: 1,
	role: "status"
}, gs = {
	key: 2,
	role: "status"
}, _s = {
	key: 3,
	role: "status"
}, vs = {
	key: 0,
	class: "month-selection__hint"
}, ys = { class: "month-selection__quarters" }, bs = { class: "month-selection__options" }, xs = {
	key: 1,
	class: "month-selection__missing"
}, Ss = { class: "month-selection__missing-target" }, Cs = ["aria-describedby"], ws = ["id"], Ts = /*#__PURE__*/ go(/* @__PURE__ */ Bn({
	__name: "MonthSelection",
	props: {
		entityKeys: { type: Array },
		alwaysExpanded: { type: Boolean }
	},
	setup(e) {
		let t = e, n = An(lo), r = /* @__PURE__ */ B(!1), i = Z(() => t.alwaysExpanded || r.value), a = `sax-months-${Vn()}`, o = Z(() => n?.language.value ?? "en"), s = Z(() => o.value === "de" ? {
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
		return (t, o) => (G(), K("div", {
			class: "month-selection",
			"aria-busy": m.value
		}, [
			q("div", cs, [q("div", ls, [q("p", us, I(f.value), 1), q("p", ds, I(p.value), 1)]), e.alwaysExpanded ? X("", !0) : (G(), K("button", {
				key: 0,
				type: "button",
				class: "month-selection__toggle",
				"aria-expanded": r.value,
				"aria-controls": a,
				onClick: o[0] ||= (e) => r.value = !r.value
			}, [Y(I(r.value ? s.value.close : s.value.edit) + " ", 1), (G(), K("svg", {
				viewBox: "0 0 24 24",
				width: "18",
				height: "18",
				"aria-hidden": "true",
				class: N({ "month-selection__chevron--expanded": r.value })
			}, [...o[1] ||= [q("path", { d: "m6 9 6 6 6-6" }, null, -1)]], 2))], 8, fs))]),
			q("div", ps, [
				i.value ? X("", !0) : (G(), K(W, { key: 0 }, [(G(!0), K(W, null, U(h.value, (e) => (G(), K("p", {
					key: e,
					class: "month-selection__error",
					role: "alert"
				}, I(e), 1))), 128)), m.value ? (G(), K("p", ms, I(s.value.pending), 1)) : X("", !0)], 64)),
				V(n)?.connected.value ? X("", !0) : (G(), K("p", hs, I(s.value.disconnected), 1)),
				d.value.length ? (G(), K("p", gs, I(s.value.unknown) + ": " + I(d.value.map((e) => e.name).join(", ")), 1)) : X("", !0),
				g.value.length ? (G(), K("p", _s, I(s.value.readOnly) + ": " + I(g.value.map((e) => e.name).join(", ")), 1)) : X("", !0)
			]),
			Dn(q("div", {
				id: a,
				class: "month-selection__details"
			}, [e.alwaysExpanded ? X("", !0) : (G(), K("p", vs, I(s.value.hint), 1)), q("div", ys, [(G(!0), K(W, null, U(l.value, (e) => (G(), K("fieldset", {
				key: e.index,
				class: "month-selection__quarter"
			}, [q("legend", null, I(e.name), 1), q("div", bs, [(G(!0), K(W, null, U(e.months, (e) => (G(), K(W, { key: e.index }, [e.entity && e.key ? (G(), oi(Bo, {
				key: 0,
				domain: "switch",
				"entity-key": e.key,
				"month-tile": ""
			}, null, 8, ["entity-key"])) : (G(), K("div", xs, [q("label", Ss, [q("span", null, I(e.name), 1), q("input", {
				type: "checkbox",
				role: "switch",
				disabled: "",
				indeterminate: !0,
				"aria-describedby": `${a}-${e.index}-missing`
			}, null, 8, Cs)]), q("p", { id: `${a}-${e.index}-missing` }, I(s.value.unavailable), 9, ws)]))], 64))), 128))])]))), 128))])], 512), [[Zi, i.value]])
		], 8, ss));
	}
}), [["styles", [".month-selection{min-width:0}.month-selection__header{flex-wrap:wrap;justify-content:space-between;align-items:center;gap:16px;display:flex}.month-selection__overview{overflow-wrap:anywhere;flex:180px;min-width:0}.month-selection__summary{margin:0;font-size:16px;font-weight:500;line-height:1.5}.month-selection__count,.month-selection__hint{color:var(--secondary-text-color,#666);margin:4px 0 0;font-size:14px;line-height:1.5}.month-selection__toggle{border:1px solid var(--divider-color,#e0e0e0);background:var(--card-background-color,#fff);min-height:44px;color:var(--primary-text-color,#212121);font:inherit;cursor:pointer;border-radius:8px;flex-shrink:0;justify-content:center;align-items:center;gap:8px;padding:8px 12px;font-size:14px;display:inline-flex}.month-selection__toggle:hover{background:var(--secondary-background-color,#f5f5f5)}:is(.month-selection__toggle:focus-visible,.month-selection .entity-control__month-target:has(input:focus-visible)){outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.month-selection__toggle svg{fill:none;stroke:currentColor;stroke-width:2px;stroke-linecap:round;stroke-linejoin:round}.month-selection__chevron--expanded{transform:rotate(180deg)}.month-selection__details{border-top:1px solid var(--divider-color,#e0e0e0);margin-top:16px;padding-top:16px}.month-selection__hint{margin:0 0 16px}.month-selection__quarters{grid-template-columns:minmax(0,1fr);gap:16px;display:grid}.month-selection__quarter{border:0;min-width:0;margin:0;padding:0}.month-selection__quarter legend{color:var(--secondary-text-color,#666);margin-bottom:8px;padding:0;font-size:13px;font-weight:500}.month-selection__options{grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;display:grid}.month-selection .entity-control.entity-control--month,.month-selection__missing{border:1px solid var(--divider-color,#e0e0e0);background:var(--card-background-color,#fff);border-radius:8px;flex-flow:column;align-items:stretch;gap:0;min-width:0;padding:0;display:flex}.month-selection .entity-control.entity-control--selected{border-color:color-mix(in srgb, var(--primary-color,#03a9f4) 55%, var(--divider-color,#e0e0e0));background:color-mix(in srgb, var(--primary-color,#03a9f4) 12%, var(--card-background-color,#fff))}.month-selection .entity-control__month-target,.month-selection__missing-target{cursor:pointer;border-radius:7px;flex-direction:column-reverse;flex:auto;justify-content:center;align-items:center;gap:8px;min-height:44px;padding:10px 6px;display:flex}.month-selection__missing-target{cursor:not-allowed}.month-selection .entity-control__month-target:has(:disabled){cursor:not-allowed}.month-selection .entity-control__name,.month-selection__missing-target span{text-align:center;overflow-wrap:anywhere;min-width:0;max-width:100%;font-size:14px;font-weight:500;line-height:1.4}.month-selection__missing input[type=checkbox]{width:22px;height:22px;min-height:22px;accent-color:var(--primary-color,#03a9f4);flex-shrink:0;margin:0;padding:0}.month-selection .entity-control__feedback,.month-selection__missing p{overflow-wrap:anywhere;min-width:0;color:var(--secondary-text-color,#666);flex:none;margin:0;padding:0 12px 10px;font-size:13px;line-height:1.5}.month-selection__feedback{color:var(--secondary-text-color,#666);overflow-wrap:anywhere;gap:8px;margin-top:12px;font-size:14px;line-height:1.5;display:grid}.month-selection__feedback:empty{display:none}.month-selection__feedback p{margin:0}.month-selection__error{color:var(--error-color,#b71c1c)}@container sax-content (width>=600px){.month-selection__quarters{grid-template-columns:repeat(2,minmax(0,1fr))}}"]]]);
//#endregion
//#region src/time.ts
function Es(e) {
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
var Ds = ["aria-busy"], Os = { class: "time-window-control__inputs" }, ks = ["for"], As = [
	"id",
	"name",
	"value",
	"disabled",
	"aria-invalid",
	"aria-describedby",
	"onInput",
	"onChange",
	"onBlur"
], js = ["disabled"], Ms = ["disabled"], Ns = ["id"], Ps = ["id"], Fs = ["aria-label"], Is = [
	"disabled",
	"aria-label",
	"aria-valuenow",
	"aria-valuetext",
	"aria-describedby",
	"onKeydown",
	"onPointerdown"
], Ls = {
	class: "time-window-control__marker-label",
	"aria-hidden": "true"
}, Rs = { class: "time-window-control__duration" }, zs = ["id"], Bs = ["id"], Vs = {
	key: 0,
	class: "time-window-control__error",
	role: "alert"
}, Hs = {
	key: 1,
	role: "status"
}, Us = /*#__PURE__*/ go(/* @__PURE__ */ Bn({
	__name: "TimeWindowControl",
	props: { kind: { type: String } },
	setup(e) {
		let t = e, n = An(lo), r = Z(() => n?.entity("time", `${t.kind}_start`)), i = Z(() => n?.entity("time", `${t.kind}_end`)), a = `sax-window-${Vn()}`, o = Z(() => n?.language.value ?? "en"), s = Z(() => o.value === "de" ? {
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
		}), c = /* @__PURE__ */ B(""), l = /* @__PURE__ */ B(""), u = /* @__PURE__ */ B(!1), d = /* @__PURE__ */ B(), f = /* @__PURE__ */ B(), p = /* @__PURE__ */ B(null), m = /* @__PURE__ */ B(!1), h = /* @__PURE__ */ B(!1), g = /* @__PURE__ */ B(!1), _ = 0, v = null;
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
		let S = Z(() => r.value?.state?.state ?? ""), C = Z(() => i.value?.state?.state ?? ""), w = Z(() => !!r.value?.available && !!i.value?.available && $(S.value) !== null && $(C.value) !== null), T = Z(() => typeof r.value?.metadata.device_id == "string" && r.value.metadata.device_id.length > 0 && r.value.metadata.device_id === i.value?.metadata.device_id), ee = Z(() => w.value ? `${b(S.value)} – ${b(C.value)}${s.value.unit ? ` ${s.value.unit}` : ""}` : [r.value, i.value].map((e) => e?.available && $(e.state?.state ?? "") !== null ? `${b(e.state.state)}${s.value.unit ? ` ${s.value.unit}` : ""}` : s.value.missingValue).join(" – ")), E = Z(() => $(c.value) !== null && $(l.value) !== null), D = Z(() => u.value && ($(c.value) !== $(S.value) || $(l.value) !== $(C.value))), te = Z(() => m.value || !!r.value?.pending || !!i.value?.pending), O = Z(() => !n?.ready.value || !n.connected.value || !w.value || !T.value || !r.value?.canControl || !i.value?.canControl || te.value), ne = Z(() => p.value ? `${ae.value.find((e) => e.key === p.value).name}: ${s.value.invalid}` : r.value?.error || i.value?.error), re = Z(() => n?.connected.value ? w.value ? T.value ? !r.value?.canControl || !i.value?.canControl ? s.value.readOnly : te.value ? s.value.pending : h.value ? s.value.awaiting : g.value ? s.value.changed : "" : s.value.incompatible : s.value.unavailable : s.value.disconnected), k = Z(() => u.value || !w.value ? c.value : S.value), ie = Z(() => u.value || !w.value ? l.value : C.value), A = Z(() => {
			let e = $(k.value), t = $(ie.value);
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
		}), j = Z(() => {
			let e = $(k.value), t = $(ie.value);
			return e === null || t === null || e === t ? [] : (t > e ? [[e, t]] : [[e, 86400], [0, t]]).filter(([e, t]) => e !== t).map(([e, t]) => ({
				left: `${e / 864}%`,
				width: `${(t - e) / 864}%`
			}));
		}), ae = Z(() => [{
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
		function oe() {
			let e = v;
			v = null, e?.target.hasPointerCapture?.(e.pointerId) && e.target.releasePointerCapture(e.pointerId);
		}
		H([
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
			let n = typeof t?.[2] == "string" ? t[2] : "", r = typeof t?.[3] == "string" ? t[3] : "", i = u.value && ($(c.value) !== $(n) || $(l.value) !== $(r)), a = te.value || h.value;
			_ += 1, oe(), m.value = !1, h.value = !1, u.value = !1, p.value = null, g.value = !!t?.length && i && !a && w.value, c.value = w.value ? x(S.value) : "", l.value = w.value ? x(C.value) : "";
		}, {
			immediate: !0,
			flush: "sync"
		}), H(O, (e) => {
			e && oe();
		}, { flush: "sync" }), Qn(oe);
		function se(e, t) {
			O.value || (e === "start" ? c.value = t : l.value = t, p.value === e && (p.value = null), u.value = !0, h.value = !1, g.value = !1);
		}
		function ce(e, t) {
			let n = t.target;
			se(e, n.value);
		}
		function le(e) {
			let t = Es(e);
			return $(t) === null ? e : x(t);
		}
		function ue(e) {
			let t = ["start", "end"].map((e) => ({
				boundary: e,
				input: f.value?.querySelector(`[name="${e}"]`)
			}));
			for (let { boundary: n, input: r } of t) {
				if (!r) continue;
				let t = n === "start" ? c.value : l.value, i = !e || n === e ? le(r.value) : r.value;
				(r.value !== t || i !== t) && se(n, i), r.value = i;
			}
		}
		function de(e) {
			O.value || ue(e);
		}
		function fe(e, t) {
			if (O.value) return;
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
			(t.key in r || t.key === "Home" || t.key === "End") && (t.preventDefault(), se(e, x(y(t.key === "Home" ? 0 : t.key === "End" ? 86340 : Math.max(0, Math.min(86340, Math.floor(n / 60) * 60 + r[t.key]))))));
		}
		function pe(e) {
			if (!v || v.pointerId !== e.pointerId || O.value || !d.value) return;
			let t = d.value.getBoundingClientRect();
			if (t.width <= 0 || !v.moved && e.clientX === v.originX) return;
			let n = Math.max(0, Math.min(1439, Math.round(v.originSeconds / 60 + (e.clientX - v.originX) / t.width * 1440)));
			v.moved = !0, se(v.boundary, y(n * 60).slice(0, 5));
		}
		function P(e, t) {
			if (O.value || !E.value || t.button !== 0 || t.isPrimary === !1) return;
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
		function F(e) {
			v?.pointerId === e.pointerId && (v.moved && pe(e), oe());
		}
		function me() {
			if (!te.value) {
				oe(), u.value = !1, p.value = null, g.value = !1, c.value = w.value ? x(S.value) : "", l.value = w.value ? x(C.value) : "";
				for (let e of ae.value) {
					let r = f.value?.querySelector(`[name="${e.key}"]`);
					r && (r.value = e.value), n?.clearControlError("time", `${t.kind}_${e.key}`);
				}
			}
		}
		async function he() {
			if (!n || O.value) return;
			if (ue(), p.value = $(c.value) === null ? "start" : $(l.value) === null ? "end" : null, p.value) {
				f.value?.querySelector(`[name="${p.value}"]`)?.focus();
				return;
			}
			if (!D.value) return;
			let e = _;
			m.value = !0, g.value = !1;
			let r = await n.performTimeWindow(t.kind, `${c.value}:00`, `${l.value}:00`);
			e === _ && (m.value = !1, h.value = r && D.value);
		}
		return (e, t) => r.value || i.value ? (G(), K("form", {
			key: 0,
			ref_key: "form",
			ref: f,
			class: "time-window-control",
			"aria-busy": te.value,
			onSubmit: Ga(he, ["prevent"])
		}, [
			q("div", Os, [(G(!0), K(W, null, U(ae.value, (e) => (G(), K("label", {
				key: e.key,
				for: `${a}-${e.key}`,
				class: "time-window-control__field"
			}, [q("span", null, [Y(I(e.name), 1), s.value.unit ? (G(), K(W, { key: 0 }, [Y(" (" + I(s.value.unit) + ")", 1)], 64)) : X("", !0)]), q("input", {
				id: `${a}-${e.key}`,
				name: e.key,
				type: "text",
				inputmode: "numeric",
				autocomplete: "off",
				placeholder: "HH:MM",
				value: e.value,
				disabled: O.value,
				"aria-invalid": p.value === e.key,
				"aria-describedby": `${a}-time-hint ${a}-confirmed ${a}-status`,
				onInput: (t) => ce(e.key, t),
				onChange: (t) => de(e.key),
				onBlur: (t) => de(e.key)
			}, null, 40, As)], 8, ks))), 128)), J(bo, null, {
				default: En(() => [q("button", {
					class: "time-window-control__apply",
					type: "submit",
					disabled: O.value
				}, I(s.value.apply), 9, js), q("button", {
					class: "time-window-control__cancel",
					type: "button",
					disabled: te.value,
					onClick: me
				}, I(s.value.cancel), 9, Ms)]),
				_: 1
			})]),
			q("p", {
				id: `${a}-time-hint`,
				class: "time-window-control__hint"
			}, I(s.value.timeHint), 9, Ns),
			q("p", {
				id: `${a}-confirmed`,
				class: "time-window-control__confirmed"
			}, I(s.value.confirmed) + ": " + I(ee.value), 9, Ps),
			q("div", {
				class: "time-window-control__timeline",
				"aria-label": s.value.timeline,
				role: "group"
			}, [q("div", {
				ref_key: "rail",
				ref: d,
				class: N(["time-window-control__rail", { "time-window-control__rail--draft": D.value }])
			}, [(G(!0), K(W, null, U(j.value, (e, t) => (G(), K("span", {
				key: t,
				class: "time-window-control__segment",
				style: M(e)
			}, null, 4))), 128))], 2), (G(!0), K(W, null, U(ae.value, (e) => (G(), K("button", {
				key: e.key,
				type: "button",
				role: "slider",
				class: N(["time-window-control__handle", `time-window-control__handle--${e.key}`]),
				style: M({ left: `${(V($)(e.value) ?? 0) / 864}%` }),
				disabled: O.value || !E.value,
				"aria-label": e.marker,
				"aria-valuemin": "0",
				"aria-valuemax": "86340",
				"aria-valuenow": V($)(e.value) ?? 0,
				"aria-valuetext": `${b(e.value)}${s.value.unit ? ` ${s.value.unit}` : ""}`,
				"aria-describedby": `${a}-help ${a}-confirmed`,
				"aria-orientation": "horizontal",
				onKeydown: (t) => fe(e.key, t),
				onPointerdown: (t) => P(e.key, t),
				onPointermove: pe,
				onPointerup: F,
				onPointercancel: oe,
				onLostpointercapture: oe
			}, [q("span", Ls, I(e.shortName), 1), t[0] ||= q("span", {
				class: "time-window-control__marker-dot",
				"aria-hidden": "true"
			}, null, -1)], 46, Is))), 128))], 8, Fs),
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
			q("p", Rs, [q("span", null, I(D.value ? s.value.draft : s.value.duration) + ":", 1), Y(" " + I(A.value), 1)]),
			q("p", {
				id: `${a}-help`,
				class: "time-window-control__sr-only"
			}, I(s.value.help), 9, zs),
			q("div", {
				id: `${a}-status`,
				class: "time-window-control__feedback"
			}, [ne.value ? (G(), K("p", Vs, I(ne.value), 1)) : re.value ? (G(), K("p", Hs, I(re.value), 1)) : X("", !0)], 8, Bs)
		], 40, Ds)) : X("", !0);
	}
}), [["styles", [".time-window-control{min-width:0;color:var(--primary-text-color,#212121)}.time-window-control__inputs{flex-wrap:wrap;align-items:end;gap:10px;display:flex}.time-window-control__field{flex:136px;gap:5px;min-width:0;font-size:14px;display:grid}.time-window-control__field input,.time-window-control__apply,.time-window-control__cancel{box-sizing:border-box;border:1px solid var(--divider-color,#767676);min-width:0;max-width:100%;min-height:44px;color:inherit;background:var(--card-background-color,#fff);font:inherit;border-radius:6px;padding:8px 10px;font-size:16px}.time-window-control__field input{width:100%}.time-window-control__field input[aria-invalid=true]{border-color:var(--error-color,#db4437)}.time-window-control__apply,.time-window-control__cancel{border-color:var(--primary-color,#03a9f4);cursor:pointer;flex:none;padding-inline:7px}.time-window-control__hint,.time-window-control__confirmed,.time-window-control__duration{color:var(--secondary-text-color,#666);overflow-wrap:anywhere;margin:9px 0 0;font-size:14px;line-height:1.5}.time-window-control__timeline{height:94px;margin:6px 22px 0;position:relative}.time-window-control__rail{background:var(--divider-color,#ddd);border-radius:3px;height:6px;position:absolute;top:44px;left:0;right:0;overflow:hidden}.time-window-control__segment{background:var(--primary-color,#03a9f4);height:100%;position:absolute}.time-window-control__rail--draft .time-window-control__segment{background-image:repeating-linear-gradient(135deg,#0000 0 5px,#ffffff3d 5px 8px)}.time-window-control__handle{width:44px;height:44px;min-height:0;color:inherit;font:inherit;cursor:ew-resize;touch-action:none;background:0 0;border:0;border-radius:6px;padding:0;display:block;position:absolute;transform:translate(-50%)}.time-window-control__handle--start{top:0}.time-window-control__handle--end{top:50px}.time-window-control__marker-label{white-space:nowrap;width:max-content;font-size:12px;line-height:16px;position:absolute;left:50%;transform:translate(-50%)}.time-window-control__handle--start .time-window-control__marker-label{top:0}.time-window-control__handle--end .time-window-control__marker-label{bottom:0}.time-window-control__marker-dot{box-sizing:border-box;border:2px solid var(--primary-color,#03a9f4);background:var(--card-background-color,#fff);border-radius:50%;width:18px;height:18px;position:absolute;left:13px}.time-window-control__handle--start .time-window-control__marker-dot{bottom:3px}.time-window-control__handle--end .time-window-control__marker-dot{top:3px}.time-window-control__marker-dot:after{content:\"\";background:var(--primary-color,#03a9f4);width:2px;height:6px;position:absolute;left:6px}.time-window-control__handle--start .time-window-control__marker-dot:after{top:14px}.time-window-control__handle--end .time-window-control__marker-dot:after{bottom:14px}.time-window-control__ticks{height:18px;color:var(--secondary-text-color,#666);margin:0 22px;font-size:12px;position:relative}.time-window-control__ticks span{white-space:nowrap;position:absolute;left:0}.time-window-control__ticks span:nth-child(2){left:25%;transform:translate(-50%)}.time-window-control__ticks span:nth-child(3){left:50%;transform:translate(-50%)}.time-window-control__ticks span:nth-child(4){left:75%;transform:translate(-50%)}.time-window-control__ticks span:last-child{left:auto;right:0}.time-window-control :disabled{opacity:.6;cursor:not-allowed}.time-window-control input:focus-visible,.time-window-control button:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.time-window-control__feedback{color:var(--secondary-text-color,#666);overflow-wrap:anywhere;margin-top:6px;font-size:14px;line-height:1.5}.time-window-control__feedback:empty{display:none}.time-window-control__feedback p{margin:0}.time-window-control__error{color:var(--error-color,#b71c1c)}.time-window-control__sr-only{clip-path:inset(50%);white-space:nowrap;border:0;width:1px;height:1px;margin:-1px;padding:0;position:absolute;overflow:hidden}"]]]), Ws = { class: "charging-view" }, Gs = {
	key: 0,
	class: "charging-view__status",
	role: "status"
}, Ks = {
	key: 1,
	class: "charging-view__status",
	role: "status"
}, qs = {
	key: 3,
	class: "charging-view__cards"
}, Js = ["aria-labelledby"], Ys = ["id"], Xs = /*#__PURE__*/ go(/* @__PURE__ */ Bn({
	__name: "ChargingLayout",
	props: {
		switchKey: { type: String },
		cards: { type: Array }
	},
	setup(e) {
		let t = e, n = An(lo), r = Vn(), i = Z(() => n?.language.value ?? "en"), a = Z(() => t.cards.map((e) => {
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
		return (t, c) => (G(), K("div", Ws, [
			!V(n)?.ready.value && !V(n)?.error.value ? (G(), K("p", Gs, I(s.value.loading), 1)) : V(n)?.ready.value && !o.value && !a.value.length ? (G(), K("p", Ks, I(s.value.empty), 1)) : X("", !0),
			o.value ? (G(), oi(Bo, {
				key: 2,
				domain: "switch",
				"entity-key": e.switchKey
			}, null, 8, ["entity-key"])) : X("", !0),
			a.value.length ? (G(), K("div", qs, [(G(!0), K(W, null, U(a.value, (e) => (G(), K("section", {
				key: e.key,
				class: "charging-view__card",
				"aria-labelledby": `${V(r)}-${e.key}`
			}, [
				q("h2", { id: `${V(r)}-${e.key}` }, I(e.title[i.value]), 9, Ys),
				e.showTimeWindow && e.timeWindow ? (G(), oi(Us, {
					key: 0,
					kind: e.timeWindow
				}, null, 8, ["kind"])) : X("", !0),
				er(t.$slots, `${e.key}-settings`),
				e.entities.length ? (G(), K("div", {
					key: 1,
					class: N(["charging-view__rows", {
						"charging-view__rows--columns": e.layout === "columns",
						"charging-view__rows--months": e.layout === "months"
					}])
				}, [e.layout === "months" ? (G(), oi(Ts, {
					key: 0,
					"entity-keys": e.entities.map(([, e]) => e)
				}, null, 8, ["entity-keys"])) : (G(!0), K(W, { key: 1 }, U(e.entities, ([e, t]) => (G(), K(W, { key: `${e}.${t}` }, [e === "switch" || e === "number" || e === "time" || e === "select" ? (G(), oi(Bo, {
					key: 0,
					domain: e,
					"entity-key": t
				}, null, 8, ["domain", "entity-key"])) : (G(), oi(Qo, {
					key: 1,
					domain: e,
					"entity-key": t
				}, null, 8, ["domain", "entity-key"]))], 64))), 128))], 2)) : X("", !0)
			], 8, Js))), 128))])) : X("", !0)
		]));
	}
}), [["styles", [".charging-view{gap:20px;min-width:0;margin-top:24px;display:grid}.charging-view__cards{align-content:start;gap:20px;min-width:0;display:grid}.charging-view__card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.charging-view__card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.charging-view__rows{gap:16px;display:grid}.charging-view__card>.time-window-control+.charging-view__rows{border-top:1px solid var(--divider-color,#e0e0e0);margin-top:20px;padding-top:16px}.charging-view__rows>.entity-control{border:0;border-bottom:1px solid var(--divider-color,#e0e0e0);box-shadow:none;border-radius:0;padding:0 0 16px}.charging-view__rows>.entity-control:last-child{border-bottom:0;padding-bottom:0}.charging-view__status{color:var(--secondary-text-color,#666);margin:0;line-height:1.6}@media (max-width:600px){.charging-view,.charging-view__cards{gap:16px}.charging-view__card{padding:20px}}@container sax-content (width>=860px){.charging-view{gap:14px;margin-top:16px}.charging-view__cards{align-items:start;gap:16px}.charging-view__card{padding:18px}.charging-view__card h2{margin-bottom:12px;font-size:16px}.charging-view__rows{gap:12px}.charging-view__rows>.entity-control{gap:8px 12px;padding-bottom:12px}.charging-view__rows>.entity-control:last-child{padding-bottom:0}.charging-view__rows>.entity-control .entity-control__description{flex-basis:120px}.charging-view__rows--columns{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;column-gap:24px}.charging-view__rows--columns>:last-child:nth-child(odd){grid-column:1/-1}.charging-view__rows--columns .entity-value{min-height:44px;padding-block:8px}}"]]]), Zs = { class: "sensor-picker" }, Qs = [
	"value",
	"disabled",
	"name",
	"aria-invalid",
	"aria-describedby"
], $s = { value: "" }, ec = ["value"], tc = /*#__PURE__*/ go(/* @__PURE__ */ Bn({
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
		return (t, n) => (G(), K("label", Zs, [Y(I(e.label), 1), q("select", {
			value: e.modelValue ?? "",
			disabled: e.disabled,
			name: e.name,
			"aria-invalid": e.invalid || void 0,
			"aria-describedby": e.describedBy,
			onChange: n[0] ||= (e) => r("update:modelValue", e.target.value || null)
		}, [q("option", $s, I(e.hass?.language?.startsWith("de") ? "Nicht konfiguriert" : "Not configured"), 1), (G(!0), K(W, null, U(i.value, (e) => (G(), K("option", {
			key: e.id,
			value: e.id
		}, I(e.name), 9, ec))), 128))], 40, Qs)]));
	}
}), [["styles", [".sensor-picker{flex-direction:column;gap:6px;min-width:0;font-size:14px;display:flex}.sensor-picker select{width:100%;min-width:0;max-width:100%;min-height:44px;font:inherit;color:var(--primary-text-color,#222);background:var(--card-background-color,#fff);border:1px solid var(--divider-color,#ccc);border-radius:6px;padding:10px}"]]]), nc = ["aria-labelledby", "aria-busy"], rc = { class: "grid-serving-source__header" }, ic = ["id"], ac = {
	key: 0,
	class: "grid-serving-source__confirmed"
}, oc = ["disabled"], sc = ["id"], cc = { key: 0 }, lc = { key: 1 }, uc = {
	key: 2,
	role: "status"
}, dc = {
	key: 3,
	role: "status"
}, fc = ["id"], pc = ["disabled"], mc = ["disabled"], hc = ["disabled"], gc = /*#__PURE__*/ go(/* @__PURE__ */ Bn({
	__name: "GridServingForecastSource",
	props: { hass: { type: Object } },
	setup(e) {
		let t = e, n = An(lo), r = `grid-serving-source-${Vn()}`, i = /* @__PURE__ */ B(), a = /* @__PURE__ */ B(), o = /* @__PURE__ */ B(null), s = /* @__PURE__ */ B(null), c = /* @__PURE__ */ B(""), l = /* @__PURE__ */ B(!1), u = /* @__PURE__ */ B(null), d = /* @__PURE__ */ B(null), f = /* @__PURE__ */ B(!1), p = !1, m = !1;
		Qn(() => {
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
					p || (u.value = null, m ? (m = !1, x(e)) : e && l.value ? (await mn(), i.value?.querySelector("select")?.focus()) : f.value && !l.value && (await mn(), a.value?.focus()));
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
					p || (u.value = null, m ? (m = !1, x()) : f.value && (await mn(), a.value?.focus()));
				}
			}
		}
		async function C() {
			u.value || (l.value = !1, d.value = null, await mn(), a.value?.focus());
		}
		function w() {
			u.value ? m = !0 : x();
		}
		return H([h, () => n?.ready.value], ([e, t]) => {
			e && t && (!l.value || u.value) && w();
		}, { immediate: !0 }), H(() => n?.entity("sensor", "grid_serving_forecast")?.state?.attributes.source_entity_id, (e, t) => {
			e !== t && n?.ready.value && w();
		}), (e, t) => (G(), K("section", {
			ref_key: "section",
			ref: i,
			class: "grid-serving-source",
			"aria-labelledby": `${r}-title`,
			"aria-busy": !!u.value
		}, [
			q("div", rc, [q("div", null, [q("h3", { id: `${r}-title` }, I(g.value.title), 9, ic), o.value ? (G(), K("p", ac, I(v.value), 1)) : X("", !0)]), o.value?.can_edit && !l.value ? (G(), K("button", {
				key: 0,
				ref_key: "editButton",
				ref: a,
				type: "button",
				disabled: !!u.value || !h.value,
				onClick: t[0] ||= (e) => x(!0)
			}, I(g.value.edit), 9, oc)) : X("", !0)]),
			q("p", { id: `${r}-hint` }, I(g.value.hint), 9, sc),
			o.value && !o.value.pv_sensor && !l.value ? (G(), K("p", cc, I(g.value.missing), 1)) : X("", !0),
			o.value && !o.value.can_edit ? (G(), K("p", lc, I(g.value.readonly), 1)) : X("", !0),
			u.value ? (G(), K("p", uc, I(u.value === "loading" ? g.value.loading : g.value.saving), 1)) : X("", !0),
			f.value ? (G(), K("p", dc, I(g.value.saved), 1)) : X("", !0),
			_.value ? (G(), K("p", {
				key: 4,
				id: `${r}-error`,
				class: "grid-serving-source__error",
				role: "alert"
			}, I(_.value), 9, fc)) : X("", !0),
			d.value === "conflict" || !o.value && _.value ? (G(), K("button", {
				key: 5,
				type: "button",
				disabled: !!u.value || !h.value,
				onClick: t[1] ||= (e) => x(l.value)
			}, I(g.value.reload), 9, pc)) : X("", !0),
			l.value ? (G(), K("form", {
				key: 6,
				onSubmit: Ga(S, ["prevent"])
			}, [J(tc, {
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
			]), J(bo, null, {
				default: En(() => [q("button", {
					type: "submit",
					disabled: !!u.value || !h.value || !o.value?.can_edit || d.value === "conflict"
				}, I(g.value.save), 9, mc), q("button", {
					type: "button",
					disabled: !!u.value,
					onClick: C
				}, I(g.value.cancel), 9, hc)]),
				_: 1
			})], 32)) : X("", !0)
		], 8, nc));
	}
}), [["styles", [".grid-serving-source{border-block:1px solid var(--divider-color,#ddd);gap:12px;min-width:0;margin-block:20px;padding-block:16px;display:grid}.grid-serving-source__header{justify-content:space-between;align-items:start;gap:12px;display:flex}.grid-serving-source__header>div{min-width:0}.grid-serving-source h3{margin:0 0 6px;font-size:16px;font-weight:500}.grid-serving-source p{color:var(--secondary-text-color,#666);overflow-wrap:anywhere;margin:0;font-size:14px;line-height:1.6}.grid-serving-source .grid-serving-source__confirmed{color:var(--primary-text-color,#222)}.grid-serving-source .grid-serving-source__error{color:var(--error-color,#b00020)}.grid-serving-source form{gap:12px;display:grid}.grid-serving-source button{border:1px solid var(--divider-color,#ccc);min-height:44px;color:var(--primary-color,#0077a3);background:var(--card-background-color,#fff);font:inherit;cursor:pointer;border-radius:6px;padding:8px 10px}.grid-serving-source button:disabled{opacity:.5;cursor:default}.grid-serving-source button:focus-visible{outline:2px solid var(--primary-color,#0077a3);outline-offset:2px}"]]]), _c = /* @__PURE__ */ Bn({
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
		return (n, r) => (G(), oi(Xs, {
			"switch-key": "grid_serving_enabled",
			cards: t
		}, {
			"pause-settings": En(() => [J(gc, { hass: e.hass }, null, 8, ["hass"])]),
			_: 1
		}));
	}
}), vc = ["aria-labelledby"], yc = ["id"], bc = { key: 0 }, xc = { key: 1 }, Sc = { key: 2 }, Cc = {
	key: 3,
	class: "charge-plan__target"
}, wc = /*#__PURE__*/ go(/* @__PURE__ */ Bn({
	__name: "ChargePlan",
	props: { hass: { type: Object } },
	setup(e) {
		let t = e, n = An(lo), r = Vn(), i = Z(() => n?.language.value === "de"), a = Z(() => n?.entity("sensor", "bridge_charge_plan")), o = Z(() => n?.entity("switch", "bridge_charge_enabled")), s = Z(() => a.value?.state?.attributes ?? {}), c = Z(() => n?.entity("sensor", "discharge_forecast")), l = Z(() => {
			switch (o.value?.state?.attributes.configuration_error) {
				case "bridge_pv_start_required": return i.value ? "Zum Einschalten unter „Preise & Zeiten“ eine PV-Prognosequelle auswählen." : "To enable planning, select a PV forecast source under “Prices & times”.";
				case "bridge_tariff_required": return i.value ? "Zum Einschalten unter „Preise & Zeiten“ einen zeitvariablen Tarif einrichten." : "To enable planning, configure a time-of-use tariff under “Prices & times”.";
				default: return null;
			}
		}), u = Z(() => i.value ? {
			title: "Ladeplanung",
			unavailable: "Die Ladeplanung ist derzeit nicht verfügbar.",
			incomplete: "Die Angaben zum Ladeplan sind noch unvollständig. Ladezeiten können derzeit nicht angezeigt werden.",
			off: "Die verbrauchsabhängige Ladeplanung ist ausgeschaltet.",
			waiting_for_data: "Für die Ladeplanung werden noch gültige Verbrauchsdaten und ein PV-Start benötigt. Die Verbrauchsprognose benötigt mindestens eine Minute Beobachtungszeit.",
			paused: "Die Ladeplanung ist pausiert. Die geplante Netzladung ist derzeit nicht freigegeben.",
			complete: "Die geplante Netzladung ist abgeschlossen.",
			completionPending: "Die geplante Netzladung ist beendet. Für die Abschlussbewertung fehlen aktuelle Batteriemesswerte; die Fehlmenge ist noch unbekannt.",
			completedInsufficient: "Die geplante Netzladung ist beendet. Die verbleibende Speicherenergie reicht voraussichtlich nicht bis zum geplanten PV-Start.",
			not_needed: "Eine Netzladung ist derzeit nicht erforderlich.",
			insufficient: "Die mögliche Netzladung reicht voraussichtlich nicht aus, um die Zeit bis zum PV-Start vollständig zu überbrücken."
		} : {
			title: "Charging plan",
			unavailable: "The charging plan is currently unavailable.",
			incomplete: "The charging plan is still incomplete. Charging times cannot currently be displayed.",
			off: "Consumption-based charging planning is turned off.",
			waiting_for_data: "Charging planning is waiting for valid consumption data and a PV start. The consumption forecast needs at least one minute of observations.",
			paused: "The charging plan is paused. Planned grid charging is currently not permitted.",
			complete: "The planned grid charging is complete.",
			completionPending: "The planned grid charging has ended. Completion assessment needs current battery measurements; the shortfall is still unknown.",
			completedInsufficient: "The planned grid charging has ended. The remaining battery energy is not expected to last until the planned PV start.",
			not_needed: "No grid charging is currently needed.",
			insufficient: "The available grid charging is not expected to cover the entire period until PV starts."
		}), d = Z(() => a.value?.available ? a.value.state?.state : "unavailable"), f = Z(() => i.value ? {
			pv_start_missing: "Die gewählte PV-Prognose liefert noch keinen Zeitraum, der den Verbrauch mindestens 30 Minuten lang deckt. Bitte die PV-Prognosequelle unter „Preise & Zeiten“ prüfen.",
			consumption_missing: "Für die Verbrauchsprognose wird mindestens eine Minute Entlademessung benötigt.",
			measurements_missing: "Aktuelle Batteriemesswerte fehlen.",
			calibration: "Die Batteriekalibrierung hat Vorrang.",
			pv_surplus: "PV-Überschuss pausiert die geplante Netzladung.",
			manual_charge: "Die manuelle Ladung hat Vorrang.",
			disabled: "Unter „Netzladung“ die Ladeweise „Nur Bedarf bis Solarstrom“ wählen und die Automatik einschalten."
		} : {
			pv_start_missing: "The selected PV forecast does not yet provide a period covering consumption for at least 30 minutes. Check the PV forecast source under “Prices & times”.",
			consumption_missing: "The consumption forecast needs at least one minute of discharge measurements.",
			measurements_missing: "Current battery measurements are missing.",
			calibration: "Battery calibration takes priority.",
			pv_surplus: "PV surplus pauses planned grid charging.",
			manual_charge: "Manual charging takes priority.",
			disabled: "Under “Grid charging”, choose “Only what is needed until solar power” and turn on automatic charging."
		}), p = Z(() => typeof s.value.reason == "string" ? f.value[s.value.reason] : void 0);
		function m(e, n, r, i = 1) {
			let a = Q(e);
			return a !== null && a >= n && a <= r ? ro(a, t.hass, i) : null;
		}
		function h(e) {
			return typeof e == "string" && /^\d{4}-\d{2}-\d{2}T.+(?:Z|[+-]\d{2}:\d{2})$/.test(e) ? io(e, t.hass) : null;
		}
		let g = Z(() => {
			if (!c.value?.available) return null;
			let e = c.value.state, t = h(e?.state), n = m(e?.attributes.observation_minutes, 1, 60), r = m(e?.attributes.average_discharge_w, Number.MIN_VALUE, Infinity, 0);
			return !t || !n || !r ? null : i.value ? `Bei durchschnittlich ${r} W Verbrauch in den letzten ${n} Minuten reicht der Speicher voraussichtlich bis ${t} Uhr.` : `With average consumption of ${r} W over the last ${n} minutes, the battery is expected to last until ${t}.`;
		}), _ = Z(() => ({
			discharge: h(s.value.discharge_at),
			start: h(s.value.charge_start),
			end: h(s.value.charge_end),
			pv: h(s.value.pv_start)
		})), v = Z(() => [
			"waiting_for_data",
			"complete",
			"insufficient"
		].includes(d.value ?? "") && h(s.value.completed_at) !== null), y = Z(() => {
			if (!v.value) return null;
			switch (s.value.data_gap_reason) {
				case "pv_start_missing": return i.value ? "Während der Ladung war die PV-Prognose zeitweise nicht verfügbar." : "The PV forecast was temporarily unavailable during charging.";
				case "measurements_missing": return i.value ? "Während der Ladung waren Batteriemesswerte zeitweise nicht verfügbar." : "Battery measurements were temporarily unavailable during charging.";
				default: return null;
			}
		}), b = Z(() => {
			let e = h(s.value.completion_evaluated_at);
			return !v.value || !e ? null : i.value ? `Bewertet am ${e} Uhr anhand aktueller Batteriemesswerte.` : `Assessed at ${e} using current battery measurements.`;
		}), x = Z(() => {
			if (g.value) return null;
			let e = m(s.value.observation_minutes, 1, 60);
			if (!e || !_.value.discharge) return null;
			let t = m(s.value.average_discharge_w, 0, Infinity, 0);
			return i.value ? `Aufgrund des Verbrauchs der letzten ${e} Minuten${t ? ` (durchschnittlich ${t} W)` : ""} wird der Speicher voraussichtlich bis ${_.value.discharge} Uhr entleert sein.` : `Based on consumption over the last ${e} minutes${t ? ` (an average of ${t} W)` : ""}, the battery is expected to be depleted by ${_.value.discharge}.`;
		}), S = Z(() => {
			let { start: e, end: t, pv: n } = _.value, r = d.value === "charging" && (Q(s.value.shortfall_kwh) ?? 0) > 0;
			switch (r ? "insufficient" : d.value) {
				case "planned":
				case "charging": {
					if (!e || !t || !n) return [u.value.incomplete];
					let r = d.value === "charging", a = i.value ? `${r ? "Die Niedertarifladung läuft seit" : x.value ? "Daher beginnt die Aufladung im Niedertarif um" : "Die Aufladung im Niedertarif beginnt um"} ${e} Uhr und dauert voraussichtlich bis ${t} Uhr, um die Zeit bis zum PV-Start um ${n} Uhr zu überbrücken.` : `${r ? "Low-tariff charging has been running since" : x.value ? "Therefore, low-tariff charging will start at" : "Low-tariff charging will start at"} ${e} and is expected to continue until ${t}, to cover consumption until PV starts at ${n}.`;
					return [x.value, a];
				}
				case "not_needed": return [x.value, n ? i.value ? `Eine Netzladung ist nicht erforderlich: Der Speicher reicht voraussichtlich bis zum PV-Start um ${n} Uhr.` : `No grid charging is needed: the battery is expected to last until PV starts at ${n}.` : u.value.not_needed];
				case "insufficient": {
					let a = m(s.value.shortfall_kwh, 0, Infinity, 2), o = a ? i.value ? ` Voraussichtlicher Fehlbetrag: ${a} kWh.` : ` Expected shortfall: ${a} kWh.` : "";
					if (v.value) return [u.value.completedInsufficient + o];
					let c = e && t ? i.value ? r ? `Eine teilweise Aufladung im Niedertarif läuft seit ${e} Uhr bis voraussichtlich ${t} Uhr.` : `Eine teilweise Aufladung im Niedertarif ist von ${e} Uhr bis voraussichtlich ${t} Uhr geplant.` : r ? `Partial low-tariff charging has been running since ${e} and is expected to continue until ${t}.` : `Partial low-tariff charging is planned from ${e} until approximately ${t}.` : null, l = n ? i.value ? `Der PV-Start wird für ${n} Uhr erwartet.` : `PV is expected to start at ${n}.` : null;
					return [
						x.value,
						u.value.insufficient + o,
						c,
						l
					];
				}
				case "off": return [u.value.off, p.value ?? f.value.disabled];
				case "waiting_for_data": return [v.value ? u.value.completionPending : p.value ?? u.value.waiting_for_data];
				case "paused": return [u.value.paused, p.value];
				case "complete": return [u.value.complete];
				default: return [u.value.unavailable];
			}
		}), C = Z(() => [g.value, ...S.value].filter(Boolean).join(" ")), w = Z(() => {
			if (v.value || ![
				"planned",
				"charging",
				"insufficient"
			].includes(d.value ?? "")) return null;
			let e = m(s.value.target_soc, 0, 100);
			return e ? i.value ? `Geplantes Netzladeziel: ${e} %.` : `Planned grid charge target: ${e} %.` : null;
		});
		return (e, t) => a.value || o.value || g.value ? (G(), K("section", {
			key: 0,
			class: "charge-plan",
			"aria-labelledby": `${V(r)}-charge-plan`
		}, [
			q("h2", { id: `${V(r)}-charge-plan` }, I(u.value.title), 9, yc),
			l.value ? (G(), K("p", bc, I(l.value), 1)) : X("", !0),
			q("p", { class: N(["charge-plan__description", { "charge-plan__forecast": g.value }]) }, I(C.value), 3),
			y.value ? (G(), K("p", xc, I(y.value), 1)) : X("", !0),
			b.value ? (G(), K("p", Sc, I(b.value), 1)) : X("", !0),
			w.value ? (G(), K("p", Cc, I(w.value), 1)) : X("", !0)
		], 8, vc)) : X("", !0);
	}
}), [["styles", [".charge-plan{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.charge-plan h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.charge-plan p{overflow-wrap:anywhere;line-height:1.6}.charge-plan p:last-child{margin-bottom:0}.charge-plan__target{color:var(--secondary-text-color,#666)}@media (max-width:600px){.charge-plan{padding:20px}}@container sax-content (width>=860px){.charge-plan{padding:18px}.charge-plan h2{margin-bottom:12px;font-size:16px}}"]]]), Tc = ["aria-labelledby"], Ec = { class: "tariff-plan__header" }, Dc = ["id"], Oc = [
	"disabled",
	"aria-expanded",
	"aria-controls"
], kc = ["disabled"], Ac = {
	key: 0,
	role: "status"
}, jc = {
	key: 1,
	class: "tariff-plan__introduction"
}, Mc = {
	key: 2,
	class: "tariff-plan__price-highlights"
}, Nc = {
	key: 0,
	class: "tariff-plan__low-status"
}, Pc = {
	key: 3,
	class: "tariff-plan__compact-summary"
}, Fc = {
	key: 0,
	class: "tariff-plan__periods"
}, Ic = { key: 0 }, Lc = { key: 1 }, Rc = { class: "tariff-plan__period-price" }, zc = {
	key: 0,
	class: "tariff-plan__badge"
}, Bc = { key: 1 }, Vc = { class: "tariff-plan__base-row" }, Hc = { class: "tariff-plan__period-price" }, Uc = {
	key: 0,
	class: "tariff-plan__badge"
}, Wc = { class: "tariff-plan__feed-row" }, Gc = {
	key: 2,
	class: "tariff-plan__period-status"
}, Kc = {
	key: 3,
	class: "tariff-plan__pending-status"
}, qc = {
	key: 4,
	class: "tariff-plan__low-unavailable"
}, Jc = { class: "tariff-plan__impact" }, Yc = {
	key: 4,
	role: "status"
}, Xc = ["id"], Zc = ["id", "aria-busy"], Qc = { key: 0 }, $c = ["disabled"], el = { class: "tariff-plan__hint" }, tl = { class: "tariff-plan__step" }, nl = ["aria-describedby"], rl = ["id"], il = { class: "tariff-plan__step" }, al = { class: "tariff-plan__hint" }, ol = ["id"], sl = {
	key: 0,
	class: "tariff-plan__empty"
}, cl = { class: "tariff-plan__window-name" }, ll = [
	"onUpdate:modelValue",
	"name",
	"aria-invalid",
	"aria-describedby",
	"onInput",
	"onChange",
	"aria-label"
], ul = [
	"onUpdate:modelValue",
	"name",
	"aria-invalid",
	"aria-describedby",
	"onInput",
	"onChange",
	"aria-label"
], dl = ["onUpdate:modelValue", "aria-label"], fl = ["aria-label", "onClick"], pl = {
	key: 2,
	class: "tariff-plan__hint"
}, ml = { class: "tariff-plan__step" }, hl = ["aria-describedby"], gl = ["id"], _l = ["open"], vl = { class: "tariff-plan__hint" }, yl = { class: "tariff-plan__impact" }, bl = { class: "tariff-plan__actions" }, xl = ["disabled"], Sl = ["disabled"], Cl = ["disabled"], wl = {
	key: 7,
	class: "tariff-plan__overview"
}, Tl = { class: "tariff-plan__current-price" }, El = {
	key: 0,
	class: "tariff-plan__low-status"
}, Dl = {
	key: 1,
	class: "tariff-plan__low-unavailable"
}, Ol = { key: 8 }, kl = {
	key: 9,
	class: "tariff-plan__details tariff-plan__all-prices"
}, Al = ["aria-label"], jl = { class: "tariff-plan__table" }, Ml = { scope: "col" }, Nl = { scope: "col" }, Pl = { scope: "col" }, Fl = { scope: "col" }, Il = { colspan: "2" }, Ll = { key: 0 }, Rl = { key: 0 }, zl = { class: "tariff-plan__details" }, Bl = /*#__PURE__*/ go(/* @__PURE__ */ Bn({
	__name: "TariffPlan",
	props: {
		hass: { type: Object },
		compact: { type: Boolean }
	},
	emits: ["saved", "editing"],
	setup(e, { emit: t }) {
		let n = e, r = t, i = An(lo), a = Vn(), o = Z(() => i?.language.value === "de" ? {
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
		}), s = Z(() => i?.entity("sensor", "economics_current_import_price")), c = (e) => {
			let t = Q(e), r = ro(t === null ? null : t * 100, n.hass, 2);
			return r === null ? o.value.unavailable : `${r} ct/kWh`;
		}, l = Z(() => {
			let e = ro(s.value?.state?.state, n.hass, 2);
			return e === null ? o.value.unavailable : `${e} ct/kWh`;
		}), u = (e) => io(e, n.hass) ?? o.value.unavailable, d = /* @__PURE__ */ B(null), f = /* @__PURE__ */ B({});
		H(() => s.value?.state?.attributes, (e) => {
			e && (f.value = e);
		}, { immediate: !0 });
		let p = Z(() => s.value?.state?.attributes ?? (i?.connected.value ? {} : f.value)), m = /* @__PURE__ */ B(null);
		function h(e) {
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
		function g() {
			let e = d.value, t = h(p.value);
			e && t && (t === h({
				tariff_type: e.tariff_type,
				base_price_eur_kwh: e.base_price_ct_kwh === null ? null : e.base_price_ct_kwh / 100,
				feed_in_price_eur_kwh: e.feed_in_price_ct_kwh === null ? null : e.feed_in_price_ct_kwh / 100,
				windows: e.windows.map((e) => ({
					...e,
					price_eur_kwh: e.price_ct_kwh / 100
				}))
			}) || t !== m.value) && (d.value = null);
		}
		H(p, g);
		let _ = !1;
		Qn(() => {
			_ = !0;
		}), H([() => i?.ready.value, () => p.value.tariff_type], ([e, t]) => {
			e && !t && !i?.tariff.value && i?.loadTariff().catch(() => {});
		}, { immediate: !0 });
		let v = Z(() => {
			let e = d.value ?? (n.compact || !p.value.tariff_type ? i?.tariff.value : null);
			if (!e) return p.value;
			let t = {
				...p.value,
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
			return h(t) === h(p.value) ? p.value : t;
		}), y = Z(() => h(v.value) === h(p.value)), b = Z(() => v.value.tariff_type === "time_of_use"), x = Z(() => Array.isArray(v.value.windows) ? v.value.windows.filter((e) => !!e && typeof e == "object" && typeof e.start == "string" && typeof e.end == "string") : []), S = Z(() => v.value.unavailable_reason), C = Z(() => s.value?.available === !0 && Q(s.value.state?.state) !== null && S.value == null && !d.value), w = Z(() => C.value && Q(v.value.low_tariff_price_eur_kwh) !== null && typeof v.value.low_tariff_active == "boolean" && (v.value.low_tariff_active === !1 || T.value !== null) && typeof v.value.base_price_is_low_tariff == "boolean" && Array.isArray(v.value.windows) && x.value.length === v.value.windows.length && x.value.every((e) => typeof e.low_tariff == "boolean" && Q(e.price_eur_kwh) !== null)), T = Z(() => io(v.value.low_tariff_valid_until, n.hass)), ee = Z(() => w.value && v.value.low_tariff_active === !0 && T.value !== null), E = (e) => w.value && e.low_tariff === !0, D = Z(() => w.value && v.value.base_price_is_low_tariff === !0), te = (e, t) => [e ? o.value.now : "", t ? o.value.low : ""].filter(Boolean).join(" · "), O = Z(() => {
			let e = v.value.active_window;
			return e && typeof e == "object" ? e : null;
		}), ne = (e) => C.value && Q(e.price_eur_kwh) !== null && O.value?.start === e.start && O.value?.end === e.end, re = Z(() => C.value && O.value === null && Q(v.value.base_price_eur_kwh) !== null), k = (e) => io(`2000-01-01T${e.length === 5 ? `${e}:00` : e}Z`, n.hass, {
			timeStyle: "short",
			timeZone: "UTC"
		}) ?? e.slice(0, 5);
		function ie(e) {
			let t = $(e.start), n = $(e.end);
			if (t === null || n === null || t === n) return null;
			let r = Math.floor((n - t + 86400) % 86400 / 60), a = Math.floor(r / 60), o = r % 60, s = i?.language.value === "de";
			return [a && `${a} ${s ? a === 1 ? "Stunde" : "Stunden" : a === 1 ? "hour" : "hours"}`, (o || !a) && `${o} ${s ? o === 1 ? "Minute" : "Minuten" : o === 1 ? "minute" : "minutes"}`].filter((e) => typeof e == "string").join(" ");
		}
		let A = /* @__PURE__ */ B(!1);
		H(A, (e) => r("editing", e));
		let j = /* @__PURE__ */ B(!1), ae = /* @__PURE__ */ B("loading"), oe = /* @__PURE__ */ B(), se = /* @__PURE__ */ B(), M = /* @__PURE__ */ B(null), ce = /* @__PURE__ */ B(""), le = /* @__PURE__ */ B(""), ue = /* @__PURE__ */ B(null), de = Z(() => i?.entity("switch", "bridge_charge_enabled")?.state?.state === "on"), fe = /* @__PURE__ */ B([]), pe = 0, P = /* @__PURE__ */ B(null), F = /* @__PURE__ */ B(null), me = /* @__PURE__ */ B(!1), he = /* @__PURE__ */ B(!1), ge = Z(() => i?.connected.value === !0 && i.ready.value), _e = Z(() => {
			if (P.value === "timeError" && F.value) {
				let e = fe.value.findIndex((e) => e.key === F.value.key);
				return `${o.value.window} ${e + 1}: ${o.value[F.value.reason]}`;
			}
			return P.value ? o.value[P.value] : null;
		});
		function ve(e, t) {
			return oe.value?.querySelector(`[name="window_${e}_${t}"]`);
		}
		function ye(e, t, n) {
			let r = fe.value.find((t) => t.key === e), i = n.target;
			r && (i.value = r[t] = Es(i.value)), L(e);
		}
		function L(e) {
			(e === void 0 || F.value?.key === e) && (F.value = null, P.value === "timeError" && (P.value = null));
		}
		function be(e) {
			if (_) return;
			let t = e && typeof e == "object" && "code" in e ? e.code : "failed";
			me.value = t === "conflict", P.value = t === "bridge_pv_start_required" ? "bridgePvRequired" : t === "pv_sensor_missing" ? "pvMissing" : t === "invalid_tariff" || t === "invalid_format" ? "invalid" : [
				"conflict",
				"disconnected",
				"forbidden"
			].includes(String(t)) ? String(t) : "failed";
		}
		function xe(e) {
			return e === null ? "" : e.toFixed(2).replace(".", i?.language.value === "de" ? "," : ".");
		}
		async function Se() {
			if (i && !j.value) {
				ae.value = "loading", j.value = !0, P.value = null, L(), he.value = !1;
				try {
					let e = await i.loadTariff();
					if (_) return;
					if (!e.can_edit || e.tariff_type !== "time_of_use") throw { code: "forbidden" };
					M.value = e, ce.value = xe(e.base_price_ct_kwh), le.value = xe(e.feed_in_price_ct_kwh), ue.value = e.profiles?.time_of_use.pv_sensor ?? null, fe.value = e.windows.map((e) => ({
						key: pe++,
						start: Ee(e.start),
						end: Ee(e.end),
						price: xe(e.price_ct_kwh)
					})), me.value = !1, A.value = !0;
				} catch (e) {
					be(e);
				} finally {
					j.value = !1, await mn(), A.value && oe.value?.querySelector("input")?.focus();
				}
			}
		}
		function R() {
			A.value = !1, P.value = null, L(), me.value = !1, fe.value = [], mn(() => se.value?.focus());
		}
		async function Ce() {
			fe.value.push({
				key: pe++,
				start: "",
				end: "",
				price: ""
			}), await mn(), oe.value?.querySelector(".tariff-plan__window:last-of-type input")?.focus();
		}
		async function we(e) {
			L(fe.value[e]?.key), fe.value.splice(e, 1), await mn();
			let t = oe.value?.querySelectorAll(".tariff-plan__window");
			(t?.[Math.min(e, t.length - 1)]?.querySelector("input") ?? oe.value?.querySelector(".tariff-plan__add"))?.focus();
		}
		function Te(e, t, n) {
			if (!/^-?\d+(?:[.,]\d{1,2})?$/.test(e.trim())) return null;
			let r = Number(e.trim().replace(",", "."));
			return Number.isFinite(r) && r >= t && r <= n ? r : null;
		}
		function Ee(e) {
			return e.length === 8 && e.endsWith(":00") ? e.slice(0, 5) : e;
		}
		async function De() {
			if (!i || !M.value || j.value || me.value) return;
			P.value = null, L();
			for (let e of fe.value) for (let t of ["start", "end"]) {
				let n = ve(e.key, t);
				n && (e[t] = Es(n.value));
			}
			let e = Te(ce.value, -200, 500), t = Te(le.value, 0, 200), a = fe.value.map((e) => ({
				...e,
				value: Te(e.price, -200, 500)
			}));
			if (e === null || t === null || a.some((e) => e.value === null)) {
				P.value = "priceError";
				return;
			}
			let o = [];
			for (let e of a) {
				let t = $(e.start), n = $(e.end);
				if (t === null || n === null || t === n) {
					let r = t === null ? "start" : "end";
					F.value = {
						key: e.key,
						field: r,
						reason: t === null ? "startError" : n === null ? "endError" : "equalTimeError"
					}, P.value = "timeError", await mn(), ve(e.key, r)?.focus();
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
				P.value = "overlap";
				return;
			}
			ae.value = "saving", j.value = !0;
			let c = h(p.value);
			try {
				let o = {
					revision: M.value.revision,
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
				if (_) return;
				d.value = s, m.value = c, g(), R(), he.value = !0, r("saved");
			} catch (e) {
				be(e);
			} finally {
				j.value = !1;
			}
		}
		return H(ge, (e) => {
			!e && A.value ? P.value = "disconnected" : e && P.value === "disconnected" && (P.value = null);
		}), H(b, (e) => {
			!e && i?.ready.value && R();
		}), (t, n) => b.value ? (G(), K("section", {
			key: 0,
			class: N(["tariff-plan", { "tariff-plan--compact": e.compact }]),
			"aria-labelledby": `${V(a)}-tariff`
		}, [
			q("header", Ec, [q("h2", { id: `${V(a)}-tariff` }, I(o.value.tariff), 9, Dc), J(bo, null, {
				default: En(() => [q("button", {
					ref_key: "editButton",
					ref: se,
					type: "button",
					disabled: j.value || !ge.value || A.value && me.value,
					"aria-expanded": A.value,
					"aria-controls": `${V(a)}-editor`,
					onClick: n[0] ||= (e) => A.value ? De() : Se()
				}, I(j.value ? o.value[ae.value] : A.value ? o.value.save : o.value.edit), 9, Oc), A.value ? (G(), K("button", {
					key: 0,
					type: "button",
					disabled: j.value,
					onClick: R
				}, I(o.value.cancel), 9, kc)) : X("", !0)]),
				_: 1
			})]),
			j.value ? (G(), K("p", Ac, I(o.value[ae.value]), 1)) : X("", !0),
			!A.value && !e.compact ? (G(), K("p", jc, I(o.value.introduction), 1)) : X("", !0),
			e.compact ? (G(), K("div", Mc, [er(t.$slots, "current-price"), w.value ? (G(), K("p", Nc, [q("span", null, I(o.value.lowTariffPrice), 1), q("strong", null, I(c(v.value.low_tariff_price_eur_kwh)), 1)])) : X("", !0)])) : X("", !0),
			e.compact && !A.value ? (G(), K("div", Pc, [
				x.value.length ? (G(), K("ul", Fc, [(G(!0), K(W, null, U(x.value, (e, t) => (G(), K("li", { key: t }, [q("span", null, [
					Y(I(o.value.everyDay) + " " + I(k(e.start)) + " – " + I(k(e.end)), 1),
					ie(e) ? (G(), K("span", Ic, " (" + I(ie(e)) + ")", 1)) : X("", !0),
					e.end < e.start ? (G(), K("span", Lc, " (" + I(o.value.overnightLabel) + ")", 1)) : X("", !0)
				]), q("span", Rc, [E(e) ? (G(), K("span", zc, I(o.value.low), 1)) : X("", !0), q("strong", null, I(c(e.price_eur_kwh)), 1)])]))), 128))])) : (G(), K("p", Bc, I(o.value.noWindows), 1)),
				q("div", Vc, [q("span", null, [Y(I(o.value.base), 1), q("small", null, I(o.value.remaining), 1)]), q("span", Hc, [D.value ? (G(), K("span", Uc, I(o.value.low), 1)) : X("", !0), q("strong", null, I(c(v.value.base_price_eur_kwh)), 1)])]),
				q("div", Wc, [q("span", null, I(o.value.feed), 1), q("strong", null, I(c(v.value.feed_in_price_eur_kwh)), 1)]),
				w.value ? (G(), K("p", Gc, [ee.value ? (G(), K(W, { key: 0 }, [Y(I(o.value.lowUntil) + " " + I(T.value) + ".", 1)], 64)) : (G(), K(W, { key: 1 }, [Y(I(o.value.notLow), 1)], 64))])) : d.value || !y.value ? (G(), K("p", Kc, I(o.value.awaitingTariff), 1)) : (G(), K("p", qc, I(o.value.noLowTariff), 1)),
				q("p", Jc, I(o.value.compactImpact), 1)
			])) : X("", !0),
			he.value ? (G(), K("p", Yc, I(o.value.saved), 1)) : X("", !0),
			_e.value ? (G(), K("p", {
				key: 5,
				id: `${V(a)}-error`,
				role: "alert",
				class: "tariff-plan__error"
			}, I(_e.value), 9, Xc)) : X("", !0),
			A.value ? (G(), K("form", {
				key: 6,
				id: `${V(a)}-editor`,
				ref_key: "editor",
				ref: oe,
				class: "tariff-plan__editor",
				"aria-busy": j.value,
				novalidate: "",
				onSubmit: Ga(De, ["prevent"])
			}, [
				M.value?.base_price_ct_kwh === null ? (G(), K("p", Qc, I(o.value.first), 1)) : X("", !0),
				q("fieldset", { disabled: j.value || !ge.value }, [
					q("p", el, I(o.value.gross), 1),
					q("div", tl, [q("h3", null, I(o.value.baseSection), 1), q("label", null, [
						Y(I(o.value.base) + " (ct/kWh)", 1),
						Dn(q("input", {
							"onUpdate:modelValue": n[1] ||= (e) => ce.value = e,
							name: "base_price",
							type: "text",
							inputmode: "decimal",
							autocomplete: "off",
							"aria-describedby": `${V(a)}-base-hint`
						}, null, 8, nl), [[La, ce.value]]),
						q("small", { id: `${V(a)}-base-hint` }, I(o.value.baseHint), 9, rl)
					])]),
					q("div", il, [
						q("h3", null, I(o.value.windowsSection), 1),
						q("p", al, I(o.value.windowsHint), 1),
						q("p", {
							id: `${V(a)}-time-hint`,
							class: "tariff-plan__hint"
						}, I(o.value.timeHint), 9, ol),
						fe.value.length ? X("", !0) : (G(), K("p", sl, I(o.value.noWindows), 1)),
						(G(!0), K(W, null, U(fe.value, (e, t) => (G(), K("div", {
							key: e.key,
							class: "tariff-plan__window"
						}, [
							q("span", cl, I(o.value.window) + " " + I(t + 1), 1),
							q("label", null, [Y(I(o.value.from), 1), Dn(q("input", {
								"onUpdate:modelValue": (t) => e.start = t,
								name: `window_${e.key}_start`,
								type: "text",
								class: "tariff-plan__time",
								inputmode: "numeric",
								autocomplete: "off",
								placeholder: "HH:MM",
								"aria-invalid": F.value?.key === e.key && F.value.field === "start",
								"aria-describedby": F.value?.key === e.key && F.value.field === "start" ? `${V(a)}-time-hint ${V(a)}-error` : `${V(a)}-time-hint`,
								onInput: (t) => L(e.key),
								onChange: (t) => ye(e.key, "start", t),
								"aria-label": `${o.value.window} ${t + 1}: ${o.value.from}`
							}, null, 40, ll), [[La, e.start]])]),
							q("label", null, [Y(I(o.value.to), 1), Dn(q("input", {
								"onUpdate:modelValue": (t) => e.end = t,
								name: `window_${e.key}_end`,
								type: "text",
								class: "tariff-plan__time",
								inputmode: "numeric",
								autocomplete: "off",
								placeholder: "HH:MM",
								"aria-invalid": F.value?.key === e.key && F.value.field === "end",
								"aria-describedby": F.value?.key === e.key && F.value.field === "end" ? `${V(a)}-time-hint ${V(a)}-error` : `${V(a)}-time-hint`,
								onInput: (t) => L(e.key),
								onChange: (t) => ye(e.key, "end", t),
								"aria-label": `${o.value.window} ${t + 1}: ${o.value.to}`
							}, null, 40, ul), [[La, e.end]])]),
							q("label", null, [Y(I(o.value.price) + " (ct/kWh)", 1), Dn(q("input", {
								"onUpdate:modelValue": (t) => e.price = t,
								class: "tariff-plan__price",
								type: "text",
								inputmode: "decimal",
								autocomplete: "off",
								"aria-label": `${o.value.window} ${t + 1}: ${o.value.price} (ct/kWh)`
							}, null, 8, dl), [[La, e.price]])]),
							q("button", {
								type: "button",
								class: "tariff-plan__remove",
								"aria-label": `${o.value.window} ${t + 1}: ${o.value.remove}`,
								onClick: (e) => we(t)
							}, I(o.value.remove), 9, fl)
						]))), 128)),
						fe.value.length < 8 ? (G(), K("button", {
							key: 1,
							type: "button",
							class: "tariff-plan__add",
							onClick: Ce
						}, I(o.value.add), 1)) : X("", !0),
						fe.value.length ? (G(), K("p", pl, I(o.value.overnight), 1)) : X("", !0)
					]),
					q("div", ml, [q("h3", null, I(o.value.feedSection), 1), q("label", null, [
						Y(I(o.value.feed) + " (ct/kWh)", 1),
						Dn(q("input", {
							"onUpdate:modelValue": n[2] ||= (e) => le.value = e,
							name: "feed_in_price",
							type: "text",
							inputmode: "decimal",
							autocomplete: "off",
							"aria-describedby": `${V(a)}-feed-hint`
						}, null, 8, hl), [[La, le.value]]),
						q("small", { id: `${V(a)}-feed-hint` }, I(o.value.feedHint), 9, gl)
					])]),
					e.compact ? (G(), K("details", {
						key: 0,
						class: "tariff-plan__details tariff-plan__pv-details",
						open: de.value || P.value === "bridgePvRequired" || P.value === "pvMissing"
					}, [
						q("summary", null, I(o.value.pvDetails), 1),
						q("p", vl, I(o.value.pvHint), 1),
						J(tc, {
							modelValue: ue.value,
							"onUpdate:modelValue": n[3] ||= (e) => ue.value = e,
							hass: e.hass,
							label: de.value ? o.value.pvRequired : o.value.pv
						}, null, 8, [
							"modelValue",
							"hass",
							"label"
						])
					], 8, _l)) : X("", !0),
					q("div", yl, [
						q("strong", null, I(o.value.impact), 1),
						q("p", null, I(o.value.impactHint), 1),
						q("p", null, I(o.value.saveHint), 1)
					])
				], 8, $c),
				q("div", bl, [J(bo, null, {
					default: En(() => [q("button", {
						type: "submit",
						class: "tariff-plan__save",
						disabled: j.value || !ge.value || me.value
					}, I(j.value ? o.value[ae.value] : o.value.save), 9, xl), q("button", {
						type: "button",
						disabled: j.value,
						onClick: R
					}, I(o.value.cancel), 9, Sl)]),
					_: 1
				}), me.value ? (G(), K("button", {
					key: 0,
					type: "button",
					disabled: j.value || !ge.value,
					onClick: Se
				}, I(o.value.reload), 9, Cl)) : X("", !0)])
			], 40, Zc)) : X("", !0),
			!A.value && !e.compact && !d.value ? (G(), K("div", wl, [q("p", Tl, [q("span", null, I(o.value.currentPrice), 1), q("strong", null, I(C.value ? l.value : o.value.unavailable), 1)]), w.value ? (G(), K("p", El, [
				q("strong", null, I(o.value.lowTariffPrice) + ":", 1),
				Y(" " + I(c(v.value.low_tariff_price_eur_kwh)) + ". ", 1),
				ee.value ? (G(), K(W, { key: 0 }, [Y(I(o.value.lowUntil) + " " + I(T.value) + ". ", 1)], 64)) : (G(), K(W, { key: 1 }, [Y(I(o.value.notLow), 1)], 64))
			])) : (G(), K("p", Dl, I(o.value.noLowTariff), 1))])) : X("", !0),
			!A.value && !e.compact && C.value && v.value.next_price_change_at && !d.value ? (G(), K("p", Ol, [q("strong", null, I(o.value.next) + ":", 1), Y(" " + I(u(v.value.next_price_change_at)), 1)])) : X("", !0),
			!A.value && !e.compact ? (G(), K("details", kl, [
				q("summary", null, I(o.value.allPrices), 1),
				q("div", {
					class: "tariff-plan__scroll",
					tabindex: "0",
					role: "region",
					"aria-label": o.value.allPrices
				}, [q("table", jl, [q("thead", null, [q("tr", null, [
					q("th", Ml, I(o.value.status), 1),
					q("th", Nl, I(o.value.from), 1),
					q("th", Pl, I(o.value.to), 1),
					q("th", Fl, I(o.value.price), 1)
				])]), q("tbody", null, [(G(!0), K(W, null, U(x.value, (e, t) => (G(), K("tr", {
					key: t,
					class: N({
						"tariff-plan__current": ne(e),
						"tariff-plan__low": E(e)
					})
				}, [
					q("td", null, I(te(ne(e), E(e))), 1),
					q("td", null, I(k(e.start)), 1),
					q("td", null, I(k(e.end)), 1),
					q("td", null, I(c(e.price_eur_kwh)), 1)
				], 2))), 128)), q("tr", { class: N({
					"tariff-plan__current": re.value,
					"tariff-plan__low": D.value
				}) }, [
					q("td", null, I(te(re.value, D.value)), 1),
					q("td", Il, I(o.value.base), 1),
					q("td", null, I(c(v.value.base_price_eur_kwh)), 1)
				], 2)])])], 8, Al),
				q("p", null, [q("strong", null, I(o.value.feed) + ":", 1), Y(" " + I(c(v.value.feed_in_price_eur_kwh)), 1)]),
				!C.value && !d.value ? (G(), K("p", Ll, [Y(I(o.value.noPrice), 1), typeof S.value == "string" && S.value ? (G(), K("span", Rl, I(o.value.technicalReason) + ": " + I(S.value), 1)) : X("", !0)])) : X("", !0)
			])) : X("", !0),
			q("details", zl, [
				q("summary", null, I(o.value.details), 1),
				q("p", null, I(o.value.rule), 1),
				q("p", null, I(o.value.configure), 1)
			])
		], 10, Tc)) : X("", !0);
	}
}), [["styles", [".tariff-plan{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.tariff-plan h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.tariff-plan__introduction{color:var(--secondary-text-color,#666);margin:0 0 16px}.tariff-plan__compact-summary{margin:0}.tariff-plan__periods{margin:12px 0;padding:0;list-style:none}.tariff-plan__periods li{border-top:1px solid var(--divider-color,#e0e0e0);flex-wrap:wrap;justify-content:space-between;gap:4px 12px;padding:10px 0;line-height:1.5;display:flex}.tariff-plan__period-price{flex-wrap:wrap;align-items:center;gap:8px;display:flex}.tariff-plan__badge{border:1px solid var(--success-color,#43a047);border-radius:6px;margin-inline-start:8px;padding:2px 7px;font-size:12px;font-weight:500;line-height:1.5;display:inline-block}.tariff-plan__periods strong{white-space:nowrap}.tariff-plan__step{margin:20px 0}.tariff-plan__step h3{margin:0 0 10px;font-size:15px;line-height:1.5}.tariff-plan__step>label{max-width:460px}.tariff-plan__step>label input{max-width:240px}.tariff-plan__step .tariff-plan__hint{margin-top:0}.tariff-plan__impact{background:var(--secondary-background-color,#f5f5f5);border-radius:8px;margin:16px 0;padding:14px;font-size:14px;line-height:1.6}.tariff-plan__impact p{margin:6px 0}.tariff-plan__empty{color:var(--secondary-text-color,#666);font-size:14px}.tariff-plan__overview{grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:12px;display:grid}.tariff-plan__overview>p{margin:0}.tariff-plan__current-price{background:var(--secondary-background-color,#f5f5f5);border-radius:8px;flex-direction:column;gap:4px;padding:12px;display:flex}.tariff-plan__current-price>span{color:var(--secondary-text-color,#666);font-size:14px}.tariff-plan__current-price>strong{font-variant-numeric:tabular-nums;font-size:26px}.tariff-plan__low-status{padding:12px 0;font-size:14px}.tariff-plan__low-unavailable{border-inline-start:3px solid var(--warning-color,#ff9800);padding-inline-start:12px;font-size:14px}.tariff-plan p{overflow-wrap:anywhere;line-height:1.6}.tariff-plan p:last-child{margin-bottom:0}.tariff-plan__scroll{overflow-x:auto}.tariff-plan__table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%;line-height:1.5}.tariff-plan__table th,.tariff-plan__table td{text-align:left;white-space:nowrap;border-bottom:1px solid var(--divider-color,#e0e0e0);padding:10px 8px}.tariff-plan__table th:last-child,.tariff-plan__table td:last-child{text-align:right}.tariff-plan__current{background:var(--secondary-background-color,color-mix(in srgb, currentColor 8%, transparent));font-weight:600}.tariff-plan__header{flex-wrap:wrap;justify-content:space-between;align-items:center;gap:12px;margin-bottom:12px;display:flex}.tariff-plan__header h2{margin:0}.tariff-plan button{font:inherit;cursor:pointer;min-height:44px;color:var(--primary-color,#03a9f4);border:1px solid var(--divider-color,#e0e0e0);background:0 0;border-radius:8px;padding:8px 12px}.tariff-plan button:disabled{cursor:default;opacity:.5}.tariff-plan button:focus-visible,.tariff-plan input:focus-visible,.tariff-plan summary:focus-visible,.tariff-plan__scroll:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.tariff-plan__editor{margin-bottom:16px}.tariff-plan__editor fieldset{border:0;min-width:0;margin:0;padding:0}.tariff-plan__editor label{flex-direction:column;gap:6px;min-width:0;font-size:14px;display:flex}.tariff-plan__editor input{box-sizing:border-box;border:1px solid var(--divider-color,#bbb);width:100%;min-width:0;min-height:44px;font:inherit;font-variant-numeric:tabular-nums;color:var(--primary-text-color,#212121);background:var(--card-background-color,#fff);border-radius:6px;padding:10px}.tariff-plan__editor small,.tariff-plan__hint{color:var(--secondary-text-color,#666);font-size:13px}.tariff-plan__window{border-top:1px solid var(--divider-color,#e0e0e0);grid-template-columns:repeat(2,minmax(0,1fr));align-items:end;gap:12px;margin-top:20px;padding-top:16px;display:grid}.tariff-plan__window-name{grid-column:1/-1;font-size:14px;font-weight:600}.tariff-plan__window label:nth-of-type(3){grid-column:1}.tariff-plan__remove{justify-self:end}.tariff-plan__add{margin-top:16px}.tariff-plan__actions{flex-wrap:wrap;gap:8px;display:flex}.tariff-plan__error{color:var(--error-color,#db4437)}.tariff-plan input[aria-invalid=true]{border-color:var(--error-color,#db4437)}.tariff-plan__details{margin-top:14px;font-size:14px}.tariff-plan__details summary{cursor:pointer;color:var(--secondary-text-color,#666);box-sizing:border-box;min-height:44px;padding:12px 0;line-height:1.5}@media (max-width:400px){.tariff-plan__window{grid-template-columns:minmax(0,1fr)}}@media (max-width:600px){.tariff-plan{padding:20px}}@container sax-content (width>=860px){.tariff-plan{padding:18px}.tariff-plan h2{margin-bottom:12px;font-size:16px}.tariff-plan p{margin-top:10px;line-height:1.5}.tariff-plan__table th,.tariff-plan__table td{padding:7px 8px}}.tariff-plan.tariff-plan--compact{box-shadow:none;background:0 0;border:0;border-radius:0;padding:0}.tariff-plan--compact .tariff-plan__header{border-bottom:1px solid var(--divider-color,#ddd);flex-wrap:nowrap;margin-bottom:14px;padding-bottom:12px}.tariff-plan--compact .tariff-plan__header h2{margin:0;font-size:18px}.tariff-plan--compact .tariff-plan__header button{flex-shrink:0}.tariff-plan__price-highlights{flex-wrap:wrap;justify-content:space-between;align-items:center;gap:8px 16px;margin-bottom:12px;display:flex}.tariff-plan--compact .tariff-plan__low-status{text-align:right;margin:0;padding:0}.tariff-plan__low-status>span{color:var(--secondary-text-color,#666);display:block}.tariff-plan__low-status>strong{font-size:20px;font-weight:500;display:block}.tariff-plan__base-row,.tariff-plan__feed-row{border-top:1px solid var(--divider-color,#ddd);justify-content:space-between;align-items:center;gap:8px 12px;padding:10px 0;display:flex}.tariff-plan__base-row small{color:var(--secondary-text-color,#666);font-size:13px;display:block}.tariff-plan__feed-row>span{color:var(--secondary-text-color,#666)}.tariff-plan__feed-row strong{white-space:nowrap;font-weight:500}.tariff-plan--compact .tariff-plan__periods{margin:0}.tariff-plan--compact .tariff-plan__period-status{color:var(--secondary-text-color,#666);font-size:13px}.tariff-plan--compact .tariff-plan__impact{margin:10px 0 0;padding:8px 10px}.tariff-plan--compact>.tariff-plan__details{border-top:1px solid var(--divider-color,#ddd);margin-top:8px}"]]]);
//#endregion
//#region src/tariff-chart.ts
function Vl(e, t = 1e3) {
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
var Hl = ["aria-busy"], Ul = {
	key: 0,
	role: "status"
}, Wl = {
	key: 1,
	class: "tariff-price-chart__empty",
	role: "status"
}, Gl = {
	key: 0,
	class: "tariff-price-chart__partial"
}, Kl = ["viewBox", "aria-label"], ql = [
	"x2",
	"y1",
	"y2"
], Jl = ["y"], Yl = ["d"], Xl = ["x1", "x2"], Zl = ["x"], Ql = { key: 2 }, $l = [
	"x1",
	"x2",
	"y1",
	"y2"
], eu = ["x", "text-anchor"], tu = {
	class: "tariff-price-chart__detail",
	"aria-live": "polite"
}, nu = { class: "tariff-price-chart__scroll" }, ru = /*#__PURE__*/ go(/* @__PURE__ */ Bn({
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
		}), i = /* @__PURE__ */ B(), a = /* @__PURE__ */ B(620), o;
		Zn(() => {
			typeof ResizeObserver > "u" || !i.value || (o = new ResizeObserver((e) => {
				a.value = Math.max(180, e[0]?.contentRect.width ?? 620);
			}), o.observe(i.value));
		}), Qn(() => o?.disconnect());
		let s = Z(() => Vl(t.series, a.value)), c = /* @__PURE__ */ B(null), l = /* @__PURE__ */ B(!1);
		H(() => t.series, () => {
			c.value = null, l.value = !1;
		});
		let u = (e) => ro(e, t.hass, 2) ?? "—", d = Z(() => {
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
		}), f = (e, n = !1) => io(e, t.hass, {
			...n && d.value ? {
				hour: "2-digit",
				minute: "2-digit",
				timeZoneName: "shortOffset"
			} : { timeStyle: "short" },
			timeZone: t.series?.time_zone
		}) ?? "—", p = Z(() => c.value === null ? null : s.value.slots[c.value]), m = Z(() => Date.parse(t.series?.now ?? "")), h = Z(() => m.value >= s.value.start && m.value < s.value.end), g = Z(() => [
			s.value.start,
			s.value.start + (s.value.end - s.value.start) / 2,
			s.value.end
		]);
		function _(e) {
			let t = e.currentTarget.getBoundingClientRect(), n = (e.clientX - t.left) / t.width * a.value, r = s.value.start + (n - 48) / (a.value - 60) * (s.value.end - s.value.start), i = s.value.slots.findIndex((e) => r >= e.from && r < e.to);
			c.value = i < 0 ? null : i, l.value = i < 0;
		}
		function v(e) {
			[
				"ArrowLeft",
				"ArrowRight",
				"Home",
				"End"
			].includes(e.key) && s.value.slots.length && (e.preventDefault(), l.value = !1, c.value = e.key === "Home" ? 0 : e.key === "End" ? s.value.slots.length - 1 : Math.max(0, Math.min(s.value.slots.length - 1, (c.value ?? -1) + (e.key === "ArrowRight" ? 1 : -1))));
		}
		return (t, n) => (G(), K("div", {
			ref_key: "container",
			ref: i,
			class: "tariff-price-chart",
			"aria-busy": e.loading
		}, [e.loading ? (G(), K("p", Ul, I(r.value.loading), 1)) : s.value.slots.length ? (G(), K(W, { key: 2 }, [
			e.series?.status === "partial" ? (G(), K("p", Gl, I(r.value.partial), 1)) : X("", !0),
			(G(), K("svg", {
				viewBox: `0 0 ${a.value} 252`,
				preserveAspectRatio: "none",
				role: "img",
				"aria-label": `${r.value.title}. ${r.value.hint}`,
				tabindex: "0",
				onPointermove: _,
				onPointerdown: _,
				onKeydown: v
			}, [
				q("title", null, I(r.value.title), 1),
				n[0] ||= q("text", {
					x: "48",
					y: "15"
				}, "ct/kWh", -1),
				(G(!0), K(W, null, U(s.value.ticks, (e) => (G(), K("g", { key: e }, [q("line", {
					x1: "48",
					x2: a.value - 12,
					y1: s.value.y(e),
					y2: s.value.y(e),
					class: "tariff-price-chart__grid"
				}, null, 8, ql), q("text", {
					x: "40",
					y: s.value.y(e) + 4,
					"text-anchor": "end"
				}, I(u(e)), 9, Jl)]))), 128)),
				q("path", {
					d: s.value.path,
					class: "tariff-price-chart__line"
				}, null, 8, Yl),
				h.value ? (G(), K("line", {
					key: 0,
					x1: s.value.x(m.value),
					x2: s.value.x(m.value),
					y1: "25",
					y2: "216",
					class: "tariff-price-chart__now"
				}, null, 8, Xl)) : X("", !0),
				h.value ? (G(), K("text", {
					key: 1,
					x: Math.max(68, Math.min(a.value - 30, s.value.x(m.value))),
					y: "23",
					"text-anchor": "middle"
				}, I(r.value.now), 9, Zl)) : X("", !0),
				p.value ? (G(), K("g", Ql, [q("line", {
					x1: s.value.x(p.value.from),
					x2: s.value.x(p.value.to),
					y1: s.value.y(p.value.price_ct_kwh),
					y2: s.value.y(p.value.price_ct_kwh),
					class: "tariff-price-chart__selected"
				}, null, 8, $l)])) : X("", !0),
				(G(!0), K(W, null, U(g.value, (e, t) => (G(), K("text", {
					key: e,
					x: s.value.x(e),
					y: "244",
					"text-anchor": t === 0 ? "start" : t === 2 ? "end" : "middle"
				}, I(t === 2 ? "24:00" : f(new Date(e).toISOString())), 9, eu))), 128))
			], 40, Kl)),
			q("p", tu, I(p.value ? `${f(p.value.start, !0)}–${f(p.value.end, !0)} · ${u(p.value.price_ct_kwh)} ct/kWh` : l.value ? r.value.gap : r.value.hint), 1),
			q("details", null, [q("summary", null, I(r.value.table), 1), q("div", nu, [q("table", null, [q("thead", null, [q("tr", null, [
				q("th", null, I(r.value.from), 1),
				q("th", null, I(r.value.to), 1),
				q("th", null, I(r.value.price), 1)
			])]), q("tbody", null, [(G(!0), K(W, null, U(s.value.slots, (e) => (G(), K("tr", { key: e.start }, [
				q("td", null, I(f(e.start, !0)), 1),
				q("td", null, I(f(e.end, !0)), 1),
				q("td", null, I(u(e.price_ct_kwh)) + " ct/kWh", 1)
			]))), 128))])])])])
		], 64)) : (G(), K("div", Wl, I(r.value.empty), 1))], 8, Hl));
	}
}), [["styles", [".tariff-price-chart{min-width:0}.tariff-price-chart svg{touch-action:pan-y;width:100%;height:240px;display:block;overflow:visible}.tariff-price-chart svg text{fill:var(--secondary-text-color,#666);font-size:14px}.tariff-price-chart__line{fill:none;stroke:var(--primary-color,#03a9f4);stroke-width:3px;vector-effect:non-scaling-stroke}.tariff-price-chart__grid{stroke:var(--divider-color,#ddd);vector-effect:non-scaling-stroke}.tariff-price-chart__now{stroke:var(--secondary-text-color,#666);stroke-dasharray:4;vector-effect:non-scaling-stroke}.tariff-price-chart__selected{stroke:var(--success-color,#38964b);stroke-width:6px;vector-effect:non-scaling-stroke}.tariff-price-chart__empty{text-align:center;min-height:240px;color:var(--secondary-text-color,#666);place-items:center;display:grid}.tariff-price-chart__detail,.tariff-price-chart__partial{min-height:20px;color:var(--secondary-text-color,#666);font-size:14px}.tariff-price-chart summary{cursor:pointer;min-height:32px;padding:6px 0}.tariff-price-chart__scroll{overflow:auto}.tariff-price-chart table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%}.tariff-price-chart th,.tariff-price-chart td{text-align:left;border-bottom:1px solid var(--divider-color,#ddd);white-space:nowrap;padding:8px}.tariff-price-chart th:last-child,.tariff-price-chart td:last-child{text-align:right}"]]]), iu = ["aria-busy"], au = ["aria-busy"], ou = { class: "entity-control__description" }, su = ["for"], cu = ["id"], lu = { class: "entity-control__input" }, uu = [
	"id",
	"value",
	"min",
	"max",
	"step",
	"disabled",
	"aria-describedby",
	"aria-invalid",
	"onInput"
], du = ["id"], fu = {
	key: 0,
	class: "entity-control__error",
	role: "alert"
}, pu = {
	key: 1,
	role: "status",
	"aria-live": "polite"
}, mu = /* @__PURE__ */ Bn({
	__name: "ChargingNumberFields",
	props: { fields: { type: Array } },
	emits: ["apply"],
	setup(e, { expose: t, emit: n }) {
		let r = e, i = n, a = An(lo), o = `sax-charging-number-${Vn()}`, s = /* @__PURE__ */ jt({}), c = /* @__PURE__ */ jt({}), l = /* @__PURE__ */ new Map(), u = /* @__PURE__ */ B(!1), d = 0, f = Z(() => a?.language.value === "de" ? {
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
			return m.value || !a?.ready.value || !p(e)?.canControl;
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
		H(() => r.fields.map(({ key: e }) => [
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
		}), Qn(() => {
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
		async function ee() {
			if (m.value || !a) return !1;
			for (let { key: e } of r.fields) {
				let t = l.get(e), n = s[e];
				t && n && t.value !== n.value && (n.value = t.value, n.edited = !0, delete c[e], a.clearControlError("number", e));
			}
			let e = r.fields.filter(({ key: e }) => _(e));
			if (!e.length) {
				for (let e of Object.keys(c)) delete c[e];
				return !0;
			}
			for (let { key: e } of r.fields) {
				delete c[e];
				let t = p(e);
				if (!t?.available) {
					if (_(e)) return C(e, "unavailable");
					continue;
				}
				if (_(e) && (!t.canControl || !a.ready.value)) return C(e, "readonly");
				let n = g(s[e]?.value ?? ""), r = v(e, "min"), i = v(e, "max"), o = v(e, "step");
				if (n === null || l.get(e)?.validity.badInput || r === void 0 || i === void 0 || o === void 0 || o <= 0 || r > i || n < r || n > i && (e !== "timed_charge_max_soc" || _(e)) || !Number.isFinite((n - r) / o) || Math.abs((n - r) / o - Math.round((n - r) / o)) > 1e-7) return C(e, "invalid");
			}
			let t = "timed_charge_min_soc", n = "timed_charge_max_soc", i = e.some(({ key: e }) => e === t), o = e.some(({ key: e }) => e === n);
			if (i || o) {
				let e = (e) => r.fields.some((t) => t.key === e) ? g(s[e]?.value ?? "") : p(e)?.available ? g(p(e)?.state?.state ?? "") : null, a = e(t), l = e(n);
				if (a !== null && l !== null && a > l) return i && o && (c[t] = "order"), C(o ? n : t, "order");
			}
			u.value = !0;
			let h = d, y = e.map(({ key: e }) => [e, s[e]?.entityId]);
			try {
				let r = await a.performChargingSettings(Object.fromEntries(e.map(({ key: e }) => [e, s[e].value])));
				if (d !== h || y.some(([e, t]) => p(e)?.metadata.entity_id !== t)) return !1;
				if (!r) {
					let r = e.some(({ key: e }) => p(e)?.error === f.value.order);
					r && i && o && (c[t] = "order", c[n] = "order");
					let a = r ? e.find(({ key: e }) => e === (o ? n : t)) ?? e[0] : e.find(({ key: e }) => p(e)?.error) ?? e[0];
					p(a.key)?.error || (c[a.key] = "failed"), u.value = !1, await mn(), d === h && l.get(a.key)?.focus();
				}
				return r;
			} catch {
				return u.value = !1, await mn(), d === h && C(e[0].key, "failed"), !1;
			} finally {
				u.value = !1;
			}
		}
		return t({
			submit: ee,
			reset: T,
			pending: m
		}), (t, n) => (G(), K("div", {
			class: "charging-number-fields",
			"aria-busy": m.value
		}, [(G(!0), K(W, null, U(e.fields, (e) => (G(), K("form", {
			key: e.key,
			class: "entity-control",
			"aria-busy": m.value,
			onSubmit: Ga(w, ["prevent"])
		}, [
			q("div", ou, [q("label", {
				for: `${o}-${e.key}`,
				class: "entity-control__name"
			}, I(e.label), 9, su), q("p", {
				id: `${o}-${e.key}-value`,
				class: "entity-control__value"
			}, I(p(e.key)?.displayValue ?? f.value.unavailable), 9, cu)]),
			q("div", lu, [q("input", {
				id: `${o}-${e.key}`,
				ref_for: !0,
				ref: (t) => b(e.key, t),
				value: s[e.key]?.value ?? "",
				type: "number",
				min: v(e.key, "min"),
				max: v(e.key, "max"),
				step: v(e.key, "step"),
				disabled: h(e.key),
				"aria-describedby": `${o}-${e.key}-value ${o}-${e.key}-status`,
				"aria-invalid": !!x(e.key),
				required: "",
				onInput: (t) => y(e.key, t),
				onInvalid: Ga(w, ["prevent"])
			}, null, 40, uu)]),
			q("div", {
				id: `${o}-${e.key}-status`,
				class: "entity-control__feedback"
			}, [x(e.key) ? (G(), K("p", fu, I(x(e.key)), 1)) : S(e.key) ? (G(), K("p", pu, I(S(e.key)), 1)) : X("", !0)], 8, du)
		], 40, au))), 128))], 8, iu));
	}
}), hu = { class: "dynamic-charging-settings" }, gu = { class: "dynamic-charging-summary" }, _u = { class: "electricity-summary-rows" }, vu = {
	key: 0,
	class: "electricity-targets"
}, yu = { class: "electricity-target" }, bu = { class: "electricity-target" }, xu = {
	key: 0,
	class: "electricity-muted dynamic-charging-neutral-summary"
}, Su = {
	key: 1,
	class: "electricity-error",
	role: "alert"
}, Cu = {
	key: 2,
	role: "status",
	"aria-live": "polite"
}, wu = {
	key: 3,
	class: "dynamic-charging-editor"
}, Tu = ["aria-label", "aria-busy"], Eu = [
	"data-strategy",
	"aria-pressed",
	"disabled",
	"onClick"
], Du = { class: "electricity-muted" }, Ou = {
	key: 0,
	class: "dynamic-charging-notice"
}, ku = /*#__PURE__*/ go(/* @__PURE__ */ Bn({
	__name: "DynamicChargingSettings",
	props: { editing: { type: Boolean } },
	emits: ["apply"],
	setup(e, { expose: t, emit: n }) {
		let r = e, i = n, a = /* @__PURE__ */ B();
		t({
			submit: () => a.value?.submit() ?? Promise.resolve(!0),
			reset: () => a.value?.reset() ?? !0,
			pending: Z(() => a.value?.pending ?? !1)
		});
		let o = An(lo), s = /* @__PURE__ */ B(r.editing);
		H(() => r.editing, (e) => {
			e && (s.value = !0);
		});
		let c = Z(() => o?.language.value === "de"), l = Z(() => c.value ? {
			mode: "Ladeweise",
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
		}), u = Z(() => o?.entity("select", "price_charge_strategy")), d = [
			"smart",
			"relative",
			"absolute",
			"off"
		], f = Z(() => {
			let e = u.value?.state?.state;
			return u.value?.available && d.includes(e) ? e : null;
		}), p = Z(() => u.value?.state?.attributes.options), m = Z(() => !u.value?.canControl || u.value.pending || a.value?.pending), h = Z(() => o?.connected.value ? u.value?.available ? u.value.metadata.can_control ? u.value.pending ? l.value.pending : "" : l.value.readonly : l.value.unavailable : l.value.disconnected), g = Z(() => o?.entity("number", "max_soc")), _ = Z(() => f.value && f.value !== "off" ? [
			{
				key: "max_soc",
				label: l.value.targetLabel
			},
			f.value === "absolute" ? {
				key: "price_charge_max_price",
				label: l.value.price
			} : {
				key: "price_charge_hours",
				label: l.value.hours
			},
			{
				key: "price_charge_neutral_price",
				label: l.value.neutral
			}
		] : []), v = Z(() => o?.entity("number", f.value === "absolute" ? "price_charge_max_price" : "price_charge_hours")), y = Z(() => {
			let e = o?.entity("number", "price_charge_neutral_price"), t = o?.entity("number", "price_charge_max_price"), n = Q(e?.state?.state), r = Q(t?.state?.state);
			return !e?.available || n === null || f.value === "absolute" && (!t?.available || r === null) ? l.value.neutralUnavailable : f.value === "absolute" && r !== null && n <= r ? l.value.neutralInactive : `${l.value.neutralSummary} ${e.displayValue}${f.value === "absolute" ? ` ${l.value.neutralBand}` : ""}.`;
		});
		async function b(e) {
			!m.value && Array.isArray(p.value) && p.value.includes(e) && f.value !== e && await o?.perform("select", "price_charge_strategy", e);
		}
		return (t, n) => (G(), K("div", hu, [
			q("div", gu, [q("dl", _u, [q("div", null, [q("dt", null, I(l.value.saved), 1), q("dd", null, I(f.value ? l.value.modes[f.value] : l.value.unavailable), 1)])]), f.value && f.value !== "off" ? (G(), K("div", vu, [q("div", yu, [q("span", null, I(l.value.targetSummary), 1), q("strong", null, I(g.value?.available ? g.value.displayValue : "—"), 1)]), q("div", bu, [q("span", null, I(f.value === "absolute" ? l.value.price : l.value.hours), 1), q("strong", null, I(v.value?.available ? v.value.displayValue : "—"), 1)])])) : X("", !0)]),
			f.value && f.value !== "off" ? (G(), K("p", xu, I(y.value), 1)) : X("", !0),
			u.value?.error ? (G(), K("p", Su, I(u.value.error), 1)) : h.value ? (G(), K("p", Cu, I(h.value), 1)) : X("", !0),
			s.value ? Dn((G(), K("div", wu, [
				q("h3", null, I(l.value.mode), 1),
				q("div", {
					class: "dynamic-charging-methods",
					role: "group",
					"aria-label": l.value.mode,
					"aria-busy": u.value?.pending ?? !1
				}, [(G(), K(W, null, U(d, (e) => q("button", {
					key: e,
					type: "button",
					"data-strategy": e,
					"aria-pressed": f.value === e,
					disabled: m.value || !Array.isArray(p.value) || !p.value.includes(e),
					onClick: (t) => b(e)
				}, [q("strong", null, I(l.value.modes[e]), 1)], 8, Eu)), 64))], 8, Tu),
				J(mu, {
					ref_key: "numbers",
					ref: a,
					fields: _.value,
					onApply: n[0] ||= (e) => i("apply")
				}, null, 8, ["fields"]),
				f.value && f.value !== "off" ? (G(), K(W, { key: 0 }, [q("p", Du, I(l.value.targetHint), 1), f.value === "absolute" ? X("", !0) : (G(), K("p", Ou, I(l.value.noPriceLimit), 1))], 64)) : X("", !0)
			], 512)), [[Zi, e.editing]]) : X("", !0)
		]));
	}
}), [["styles", [".dynamic-charging-methods{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:16px;display:grid}.dynamic-charging-methods button{text-align:left;color:var(--primary-text-color,#212121);padding:12px}.dynamic-charging-methods button[aria-pressed=true]{border:2px solid var(--primary-color,#03a9f4);background:var(--secondary-background-color,#f5f5f5);padding:11px}.dynamic-charging-methods strong{line-height:1.5;display:block}.dynamic-charging-editor>.entity-control{box-shadow:none;background:0 0;border:0;border-radius:0;padding:12px 0}.dynamic-charging-notice{border-left:3px solid var(--primary-color,#03a9f4);padding-left:12px}@media (max-width:700px){.dynamic-charging-methods{grid-template-columns:minmax(0,1fr)}}"]]]), Au = { class: "tou-charging-settings" }, ju = { class: "tou-charging-summary" }, Mu = { class: "electricity-summary-rows" }, Nu = {
	key: 0,
	class: "electricity-target tou-charging-threshold"
}, Pu = { class: "electricity-target tou-charging-target" }, Fu = { class: "electricity-target tou-charging-global" }, Iu = { class: "electricity-summary-rows tou-charging-month-summary" }, Lu = {
	key: 0,
	class: "tou-charging-error",
	role: "alert"
}, Ru = {
	key: 1,
	role: "status",
	"aria-live": "polite"
}, zu = {
	key: 0,
	class: "tou-charging-editor"
}, Bu = ["aria-label", "aria-busy"], Vu = [
	"data-method",
	"aria-pressed",
	"disabled",
	"onClick"
], Hu = {
	key: 0,
	class: "tou-charging-hint"
}, Uu = { class: "tou-charging-limits" }, Wu = /*#__PURE__*/ go(/* @__PURE__ */ Bn({
	__name: "TimeOfUseChargingSettings",
	props: {
		editing: { type: Boolean },
		hass: { type: Object }
	},
	emits: ["apply"],
	setup(e, { expose: t, emit: n }) {
		let r = e, i = n, a = /* @__PURE__ */ B();
		t({
			submit: () => a.value?.submit() ?? Promise.resolve(!0),
			reset: () => a.value?.reset() ?? !0,
			pending: Z(() => a.value?.pending ?? !1)
		});
		let o = An(lo), s = Z(() => o?.language.value === "de"), c = `sax-tou-method-${Vn()}`, l = /* @__PURE__ */ B(r.editing);
		H(() => r.editing, (e) => {
			e && (l.value = !0);
		});
		let u = Z(() => s.value ? {
			saved: "Ladeweise",
			start: "Start nur unter",
			startAtZero: "Start bei",
			mode: "Ladeweise",
			fixed: "Festes Netzladeziel",
			bridge: "Nur Bedarf bis Solarstrom",
			target: "Netzladeziel",
			fixedTarget: "Netzladeziel (%)",
			bridgeTarget: "Maximales Netzladeziel (%)",
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
			bridge: "Only what is needed until solar power",
			target: "Grid charge target",
			fixedTarget: "Grid charge target (%)",
			bridgeTarget: "Maximum grid charge target (%)",
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
		}), d = Z(() => o?.entity("switch", "bridge_charge_enabled")), f = ["fixed", "bridge"], p = Z(() => d.value?.available ? d.value.state?.state === "off" ? "fixed" : d.value.state?.state === "on" ? "bridge" : null : null), m = Z(() => !d.value?.canControl || d.value.pending || a.value?.pending || p.value === null), h = Z(() => d.value?.pending ? u.value.pending : o?.connected.value ? p.value ? d.value?.metadata.can_control ? "" : u.value.readonly : u.value.unavailable : u.value.disconnected), g = Z(() => o?.entity("number", "timed_charge_max_soc")), _ = Z(() => o?.entity("number", "timed_charge_min_soc")), v = Z(() => o?.entity("number", "max_soc")), y = Z(() => [
			...p.value === "fixed" ? [{
				key: "timed_charge_min_soc",
				label: u.value.threshold
			}] : [],
			...p.value ? [{
				key: "timed_charge_max_soc",
				label: p.value === "fixed" ? u.value.fixedTarget : u.value.bridgeTarget
			}] : [],
			{
				key: "max_soc",
				label: u.value.global
			}
		]), b = Z(() => p.value === "bridge" ? u.value.bridgeTarget.replace(" (%)", "") : u.value.target), x = Z(() => g.value?.available ? g.value.displayValue : u.value.valueUnavailable), S = Z(() => !!o?.tariff.value?.profiles?.time_of_use.pv_sensor), C = Array.from({ length: 12 }, (e, t) => `timed_charge_month_${t + 1}`), w = Z(() => {
			let e = new Intl.DateTimeFormat(s.value ? "de" : "en", {
				month: "short",
				timeZone: "UTC"
			}), t = C.map((t, n) => {
				let r = o?.entity("switch", t), i = r?.state?.state;
				return {
					known: r?.available && (i === "on" || i === "off"),
					selected: r?.available && i === "on",
					name: e.format(new Date(Date.UTC(2024, n, 1)))
				};
			}), n = t.filter((e) => e.selected), r = t.some((e) => !e.known);
			return n.length === 12 ? u.value.allYear : n.length ? `${n.map((e) => e.name).join(", ")}${r ? ` · ${u.value.unknownMonths}` : ""}` : r ? u.value.unknownMonths : u.value.noMonths;
		});
		async function T(e) {
			m.value || p.value === e || await o?.perform("switch", "bridge_charge_enabled", e === "bridge");
		}
		return (t, n) => (G(), K("div", Au, [
			q("div", ju, [
				q("dl", Mu, [q("div", null, [q("dt", null, I(u.value.saved), 1), q("dd", null, I(p.value ? u.value[p.value] : u.value.unavailable), 1)])]),
				p.value ? (G(), K("div", {
					key: 0,
					class: N(["electricity-targets tou-charging-soc-row", { "tou-charging-soc-row--bridge": p.value === "bridge" }])
				}, [
					p.value === "fixed" ? (G(), K("div", Nu, [q("span", null, I(V(Q)(_.value?.state?.state) === 0 ? u.value.startAtZero : u.value.start), 1), q("strong", null, I(_.value?.available ? _.value.displayValue : u.value.valueUnavailable), 1)])) : X("", !0),
					q("div", Pu, [q("span", null, I(b.value), 1), q("strong", null, I(x.value), 1)]),
					q("div", Fu, [q("span", null, I(u.value.maxSoc), 1), q("strong", null, I(v.value?.available ? v.value.displayValue : u.value.valueUnavailable), 1)])
				], 2)) : X("", !0),
				q("dl", Iu, [q("div", null, [q("dt", null, I(u.value.months), 1), q("dd", null, I(w.value), 1)])])
			]),
			q("div", {
				id: c,
				class: "tou-charging-feedback"
			}, [e.editing && d.value?.error ? (G(), K("p", Lu, I(d.value.error), 1)) : X("", !0), h.value && (e.editing || !d.value?.pending) ? (G(), K("p", Ru, I(h.value), 1)) : X("", !0)]),
			l.value ? Dn((G(), K("div", zu, [
				q("h3", null, I(u.value.mode), 1),
				q("div", {
					class: "tou-charging-methods",
					role: "group",
					"aria-label": u.value.mode,
					"aria-describedby": c,
					"aria-busy": d.value?.pending ?? !1
				}, [(G(), K(W, null, U(f, (e) => q("button", {
					key: e,
					type: "button",
					"data-method": e,
					"aria-pressed": p.value === e,
					disabled: m.value,
					onClick: (t) => T(e)
				}, [q("strong", null, I(u.value[e]), 1)], 8, Vu)), 64))], 8, Bu),
				p.value === "bridge" && !S.value ? (G(), K("p", Hu, I(u.value.pvRequired), 1)) : X("", !0),
				q("div", Uu, [J(mu, {
					ref_key: "numbers",
					ref: a,
					fields: y.value,
					onApply: n[0] ||= (e) => i("apply")
				}, null, 8, ["fields"])]),
				q("h3", null, I(u.value.months), 1),
				J(Ts, {
					"entity-keys": V(C),
					"always-expanded": ""
				}, null, 8, ["entity-keys"])
			], 512)), [[Zi, e.editing]]) : X("", !0)
		]));
	}
}), [["styles", [".tou-charging-settings{min-width:0}.tou-charging-settings .tou-charging-soc-row{grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.tou-charging-settings .tou-charging-soc-row--bridge{grid-template-columns:repeat(2,minmax(0,1fr))}.tou-charging-soc-row>.electricity-target{padding:8px}.tou-charging-soc-row>.electricity-target>strong{margin-top:auto;font-size:clamp(18px,4cqi,24px)}.tou-charging-limits .entity-control{box-shadow:none;background:0 0;border:0;border-radius:0;padding:12px 0}.tou-charging-summary,.tou-charging-threshold,.tou-charging-month-summary{overflow-wrap:anywhere;line-height:1.5}.tou-charging-hint{color:var(--secondary-text-color,#666);font-size:14px;line-height:1.6}.tou-charging-error{color:var(--error-color,#b00020)}.tou-charging-methods{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:16px 0;display:grid}.tou-charging-methods button{border:1px solid var(--divider-color,#ddd);background:var(--card-background-color,#fff);min-width:0;min-height:44px;color:var(--primary-text-color,#212121);text-align:left;font:inherit;cursor:pointer;border-radius:8px;padding:12px}.tou-charging-methods button[aria-pressed=true]{border:2px solid var(--primary-color,#03a9f4);background:var(--secondary-background-color,#f5f5f5);padding:11px}.tou-charging-methods strong{line-height:1.5;display:block}.tou-charging-methods button:disabled{opacity:.55;cursor:not-allowed}.tou-charging-methods button:focus-visible{outline:3px solid var(--primary-color,#03a9f4);outline-offset:3px}@media (max-width:700px){.tou-charging-methods{grid-template-columns:minmax(0,1fr)}}"]]]), Gu = { class: "electricity-tariff-view" }, Ku = { class: "electricity-card electricity-tariff-bar" }, qu = { class: "electricity-tariff-bar__row" }, Ju = { class: "electricity-active" }, Yu = ["disabled", "aria-expanded"], Xu = ["aria-busy"], Zu = ["disabled"], Qu = { class: "electricity-sr-only" }, $u = ["value"], ed = {
	key: 0,
	role: "status"
}, td = ["disabled"], nd = ["disabled"], rd = {
	key: 1,
	class: "electricity-operation-status",
	role: "status",
	"aria-live": "polite"
}, id = {
	key: 2,
	role: "alert",
	class: "electricity-error"
}, ad = ["disabled"], od = {
	key: 4,
	role: "status"
}, sd = {
	key: 5,
	role: "status"
}, cd = {
	key: 6,
	role: "status"
}, ld = {
	key: 0,
	class: "electricity-columns"
}, ud = ["aria-label"], dd = { class: "electricity-current" }, fd = { class: "electricity-muted" }, pd = { class: "electricity-current-price" }, md = { key: 0 }, hd = ["aria-busy"], gd = ["disabled", "aria-expanded"], _d = ["disabled"], vd = { class: "electricity-current" }, yd = { class: "electricity-muted" }, bd = { class: "electricity-current-price" }, xd = { key: 0 }, Sd = { class: "electricity-price-summary electricity-summary-rows" }, Cd = ["aria-busy"], wd = ["id"], Td = ["disabled"], Ed = { class: "electricity-muted" }, Dd = { class: "electricity-fields" }, Od = ["aria-invalid", "aria-describedby"], kd = { class: "electricity-muted" }, Ad = { class: "electricity-muted" }, jd = { class: "electricity-fields" }, Md = { class: "electricity-muted" }, Nd = {
	key: 0,
	class: "electricity-muted electricity-additional-settings"
}, Pd = { class: "electricity-price-advanced" }, Fd = { class: "electricity-fields" }, Id = ["aria-invalid", "aria-describedby"], Ld = ["aria-invalid", "aria-describedby"], Rd = ["value"], zd = { class: "electricity-muted" }, Bd = { class: "electricity-muted" }, Vd = { class: "electricity-fields" }, Hd = ["aria-invalid", "aria-describedby"], Ud = { class: "electricity-muted" }, Wd = ["disabled"], Gd = ["disabled"], Kd = { class: "electricity-price-details" }, qd = ["aria-label"], Jd = ["aria-pressed", "onClick"], Yd = { class: "electricity-day" }, Xd = { key: 0 }, Zd = {
	key: 0,
	class: "electricity-card electricity-charging"
}, Qd = [
	"disabled",
	"aria-busy",
	"aria-expanded"
], $d = ["disabled"], ef = {
	key: 0,
	class: "electricity-activation"
}, tf = ["aria-busy"], nf = [
	"checked",
	"aria-describedby",
	"disabled"
], rf = {
	id: "electricity-master-status",
	class: "electricity-master-status",
	role: "status",
	"aria-live": "polite"
}, af = {
	key: 0,
	id: "electricity-activation-error",
	class: "electricity-error",
	role: "alert"
}, of = ["disabled"], sf = {
	key: 2,
	class: "electricity-muted"
}, cf = {
	key: 3,
	class: "electricity-muted"
}, lf = {
	key: 4,
	class: "electricity-muted"
}, uf = { key: 5 }, df = {
	key: 3,
	class: "electricity-charging-feedback"
}, ff = {
	key: 0,
	class: "electricity-error",
	role: "alert"
}, pf = {
	key: 1,
	role: "status",
	"aria-live": "polite"
}, mf = {
	key: 4,
	class: "electricity-charging-editor"
}, hf = ["disabled"], gf = ["disabled"], _f = {
	key: 0,
	role: "status",
	"aria-live": "polite"
}, vf = {
	key: 5,
	class: "electricity-charge-status"
}, yf = ["aria-label"], bf = { key: 0 }, xf = { class: "electricity-summary-rows electricity-pv-summary" }, Sf = {
	key: 0,
	class: "electricity-planned-pv"
}, Cf = {
	key: 1,
	class: "electricity-footnote"
}, wf = /*#__PURE__*/ go(/* @__PURE__ */ Bn({
	__name: "ElectricityTariffView",
	props: { hass: { type: Object } },
	setup(e) {
		let t = e, n = An(lo), r = Z(() => n?.language.value === "de"), i = Z(() => r.value ? {
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
		}), a = /* @__PURE__ */ B(null);
		H(() => n?.tariff.value, (e) => {
			e && (a.value = e);
		}, { immediate: !0 });
		let o = Z(() => n?.tariff.value ?? a.value), s = Z(() => o.value?.tariff_type), c = Z(() => s.value === "time_of_use" || s.value === "dynamic"), l = Z(() => n?.connected.value === !0 && n.ready.value), u = Z(() => o.value?.can_configure === !0 && l.value), d = Z(() => s.value === "dynamic" ? i.value.dynamic : s.value === "time_of_use" ? i.value.tou : i.value.unset), f = Z(() => n?.entity("switch", s.value === "dynamic" ? "price_charge_enabled" : "timed_charge_enabled")), p = Z(() => typeof o.value?.automation_enabled == "boolean" ? o.value.automation_enabled : f.value?.available ? f.value.state?.state === "on" : null), m = /* @__PURE__ */ B(null), h = /* @__PURE__ */ B(!1), g = /* @__PURE__ */ B("today"), _ = /* @__PURE__ */ B(null), v = /* @__PURE__ */ B(null), y = /* @__PURE__ */ B(null), b = Vn(), x = /* @__PURE__ */ B(!1), S = /* @__PURE__ */ B(!1), C = /* @__PURE__ */ B(null), w = /* @__PURE__ */ B(null), T = /* @__PURE__ */ B(!1), ee = /* @__PURE__ */ B(!1), E = /* @__PURE__ */ B(!1), D = /* @__PURE__ */ B("time_of_use"), te = /* @__PURE__ */ B(""), O = /* @__PURE__ */ B(!1), ne = /* @__PURE__ */ B(!1), re = /* @__PURE__ */ B(!1), k = /* @__PURE__ */ B({
			feed_in_price_ct_kwh: null,
			price_sensor: null,
			price_attribute: null,
			price_unit: "auto",
			pv_sensor: null,
			pv_factor: 100
		}), ie = /* @__PURE__ */ B(""), A = /* @__PURE__ */ B(""), j = /* @__PURE__ */ B(""), ae = /* @__PURE__ */ B(), oe = /* @__PURE__ */ B(), se = /* @__PURE__ */ B(), M = /* @__PURE__ */ B(), ce = /* @__PURE__ */ B(!1), le = !1, ue = 0;
		Qn(() => {
			le = !0, ue++, window.clearInterval(xe);
		});
		let de = Z(() => O.value || ne.value || re.value), N = Z(() => ro(l.value ? m.value?.current_price_ct_kwh : null, t.hass, 2)), fe = Z(() => m.value ? io(`${m.value.date}T12:00:00Z`, t.hass, {
			dateStyle: "medium",
			timeZone: "UTC"
		}) : null), pe = Z(() => {
			let e = s.value === "dynamic" ? o.value?.profiles?.dynamic.price_sensor : n?.entity("sensor", "economics_current_import_price")?.metadata.entity_id;
			return e ? t.hass?.states[e] : void 0;
		}), P = Z(() => {
			let e = n?.entity("sensor", "price_charge_status_text"), r = e?.state?.attributes, i = o.value?.profiles?.dynamic.pv_sensor;
			if (!e?.available || !i || r?.pv_prognose_sensor !== i) return null;
			let a = Q(r.pv_prognose_kwh);
			return a !== null && a >= 0 ? ro(a, t.hass, 1) : null;
		}), F = Array.from({ length: 12 }, (e, t) => `timed_charge_month_${t + 1}`), me = Z(() => (s.value === "dynamic" ? [
			["number", "max_soc"],
			["number", "price_charge_max_price"],
			["number", "price_charge_hours"],
			["number", "price_charge_neutral_price"]
		] : [
			["number", "max_soc"],
			["number", "timed_charge_max_soc"],
			["number", "timed_charge_min_soc"],
			["switch", "bridge_charge_enabled"],
			...F.map((e) => ["switch", e])
		]).map(([e, t]) => n?.entity(e, t)).filter((e) => e && (e.pending || e.error))), he = Z(() => {
			let e = o.value?.profiles?.dynamic;
			return e ? [
				e.price_attribute ? `${i.value.attribute}: ${e.price_attribute}` : "",
				e.price_unit === "auto" ? "" : `${i.value.unit}: ${i.value.units[e.price_unit]}`,
				e.pv_factor === 100 ? "" : `${i.value.pvFactor}: ${e.pv_factor}`
			].filter(Boolean).join(" · ") : "";
		}), ge = Z(() => {
			let e = o.value?.profiles?.dynamic.price_sensor;
			return e ? t.hass?.states[e]?.attributes.friendly_name ?? e : i.value.unset;
		}), _e = Z(() => ro(o.value?.profiles?.dynamic.feed_in_price_ct_kwh, t.hass, 2)), ve = Z(() => {
			let e = s.value === "dynamic" ? o.value?.profiles?.dynamic.pv_sensor : o.value?.profiles?.time_of_use.pv_sensor;
			if (!e) return i.value.noPv;
			if (!n?.connected.value) return i.value.pvReadError;
			let t = n?.entity("sensor", "charging_pv_forecast");
			return t?.state?.attributes.source_entity_id === e ? t.available ? t.displayValue : t.state?.attributes.reading_status === "error" ? i.value.pvReadError : i.value.pvWaiting : i.value.pvWaiting;
		});
		function ye(e, t) {
			_.value = t, O.value && (y.value = e, mn(() => {
				if (le) return;
				let t = ae.value?.querySelector(`[name="dynamic_${e}"]`), n = t?.closest("details");
				n && (n.open = !0), t?.focus();
			}));
		}
		function L(e, t = null) {
			if (le) return;
			v.value = t;
			let n = e && typeof e == "object" && "code" in e ? String(e.code) : "failed";
			x.value = n === "conflict", y.value = null;
			let r = {
				price_sensor_not_configured: ["price_sensor", i.value.missingPriceSensor],
				price_sensor_missing: ["price_sensor", i.value.priceSensorMissing],
				price_unit_unsupported: ["price_unit", i.value.unsupportedPriceUnit],
				pv_sensor_missing: ["pv_sensor", i.value.pvSensorMissing],
				invalid_price_attribute: ["price_attribute", i.value.invalidAttribute],
				invalid_feed_in_price: ["feed", ie.value.trim() ? i.value.invalidFeed : i.value.missingFeed],
				invalid_pv_factor: ["pv_factor", i.value.invalidPvFactor]
			}[n];
			if (r) {
				ye(...r);
				return;
			}
			_.value = n === "bridge_pv_start_required" ? i.value.bridgePvRequired : n === "conflict" ? i.value.conflict : n === "forbidden" ? i.value.readonly : n === "disconnected" ? i.value.disconnected : n === "invalid_tariff" || n === "invalid_format" ? i.value.invalid : i.value.failed;
		}
		async function be() {
			let e = ++ue;
			if (!n || !l.value || !c.value) {
				m.value = null, h.value = !1;
				return;
			}
			let t = s.value, r = o.value?.revision, i = g.value;
			h.value = !0;
			try {
				let a = await n.loadTariffSeries(i);
				!le && e === ue && s.value === t && o.value?.revision === r && g.value === i && (m.value = a.tariff_type === t && a.revision === r && a.day === i ? a : null);
			} catch {
				!le && e === ue && (m.value = null);
			} finally {
				!le && e === ue && (h.value = !1);
			}
		}
		H([
			l,
			s,
			() => o.value?.revision,
			g,
			pe
		], () => {
			be();
		}, { immediate: !0 }), H(s, (e, t) => {
			t && e !== t && de.value && (O.value = !1, ne.value = !1, re.value = !1, _.value = null, y.value = null, x.value = !1, ee.value = !0), g.value = "today", m.value = null;
		}), H(l, (e) => {
			e && n?.loadTariff().catch(L);
		}, { immediate: !0 });
		let xe = window.setInterval(() => {
			l.value && (be(), S.value || n?.loadTariff().catch(() => {}));
		}, 6e4), Se = Z(() => {
			let e = o.value?.profiles?.[D.value];
			return !e || e.feed_in_price_ct_kwh === null ? !0 : "price_sensor" in e ? !e.price_sensor : e.base_price_ct_kwh === null;
		});
		function R() {
			ee.value = !1, D.value = s.value === "dynamic" ? "dynamic" : "time_of_use", te.value = o.value?.revision ?? "", E.value = !0, _.value = null, T.value = !1;
		}
		async function Ce() {
			if (n && u.value && !S.value) {
				S.value = !0, w.value = "applying", _.value = null;
				try {
					await n.configureTariff({
						revision: te.value,
						tariff_type: D.value,
						...Se.value ? { automation_enabled: !1 } : {}
					}), le || (E.value = !1, T.value = !0);
				} catch (e) {
					L(e);
				} finally {
					w.value = null, S.value = !1;
				}
			}
		}
		async function we(e) {
			let t = e.target, r = t.checked;
			if (t.checked = p.value === !0, n && u.value && c.value && !S.value) {
				S.value = !0, C.value = r, _.value = null, T.value = !1;
				try {
					await n.configureTariff({
						revision: o.value.revision,
						tariff_type: s.value,
						automation_enabled: r
					});
				} catch (e) {
					L(e, "activation");
				} finally {
					C.value = null, S.value = !1;
				}
			}
		}
		async function Te() {
			if (ee.value = !1, n && !S.value) {
				S.value = !0, w.value = "loading", _.value = null, y.value = null, T.value = !1;
				try {
					let e = await n.loadTariff();
					if (le) return;
					if (!e.can_configure || e.tariff_type !== "dynamic" || !e.profiles) throw { code: "forbidden" };
					k.value = { ...e.profiles.dynamic }, ie.value = k.value.feed_in_price_ct_kwh === null ? "" : String(k.value.feed_in_price_ct_kwh).replace(".", r.value ? "," : "."), A.value = String(k.value.pv_factor), j.value = e.revision, O.value = !0, x.value = !1;
				} catch (e) {
					L(e);
				} finally {
					w.value = null, S.value = !1, await mn(), ae.value?.querySelector("select,input")?.focus();
				}
			}
		}
		function Ee() {
			O.value = !1, _.value = null, y.value = null, x.value = !1, mn(() => oe.value?.focus());
		}
		async function De() {
			if (!n || S.value || x.value) return;
			if (y.value = null, !k.value.price_sensor) {
				ye("price_sensor", i.value.missingPriceSensor);
				return;
			}
			if (!ie.value.trim()) {
				ye("feed", i.value.missingFeed);
				return;
			}
			let e = /^\d+(?:[.,]\d{1,2})?$/.test(ie.value.trim()) ? Number(ie.value.trim().replace(",", ".")) : NaN;
			if (!Number.isFinite(e) || e < 0 || e > 200) {
				ye("feed", i.value.invalidFeed);
				return;
			}
			let t = Number(A.value);
			if (String(A.value).trim() === "" || !Number.isInteger(t) || t < 0 || t > 100) {
				ye("pv_factor", i.value.invalidPvFactor);
				return;
			}
			S.value = !0, w.value = "saving", _.value = null;
			try {
				await n.configureTariff({
					revision: j.value,
					tariff_type: "dynamic",
					profile: {
						...k.value,
						price_attribute: k.value.price_attribute?.trim() || null,
						feed_in_price_ct_kwh: e,
						pv_factor: t
					}
				}), le || (Ee(), T.value = !0);
			} catch (e) {
				L(e);
			} finally {
				w.value = null, S.value = !1;
			}
		}
		async function Oe() {
			if (n && !S.value) {
				S.value = !0, w.value = "loading";
				try {
					await n.loadTariff(), le || (O.value = !1, E.value = !1, _.value = null, y.value = null, x.value = !1);
				} catch (e) {
					L(e);
				} finally {
					w.value = null, S.value = !1;
				}
			}
		}
		function ke() {
			re.value = !1, mn(() => se.value?.focus());
		}
		function Ae() {
			ce.value || M.value?.pending || M.value?.reset() !== !1 && ke();
		}
		async function je() {
			if (ce.value || M.value?.pending) return;
			let e = M.value;
			if (e) {
				ce.value = !0;
				try {
					await e.submit() && ke();
				} finally {
					ce.value = !1;
				}
			}
		}
		return (t, n) => (G(), K("div", Gu, [
			q("section", Ku, [
				q("div", qu, [q("div", Ju, [
					q("span", null, I(i.value.active), 1),
					q("strong", null, I(d.value), 1),
					q("button", {
						type: "button",
						disabled: !u.value || S.value || de.value,
						"aria-expanded": E.value,
						onClick: R
					}, I(i.value.change), 9, Yu)
				])]),
				E.value ? (G(), K("form", {
					key: 0,
					class: "electricity-choice",
					"aria-busy": w.value === "applying",
					onSubmit: Ga(Ce, ["prevent"])
				}, [
					q("fieldset", { disabled: S.value || !l.value }, [q("legend", Qu, I(i.value.active), 1), (G(), K(W, null, U(["time_of_use", "dynamic"], (e) => q("label", { key: e }, [Dn(q("input", {
						"onUpdate:modelValue": n[0] ||= (e) => D.value = e,
						type: "radio",
						name: "electricity-tariff",
						value: e
					}, null, 8, $u), [[Ra, D.value]]), q("span", null, [q("strong", null, I(e === "time_of_use" ? i.value.tou : i.value.dynamic), 1), q("small", null, I(e === "time_of_use" ? i.value.touHint : i.value.dynamicHint), 1)])])), 64))], 8, Zu),
					q("p", null, I(i.value.chooseHint), 1),
					Se.value ? (G(), K("p", ed, I(i.value.incomplete), 1)) : X("", !0),
					J(bo, { class: "electricity-actions" }, {
						default: En(() => [q("button", {
							type: "submit",
							disabled: S.value || !l.value || x.value
						}, I(w.value === "applying" ? i.value.applying : i.value.apply), 9, td), q("button", {
							type: "button",
							disabled: S.value,
							onClick: n[1] ||= (e) => {
								E.value = !1, _.value = null;
							}
						}, I(i.value.cancel), 9, nd)]),
						_: 1
					})
				], 40, Xu)) : X("", !0),
				w.value ? (G(), K("p", rd, I(i.value[w.value]), 1)) : X("", !0),
				_.value && !y.value && v.value !== "activation" ? (G(), K("p", id, I(_.value), 1)) : X("", !0),
				x.value && v.value !== "activation" ? (G(), K("button", {
					key: 3,
					type: "button",
					disabled: S.value || !l.value,
					onClick: Oe
				}, I(i.value.reload), 9, ad)) : X("", !0),
				T.value ? (G(), K("p", od, I(i.value.saved), 1)) : X("", !0),
				ee.value ? (G(), K("p", sd, I(i.value.tariffChanged), 1)) : X("", !0),
				!o.value && !_.value ? (G(), K("p", cd, I(i.value.loading), 1)) : X("", !0)
			]),
			c.value ? (G(), K("div", ld, [q("section", {
				class: "electricity-card electricity-price-card",
				"aria-label": i.value.prices
			}, [s.value === "time_of_use" ? (G(), oi(Bl, {
				key: 0,
				hass: e.hass,
				compact: "",
				onEditing: n[2] ||= (e) => ne.value = e,
				onSaved: be
			}, {
				"current-price": En(() => [q("div", dd, [q("span", fd, I(i.value.price) + " · " + I(i.value.current), 1), q("p", pd, [Y(I(N.value ?? i.value.unavailable), 1), N.value === null ? X("", !0) : (G(), K("span", md, " ct/kWh"))])])]),
				_: 1
			}, 8, ["hass"])) : s.value === "dynamic" ? (G(), K("section", {
				key: 1,
				class: "electricity-card electricity-prices",
				"aria-busy": w.value === "loading" || w.value === "saving"
			}, [
				q("header", null, [q("div", null, [q("h2", null, I(i.value.prices), 1)]), J(bo, null, {
					default: En(() => [q("button", {
						ref_key: "priceButton",
						ref: oe,
						type: "button",
						disabled: S.value || !u.value || E.value || O.value && (!l.value || x.value),
						"aria-expanded": O.value,
						onClick: n[3] ||= (e) => O.value ? De() : Te()
					}, I(w.value === "loading" ? i.value.loading : w.value === "saving" ? i.value.saving : O.value ? i.value.save : i.value.edit), 9, gd), O.value ? (G(), K("button", {
						key: 0,
						type: "button",
						disabled: S.value,
						onClick: Ee
					}, I(i.value.cancel), 9, _d)) : X("", !0)]),
					_: 1
				})]),
				q("div", vd, [q("span", yd, I(i.value.price) + " · " + I(i.value.current), 1), q("p", bd, [Y(I(N.value ?? i.value.unavailable), 1), N.value === null ? X("", !0) : (G(), K("span", xd, " ct/kWh"))])]),
				q("dl", Sd, [q("div", null, [q("dt", null, I(i.value.sourceSummary), 1), q("dd", null, I(ge.value), 1)]), q("div", null, [q("dt", null, I(i.value.feed), 1), q("dd", null, [Y(I(_e.value ?? i.value.unavailable), 1), _e.value === null ? X("", !0) : (G(), K(W, { key: 0 }, [Y(" ct/kWh")], 64))])])]),
				O.value ? (G(), K("form", {
					key: 0,
					ref_key: "pricesEditor",
					ref: ae,
					class: "electricity-price-editor",
					"aria-busy": w.value === "saving",
					novalidate: "",
					onSubmit: Ga(De, ["prevent"])
				}, [
					_.value && y.value ? (G(), K("p", {
						key: 0,
						id: V(b),
						role: "alert",
						class: "electricity-error"
					}, I(_.value), 9, wd)) : X("", !0),
					q("fieldset", { disabled: S.value || !l.value }, [
						q("p", Ed, I(i.value.priceHint), 1),
						q("div", Dd, [J(tc, {
							modelValue: k.value.price_sensor,
							"onUpdate:modelValue": n[4] ||= (e) => k.value.price_sensor = e,
							hass: e.hass,
							label: i.value.source,
							name: "dynamic_price_sensor",
							invalid: y.value === "price_sensor",
							"described-by": y.value === "price_sensor" ? V(b) : void 0
						}, null, 8, [
							"modelValue",
							"hass",
							"label",
							"invalid",
							"described-by"
						]), q("label", null, [Y(I(i.value.feed) + " (ct/kWh)", 1), Dn(q("input", {
							"onUpdate:modelValue": n[5] ||= (e) => ie.value = e,
							type: "text",
							inputmode: "decimal",
							name: "dynamic_feed",
							autocomplete: "off",
							required: "",
							"aria-invalid": y.value === "feed" || void 0,
							"aria-describedby": y.value === "feed" ? V(b) : void 0
						}, null, 8, Od), [[La, ie.value]])])]),
						q("p", kd, I(i.value.sourceHint), 1),
						q("p", Ad, I(i.value.feedHint), 1),
						q("div", jd, [J(tc, {
							modelValue: k.value.pv_sensor,
							"onUpdate:modelValue": n[6] ||= (e) => k.value.pv_sensor = e,
							hass: e.hass,
							label: i.value.pv,
							name: "dynamic_pv_sensor",
							invalid: y.value === "pv_sensor",
							"described-by": y.value === "pv_sensor" ? V(b) : void 0
						}, null, 8, [
							"modelValue",
							"hass",
							"label",
							"invalid",
							"described-by"
						])]),
						q("p", Md, I(i.value.pvHint), 1),
						he.value ? (G(), K("p", Nd, I(i.value.customSettings) + ": " + I(he.value), 1)) : X("", !0),
						q("details", Pd, [
							q("summary", null, I(i.value.advanced), 1),
							q("h3", null, I(i.value.sourceSettings), 1),
							q("div", Fd, [q("label", null, [Y(I(i.value.attribute), 1), Dn(q("input", {
								"onUpdate:modelValue": n[7] ||= (e) => k.value.price_attribute = e,
								name: "dynamic_price_attribute",
								type: "text",
								autocomplete: "off",
								"aria-invalid": y.value === "price_attribute" || void 0,
								"aria-describedby": y.value === "price_attribute" ? V(b) : void 0
							}, null, 8, Id), [[La, k.value.price_attribute]])]), q("label", null, [Y(I(i.value.unit), 1), Dn(q("select", {
								"onUpdate:modelValue": n[8] ||= (e) => k.value.price_unit = e,
								name: "dynamic_price_unit",
								"aria-invalid": y.value === "price_unit" || void 0,
								"aria-describedby": y.value === "price_unit" ? V(b) : void 0
							}, [(G(!0), K(W, null, U(i.value.units, (e, t) => (G(), K("option", {
								key: t,
								value: t
							}, I(e), 9, Rd))), 128))], 8, Ld), [[za, k.value.price_unit]])])]),
							q("p", zd, I(i.value.attributeHint), 1),
							q("p", Bd, I(i.value.unitHint), 1),
							q("div", Vd, [q("label", null, [Y(I(i.value.pvFactor), 1), Dn(q("input", {
								"onUpdate:modelValue": n[9] ||= (e) => A.value = e,
								name: "dynamic_pv_factor",
								type: "number",
								min: "0",
								max: "100",
								step: "1",
								"aria-invalid": y.value === "pv_factor" || void 0,
								"aria-describedby": y.value === "pv_factor" ? V(b) : void 0
							}, null, 8, Hd), [[La, A.value]])])]),
							q("p", Ud, I(i.value.pvFactorHint), 1)
						])
					], 8, Td),
					J(bo, { class: "electricity-actions" }, {
						default: En(() => [q("button", {
							type: "submit",
							disabled: S.value || !l.value || x.value
						}, I(w.value === "saving" ? i.value.saving : i.value.save), 9, Wd), q("button", {
							type: "button",
							disabled: S.value,
							onClick: Ee
						}, I(i.value.cancel), 9, Gd)]),
						_: 1
					})
				], 40, Cd)) : X("", !0)
			], 8, hd)) : X("", !0), q("details", Kd, [
				q("summary", null, I(i.value.chart), 1),
				s.value === "dynamic" ? (G(), K("div", {
					key: 0,
					class: "electricity-days",
					"aria-label": i.value.price
				}, [(G(), K(W, null, U(["today", "tomorrow"], (e) => q("button", {
					key: e,
					type: "button",
					"aria-pressed": g.value === e,
					onClick: (t) => g.value = e
				}, I(e === "today" ? i.value.today : i.value.tomorrow), 9, Jd)), 64))], 8, qd)) : X("", !0),
				q("p", Yd, [Y(I(g.value === "today" ? i.value.today : i.value.tomorrow), 1), fe.value ? (G(), K("span", Xd, " · " + I(fe.value), 1)) : X("", !0)]),
				J(ru, {
					series: m.value,
					hass: e.hass,
					loading: h.value
				}, null, 8, [
					"series",
					"hass",
					"loading"
				])
			])], 8, ud), c.value ? (G(), K("section", Zd, [
				q("header", null, [q("div", null, [q("h2", null, I(i.value.charging), 1)]), J(bo, null, {
					default: En(() => [q("button", {
						ref_key: "chargingButton",
						ref: se,
						type: "button",
						disabled: E.value || ce.value || M.value?.pending,
						"aria-busy": ce.value,
						"aria-expanded": re.value,
						onClick: n[10] ||= (e) => re.value ? je() : re.value = !0
					}, I(ce.value ? i.value.saving : re.value ? i.value.done : i.value.edit), 9, Qd), re.value ? (G(), K("button", {
						key: 0,
						type: "button",
						disabled: ce.value || M.value?.pending,
						onClick: Ae
					}, I(i.value.cancel), 9, $d)) : X("", !0)]),
					_: 1
				})]),
				c.value ? (G(), K("section", ef, [
					q("label", {
						class: "electricity-master",
						"aria-busy": C.value !== null
					}, [q("input", {
						type: "checkbox",
						role: "switch",
						checked: p.value === !0,
						"aria-describedby": _.value && v.value === "activation" ? "electricity-master-status electricity-activation-error" : "electricity-master-status",
						disabled: !u.value || S.value || p.value === null || E.value || de.value,
						onChange: we
					}, null, 40, nf), Y(I(i.value.automatic), 1)], 8, tf),
					q("p", rf, I(C.value === null ? "" : C.value ? i.value.turningOn : i.value.turningOff), 1),
					_.value && v.value === "activation" ? (G(), K("p", af, I(_.value), 1)) : X("", !0),
					x.value && v.value === "activation" ? (G(), K("button", {
						key: 1,
						type: "button",
						disabled: S.value || !l.value,
						onClick: Oe
					}, I(i.value.reload), 9, of)) : X("", !0),
					l.value ? u.value ? de.value || E.value ? (G(), K("p", lf, I(i.value.editFirst), 1)) : (G(), K("p", uf, I(p.value === null ? i.value.unavailable : p.value ? i.value.activationOn : i.value.activationOff), 1)) : (G(), K("p", cf, I(i.value.readonly), 1)) : (G(), K("p", sf, I(i.value.disconnected), 1))
				])) : X("", !0),
				s.value === "dynamic" ? (G(), oi(ku, {
					key: 1,
					ref_key: "chargingSettings",
					ref: M,
					editing: re.value,
					onApply: je
				}, null, 8, ["editing"])) : X("", !0),
				s.value === "time_of_use" ? (G(), oi(Wu, {
					key: 2,
					ref_key: "chargingSettings",
					ref: M,
					editing: re.value,
					hass: e.hass,
					onApply: je
				}, null, 8, ["editing", "hass"])) : X("", !0),
				re.value ? X("", !0) : (G(), K("div", df, [(G(!0), K(W, null, U(me.value, (e) => (G(), K(W, { key: e?.metadata.entity_id }, [e?.error ? (G(), K("p", ff, I(e.name) + ": " + I(e.error), 1)) : e?.pending ? (G(), K("p", pf, I(e.name) + ": " + I(i.value.entityPending), 1)) : X("", !0)], 64))), 128))])),
				re.value ? (G(), K("div", mf, [J(bo, {
					class: "electricity-actions",
					"aria-busy": ce.value
				}, {
					default: En(() => [q("button", {
						type: "button",
						disabled: E.value || ce.value || M.value?.pending,
						onClick: je
					}, I(ce.value ? i.value.saving : i.value.done), 9, hf), q("button", {
						type: "button",
						disabled: ce.value || M.value?.pending,
						onClick: Ae
					}, I(i.value.cancel), 9, gf)]),
					_: 1
				}, 8, ["aria-busy"]), ce.value ? (G(), K("p", _f, I(i.value.entityPending), 1)) : X("", !0)])) : X("", !0),
				s.value === "dynamic" ? (G(), K("div", vf, [J(Qo, {
					domain: "sensor",
					"entity-key": "price_charge_status_text"
				})])) : X("", !0),
				c.value ? (G(), K("section", {
					key: 6,
					class: "electricity-plan",
					"aria-label": i.value.details
				}, [
					s.value === "time_of_use" ? X("", !0) : (G(), K("h3", bf, I(i.value.details), 1)),
					q("dl", xf, [q("div", null, [q("dt", null, I(i.value.pvSummary), 1), q("dd", null, I(ve.value), 1)])]),
					s.value === "time_of_use" ? (G(), oi(wc, {
						key: 1,
						hass: e.hass
					}, null, 8, ["hass"])) : (G(), K(W, { key: 2 }, [
						J(Qo, {
							domain: "sensor",
							"entity-key": "price_charge_active_text"
						}),
						J(Qo, {
							domain: "sensor",
							"entity-key": "price_charge_status_text"
						}),
						J(Qo, {
							domain: "sensor",
							"entity-key": "price_charge_next_start"
						}),
						P.value === null ? X("", !0) : (G(), K("p", Sf, [Y(I(i.value.plannedPv) + ": ", 1), q("strong", null, I(P.value) + " kWh", 1)]))
					], 64))
				], 8, yf)) : X("", !0)
			])) : X("", !0)])) : X("", !0),
			c.value ? (G(), K("p", Cf, I(i.value.gross), 1)) : X("", !0)
		]));
	}
}), [["styles", [".electricity-tariff-view{gap:16px;min-width:0;margin-top:12px;display:grid}.electricity-card{border:1px solid var(--divider-color,#ddd);border-radius:var(--ha-card-border-radius,12px);background:var(--card-background-color,#fff);min-width:0;padding:16px 18px}.electricity-card h2{margin:0;font-size:18px}.electricity-card h3{margin:20px 0 10px;font-size:16px}.electricity-card p{margin:10px 0 0;line-height:1.6}.electricity-card button{font:inherit;cursor:pointer;border:1px solid var(--divider-color,#ddd);min-height:44px;color:var(--primary-color,#03a9f4);background:0 0;border-radius:7px;padding:8px 12px}.electricity-card button:disabled{opacity:.5;cursor:default}.electricity-card header,.electricity-tariff-bar__row{flex-wrap:wrap;justify-content:space-between;align-items:center;gap:16px;display:flex}.electricity-card header>div:not(.editor-actions){flex:1;min-width:0}.electricity-card header>.editor-actions{white-space:nowrap;flex-shrink:0}.electricity-active{flex-wrap:wrap;align-items:center;gap:10px;display:flex}.electricity-active>span,.electricity-muted{color:var(--secondary-text-color,#666)}.electricity-master{cursor:pointer;align-items:center;gap:10px;min-height:44px;display:flex}.electricity-master-status:empty{display:none}.electricity-master-status{border-left:3px solid var(--primary-color,#03a9f4);background:var(--secondary-background-color,#f5f5f5);padding:10px 14px;font-weight:500}.electricity-activation .electricity-master{margin-top:0;font-weight:600}.electricity-price-details{margin-top:16px}.electricity-master[aria-busy=true]{cursor:progress}.electricity-master input{width:22px;height:22px;accent-color:var(--primary-color,#03a9f4);flex-shrink:0}.electricity-choice{border-top:1px solid var(--divider-color,#ddd);margin-top:16px;padding-top:16px}.electricity-choice fieldset{border:0;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;min-width:0;padding:0;display:grid}.electricity-choice fieldset>label{border:1px solid var(--divider-color,#ddd);cursor:pointer;border-radius:8px;gap:12px;padding:14px;display:flex}.electricity-choice input{accent-color:var(--primary-color,#03a9f4);flex-shrink:0;width:20px;height:20px}.electricity-choice strong,.electricity-choice small{display:block}.electricity-choice small{color:var(--secondary-text-color,#666);margin-top:5px;font-size:14px}.electricity-actions{margin-top:16px}.electricity-current-price{font-size:32px;font-weight:500;line-height:1.1!important}.electricity-current-price span{font-size:16px;font-weight:400}.electricity-days{gap:6px;margin-top:12px;display:flex}.electricity-days [aria-pressed=true]{background:var(--secondary-background-color,#eee);border-color:var(--primary-color,#03a9f4)}.electricity-day{margin:20px 0!important}.electricity-error{color:var(--error-color,#db4437)}.electricity-price-editor [aria-invalid=true]{border-color:var(--error-color,#db4437);outline:1px solid var(--error-color,#db4437)}.electricity-fields{grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:16px;display:grid}.electricity-fields>label{flex-direction:column;gap:6px;min-width:0;font-size:14px;display:flex}.electricity-fields input,.electricity-fields select{width:100%;min-width:0;min-height:44px;font:inherit;color:var(--primary-text-color,#222);background:var(--card-background-color,#fff);border:1px solid var(--divider-color,#ccc);border-radius:6px;padding:10px}.electricity-price-editor fieldset{border:0;min-width:0;margin:0;padding:0}.electricity-price-advanced{border-top:1px solid var(--divider-color,#ddd);margin-top:16px;padding-top:12px}.electricity-price-advanced>summary{cursor:pointer;align-content:center;min-height:44px}.dynamic-charging-settings .entity-control,.electricity-charging-editor .entity-control{margin-top:12px}.electricity-price-details>summary{cursor:pointer;align-content:center;min-height:44px;font-size:14px;font-weight:500;display:list-item}.electricity-plan>.charge-plan{box-shadow:none;border:0;padding:16px 0 0}.electricity-sr-only{clip-path:inset(50%);width:1px;height:1px;position:absolute;overflow:hidden}@media (max-width:700px){.electricity-tariff-bar__row{flex-direction:column;align-items:flex-start}.electricity-fields,.electricity-choice fieldset{grid-template-columns:minmax(0,1fr)}.electricity-card{padding:16px}.electricity-card header{align-items:flex-start}.electricity-current-price{font-size:28px}}.electricity-columns{align-items:start;gap:16px;min-width:0;display:grid}.electricity-card.electricity-tariff-bar{background:0 0;border:0;padding:0}.electricity-tariff-bar__row{justify-content:flex-end}.electricity-active>strong{color:var(--primary-text-color,#212121)}.electricity-price-card{container:sax-tariff-prices/inline-size}.electricity-card.electricity-prices{border:0;border-radius:0;padding:0}.electricity-prices>header,.electricity-charging>header{border-bottom:1px solid var(--divider-color,#ddd);margin-bottom:14px;padding-bottom:12px}.electricity-card .electricity-current-price{margin:3px 0 0}.electricity-current{min-width:0}.electricity-prices>.electricity-current{margin:14px 0}.electricity-activation{background:var(--secondary-background-color,#f5f5f5);border-radius:8px;margin-bottom:12px;padding:8px 12px 12px}.electricity-activation>p{color:var(--secondary-text-color,#666);margin-top:2px}.electricity-summary-rows{margin:0}.electricity-summary-rows>div{border-bottom:1px solid var(--divider-color,#ddd);justify-content:space-between;align-items:center;gap:8px 16px;min-height:41px;padding:7px 0;display:flex}.electricity-summary-rows dt{color:var(--secondary-text-color,#666)}.electricity-summary-rows dd{text-align:right;overflow-wrap:anywhere;min-width:0;margin:0}.electricity-targets{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:12px 0;display:grid}.electricity-target{background:var(--secondary-background-color,#f5f5f5);border-radius:8px;flex-direction:column;gap:4px;min-width:0;padding:10px 12px;display:flex}.electricity-target>span{color:var(--secondary-text-color,#666);font-size:14px}.electricity-target>strong{overflow-wrap:anywhere;font-size:24px;font-weight:500}.electricity-charge-status .entity-value{padding:12px 0}.electricity-plan,.electricity-price-details,.tou-charging-rules{border-top:1px solid var(--divider-color,#ddd);margin-top:10px;padding-top:0}.tou-charging-rules>summary{cursor:pointer;align-content:center;min-height:44px}.electricity-footnote{color:var(--secondary-text-color,#666);margin:0;font-size:13px}@container sax-content (width>=860px){.electricity-columns{grid-template-columns:minmax(0,1.14fr) minmax(0,1fr)}.electricity-tariff-view{margin-top:-36px}.electricity-tariff-bar__row{min-height:44px;padding-left:260px}}@container sax-tariff-prices (width<=560px){.electricity-fields{grid-template-columns:minmax(0,1fr);gap:10px}}"]]]), Tf = { class: "savings-view" }, Ef = { class: "savings-overview" }, Df = ["aria-labelledby"], Of = ["id"], kf = ["aria-labelledby"], Af = ["id"], jf = {
	key: 0,
	class: "savings-progress"
}, Mf = ["id"], Nf = { class: "savings-large" }, Pf = [
	"role",
	"aria-labelledby",
	"aria-valuemin",
	"aria-valuemax",
	"aria-valuenow"
], Ff = {
	key: 1,
	class: "savings-rows"
}, If = { key: 0 }, Lf = { key: 1 }, Rf = { key: 2 }, zf = { key: 3 }, Bf = ["aria-label"], Vf = { class: "savings-large" }, Hf = ["aria-labelledby"], Uf = ["id"], Wf = ["for"], Gf = ["id", "max"], Kf = ["for"], qf = ["id", "min"], Jf = { type: "submit" }, Yf = ["disabled"], Xf = {
	key: 0,
	role: "status"
}, Zf = {
	key: 1,
	role: "alert"
}, Qf = { class: "savings-selected-dates" }, $f = { class: "savings-large" }, ep = ["id"], tp = { class: "savings-chart-hint" }, np = [
	"viewBox",
	"aria-labelledby",
	"aria-describedby"
], rp = ["id"], ip = [
	"x1",
	"x2",
	"y1",
	"y2"
], ap = ["x"], op = ["x"], sp = ["x"], cp = ["x"], lp = [
	"x",
	"y",
	"width",
	"height"
], up = { class: "savings-chart-table" }, dp = { class: "savings-table-scroll" }, fp = { class: "savings-table" }, pp = {
	key: 1,
	class: "savings-empty"
}, mp = { class: "savings-card savings-explanation" }, hp = {
	key: 1,
	class: "savings-card savings-status",
	role: "status"
}, gp = /*#__PURE__*/ go(/* @__PURE__ */ Bn({
	__name: "SavingsView",
	props: {
		hass: { type: Object },
		entryId: { type: String }
	},
	setup(e) {
		let t = e, n = An(lo), r = Vn(), i = Z(() => n?.language.value === "de"), a = Z(() => i.value ? {
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
			let n = ro(e, t.hass);
			return n === null ? a.value.unavailable : `${n} €`;
		}, h = (e) => io(e, t.hass) ?? a.value.unavailable, g = (e) => io(`${e}T12:00:00Z`, t.hass, {
			dateStyle: "medium",
			timeZone: "UTC"
		}) ?? e, _ = Z(() => {
			let e = d.value?.available ? d.value.state?.state : void 0;
			return e === "active" || e === "storage_error" ? null : e === "disabled" || e === "price_unavailable" || e === "origin_unavailable" || e === "partial_price_coverage" ? a.value[e] : a.value.missing;
		}), v = so(() => t.hass, () => t.entryId, () => u.value?.metadata.entity_id), y = /* @__PURE__ */ B(""), b = /* @__PURE__ */ B(""), x = null;
		H(v.data, (e) => {
			e && ((!y.value && !b.value || y.value === x?.start && b.value === x?.end) && (y.value = e.selected.start_date, b.value = e.selected.end_date), x = {
				start: e.selected.start_date,
				end: e.selected.end_date
			});
		}), H(() => t.entryId, () => {
			y.value = "", b.value = "", x = null;
		});
		let S = Z(() => v.error.value === "invalid" ? a.value.invalid : v.error.value === "failed" ? a.value.failed : v.error.value === "unavailable" || v.data.value?.status === "recorder_unavailable" ? a.value.noRecorder : null), C = [
			"day",
			"week",
			"month",
			"year"
		], w = Z(() => v.data.value?.selected.buckets ?? []), T = /* @__PURE__ */ B(null), ee = /* @__PURE__ */ B(720);
		H(T, (e, t, n) => {
			if (!e) return;
			let r = (e) => {
				Number.isFinite(e) && e > 0 && (ee.value = e);
			};
			if (r(e.getBoundingClientRect().width), typeof ResizeObserver > "u") return;
			let i = new ResizeObserver((e) => {
				for (let t of e) r(t.contentRect.width);
			});
			i.observe(e), n(() => i.disconnect());
		});
		let E = Z(() => {
			let e = w.value.map((e) => Q(e.change)), n = Math.max(0, ...e.map((e) => e ?? 0)), r = Math.min(0, ...e.map((e) => e ?? 0)), i = n - r || 1, a = (e) => 20 + (n - e) / i * 180, o = v.data.value?.selected, s = Date.parse(o?.start ?? ""), c = Date.parse(o?.end ?? ""), l = c - s, u = ro(n, t.hass) ?? "", d = ro(r, t.hass) ?? "", f = Math.max(56, Math.max(u.length, d.length) * 7.1 + 12), p = ee.value - 24, m = Math.max(1, p - f), g = (e) => f + Math.max(0, Math.min(1, (Date.parse(e) - s) / l)) * m;
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
		}), D = Z(() => w.value.some((e) => Q(e.change) !== null)), te = (e) => io(e, t.hass, v.data.value?.selected.period === "hour" ? { timeStyle: "short" } : v.data.value?.selected.period === "month" ? {
			month: "short",
			year: "numeric"
		} : {
			day: "2-digit",
			month: "short"
		}) ?? e;
		return (t, i) => (G(), K("div", Tf, [
			q("div", Ef, [o.value?.available && o.value.state?.state === "off" ? (G(), K("section", {
				key: 0,
				class: "savings-card savings-payback",
				"aria-labelledby": `${V(r)}-investment`
			}, [q("h2", { id: `${V(r)}-investment` }, I(a.value.payback), 9, Of), q("p", null, I(a.value.investment), 1)], 8, Df)) : o.value?.available && o.value.state?.state === "on" && (s.value || c.value || l.value || u.value || d.value) ? (G(), K("section", {
				key: 1,
				class: "savings-card savings-payback",
				"aria-labelledby": `${V(r)}-payback`
			}, [
				q("h2", { id: `${V(r)}-payback` }, I(a.value.payback), 9, Af),
				s.value ? (G(), K("div", jf, [
					q("h3", { id: `${V(r)}-progress` }, I(s.value.name), 9, Mf),
					q("p", Nf, I(f.value === null ? a.value.unavailable : `${V(ro)(f.value, e.hass)} %`), 1),
					q("div", {
						class: "savings-progress__track",
						role: p.value === null ? void 0 : "meter",
						"aria-labelledby": `${V(r)}-progress`,
						"aria-valuemin": p.value === null ? void 0 : 0,
						"aria-valuemax": p.value === null ? void 0 : 100,
						"aria-valuenow": p.value ?? void 0
					}, [p.value === null ? X("", !0) : (G(), K("span", {
						key: 0,
						style: M({ width: `${p.value}%` })
					}, null, 4))], 8, Pf)
				])) : X("", !0),
				c.value || l.value || u.value || d.value ? (G(), K("dl", Ff, [
					c.value ? (G(), K("div", If, [q("dt", null, I(c.value.name), 1), q("dd", null, I(m(c.value.available ? c.value.state?.state : null)), 1)])) : X("", !0),
					l.value ? (G(), K("div", Lf, [q("dt", null, I(a.value.prior), 1), q("dd", null, I(m(l.value.available ? l.value.state?.attributes.prior_result_eur ?? l.value.state?.attributes.prior_result_eur_formatted : null)), 1)])) : X("", !0),
					u.value ? (G(), K("div", Rf, [q("dt", null, I(a.value.net), 1), q("dd", null, I(m(u.value.available ? u.value.state?.state : null)), 1)])) : X("", !0),
					d.value ? (G(), K("div", zf, [q("dt", null, I(a.value.started), 1), q("dd", null, I(h(d.value.available ? d.value.state?.attributes.economics_started_at : null)), 1)])) : X("", !0)
				])) : X("", !0)
			], 8, kf)) : X("", !0), u.value ? (G(), K("section", {
				key: 2,
				class: "savings-periods",
				"aria-label": a.value.periods
			}, [(G(), K(W, null, U(C, (e) => q("article", {
				key: e,
				class: "savings-card"
			}, [q("h2", null, I(a.value[e]), 1), q("p", Vf, I(V(v).loading.value ? "…" : m(V(v).data.value?.periods[e].change)), 1)])), 64))], 8, Bf)) : X("", !0)]),
			J(Bl, {
				hass: e.hass,
				class: "savings-tariff"
			}, null, 8, ["hass"]),
			u.value ? (G(), K("section", {
				key: 0,
				class: "savings-card savings-range",
				"aria-labelledby": `${V(r)}-range`
			}, [
				q("h2", { id: `${V(r)}-range` }, I(a.value.range), 9, Uf),
				q("form", {
					class: "savings-dates",
					onSubmit: i[3] ||= Ga((e) => V(v).select(y.value, b.value), ["prevent"])
				}, [
					q("label", { for: `${V(r)}-from` }, [Y(I(a.value.from), 1), Dn(q("input", {
						id: `${V(r)}-from`,
						"onUpdate:modelValue": i[0] ||= (e) => y.value = e,
						type: "date",
						required: "",
						max: b.value || void 0
					}, null, 8, Gf), [[La, y.value]])], 8, Wf),
					q("label", { for: `${V(r)}-to` }, [Y(I(a.value.to), 1), Dn(q("input", {
						id: `${V(r)}-to`,
						"onUpdate:modelValue": i[1] ||= (e) => b.value = e,
						type: "date",
						required: "",
						min: y.value || void 0
					}, null, 8, qf), [[La, b.value]])], 8, Kf),
					q("button", Jf, I(a.value.apply), 1),
					q("button", {
						type: "button",
						disabled: V(v).loading.value,
						onClick: i[2] ||= (...e) => V(v).refresh && V(v).refresh(...e)
					}, I(a.value.refresh), 9, Yf)
				], 32),
				V(v).loading.value ? (G(), K("p", Xf, I(a.value.loading), 1)) : S.value ? (G(), K("p", Zf, I(S.value), 1)) : V(v).data.value ? (G(), K(W, { key: 2 }, [
					q("p", Qf, I(g(V(v).data.value.selected.start_date)) + " – " + I(g(V(v).data.value.selected.end_date)), 1),
					q("h3", null, I(a.value.selected), 1),
					q("p", $f, I(m(V(v).data.value.selected.change)), 1),
					q("h3", { id: `${V(r)}-chart` }, I(a.value.chart), 9, ep),
					q("p", tp, I(a.value.chartHint), 1),
					D.value ? (G(), K(W, { key: 0 }, [(G(), K("svg", {
						ref_key: "chartElement",
						ref: T,
						class: "savings-chart",
						viewBox: `0 0 ${ee.value} 240`,
						role: "img",
						"aria-labelledby": `${V(r)}-chart`,
						"aria-describedby": `${V(r)}-chart-description`
					}, [
						q("desc", { id: `${V(r)}-chart-description` }, I(a.value.net) + ": " + I(m(V(v).data.value.selected.change)) + ". " + I(a.value.table) + ". ", 9, rp),
						q("line", {
							x1: E.value.left - 2,
							x2: E.value.right + 2,
							y1: E.value.zero,
							y2: E.value.zero,
							class: "savings-chart__axis"
						}, null, 8, ip),
						q("text", {
							x: E.value.left - 8,
							y: "24",
							"text-anchor": "end"
						}, I(E.value.highLabel), 9, ap),
						q("text", {
							x: E.value.left - 8,
							y: "204",
							"text-anchor": "end"
						}, I(E.value.lowLabel), 9, op),
						i[4] ||= q("text", {
							x: "10",
							y: "226"
						}, "EUR", -1),
						w.value.length ? (G(), K("text", {
							key: 0,
							x: E.value.left,
							y: "226"
						}, I(te(E.value.start)), 9, sp)) : X("", !0),
						w.value.length > 1 ? (G(), K("text", {
							key: 1,
							x: E.value.right,
							y: "226",
							"text-anchor": "end"
						}, I(te(E.value.end)), 9, cp)) : X("", !0),
						(G(!0), K(W, null, U(E.value.bars, (e, t) => (G(), K("rect", {
							key: t,
							x: e.x,
							y: e.y,
							width: e.width,
							height: e.height,
							class: N(["savings-chart__bar", { "savings-chart__bar--negative": (e.value ?? 0) < 0 }])
						}, [q("title", null, I(e.label) + ": " + I(m(e.value)), 1)], 10, lp))), 128))
					], 8, np)), q("details", up, [q("summary", null, I(a.value.table), 1), q("div", dp, [q("table", fp, [q("thead", null, [q("tr", null, [
						q("th", null, I(a.value.from), 1),
						q("th", null, I(a.value.to), 1),
						q("th", null, I(a.value.net), 1)
					])]), q("tbody", null, [(G(!0), K(W, null, U(E.value.bars, (e, t) => (G(), K("tr", { key: t }, [
						q("td", null, I(e.label), 1),
						q("td", null, I(h(e.end)), 1),
						q("td", null, I(m(e.value)), 1)
					]))), 128))])])])])], 64)) : X("", !0),
					!D.value || V(v).data.value.selected.change === null ? (G(), K("p", pp, I(V(v).data.value.selected.change === null ? a.value.noData : a.value.noChartData), 1)) : X("", !0)
				], 64)) : X("", !0)
			], 8, Hf)) : X("", !0),
			q("details", mp, [
				q("summary", null, I(a.value.explain), 1),
				q("p", null, I(a.value.netHint), 1),
				q("p", null, I(a.value.calendarHint), 1),
				q("p", null, I(a.value.rangeHint), 1)
			]),
			_.value && V(n)?.ready.value ? (G(), K("p", hp, I(_.value), 1)) : X("", !0)
		]));
	}
}), [["styles", [".savings-view{gap:20px;min-width:0;margin-top:24px;display:grid}.savings-overview{display:contents}.savings-card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.savings-card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.savings-card h3{margin:20px 0 8px;font-size:16px;font-weight:500}.savings-card p{overflow-wrap:anywhere;line-height:1.6}.savings-card p:last-child{margin-bottom:0}.savings-large{font-variant-numeric:tabular-nums;margin:0 0 12px;font-size:28px;font-weight:500}.savings-progress__track{background:var(--divider-color,#e0e0e0);border-radius:8px;height:16px;overflow:hidden}.savings-progress__track span{background:var(--info-color,#039be5);height:100%;display:block}.savings-rows{margin:20px 0 0}.savings-rows>div{border-bottom:1px solid var(--divider-color,#e0e0e0);justify-content:space-between;gap:16px;padding:12px 0;line-height:1.5;display:flex}.savings-rows>div:last-child{border-bottom:0;padding-bottom:0}.savings-rows dd{text-align:right;font-variant-numeric:tabular-nums;margin:0}.savings-periods{grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:16px;display:grid}.savings-periods h2{font-size:16px}.savings-table-scroll{overflow-x:auto}.savings-table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%;line-height:1.5}.savings-table th,.savings-table td{text-align:left;border-bottom:1px solid var(--divider-color,#e0e0e0);padding:10px 8px}.savings-table th:last-child,.savings-table td:last-child{text-align:right}.savings-dates{flex-wrap:wrap;align-items:end;gap:16px;display:flex}.savings-dates label{flex:180px;gap:8px;min-width:0;display:grid}.savings-dates input,.savings-dates button{box-sizing:border-box;font:inherit;border:1px solid var(--divider-color,#bdbdbd);background:var(--ha-card-background,var(--card-background-color,#fff));min-height:44px;color:var(--primary-text-color,#212121);border-radius:6px;padding:10px 12px}.savings-dates input{--lightningcss-light:initial;--lightningcss-dark: ;color-scheme:light dark;width:100%}@media (prefers-color-scheme:dark){.savings-dates input{--lightningcss-light: ;--lightningcss-dark:initial}}.savings-dates button{cursor:pointer;color:var(--primary-color,#0288d1)}.savings-dates button:disabled{opacity:.6;cursor:default}.savings-dates :focus-visible,.savings-card summary:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:3px}.savings-selected-dates,.savings-empty{color:var(--secondary-text-color,#666)}.savings-chart{width:100%;height:auto;display:block;overflow:visible}.savings-chart text{fill:var(--secondary-text-color,#666);font-size:12px}.savings-chart__axis{stroke:var(--primary-text-color,#212121);stroke-width:1px}.savings-chart__bar{fill:var(--info-color,#039be5)}.savings-chart__bar--negative{fill:var(--error-color,#db4437)}.savings-card summary{cursor:pointer;min-height:24px;font-weight:500;line-height:1.6}.savings-chart-table{margin-top:16px}.savings-status{margin:0;line-height:1.6}@container sax-content (width>=860px){.savings-view{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;gap:16px;margin-top:16px}.savings-view>*{grid-column:1/-1}.savings-overview{gap:16px;min-width:0;display:grid}.savings-overview:empty{display:none}.savings-view:has(>.savings-overview>section):has(>.savings-tariff)>:is(.savings-overview,.savings-tariff){grid-column:auto}.savings-card{padding:18px}.savings-card h2{margin-bottom:12px;font-size:16px}.savings-card h3{margin-top:16px;font-size:14px}.savings-card p{margin-top:10px;line-height:1.5}.savings-progress h3{margin-top:0}.savings-card .savings-large{margin-top:0;margin-bottom:8px;font-size:24px}.savings-rows{margin-top:12px}.savings-rows>div{gap:12px;padding:8px 0}.savings-rows dt{min-width:0}.savings-rows dd{flex-shrink:0;max-width:58%}.savings-periods{grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.savings-view:has(>.savings-tariff) .savings-periods{grid-template-columns:repeat(2,minmax(0,1fr))}.savings-periods .savings-card{padding:14px 16px}.savings-periods h2{margin-bottom:6px;font-size:14px}.savings-periods .savings-large{margin-bottom:0;font-size:22px}.savings-table th,.savings-table td{padding:7px 8px}.savings-dates{gap:12px}.savings-dates label{flex:0 220px;gap:6px}.savings-range .savings-selected-dates{margin-bottom:8px}.savings-range .savings-chart-hint{margin-top:0;margin-bottom:8px}.savings-chart-table{margin-top:12px}}@media (max-width:600px){.savings-view{gap:16px}.savings-card{padding:20px}.savings-rows>div{flex-wrap:wrap;gap:4px 16px}.savings-rows dd{margin-left:auto}}"]]]), _p = ["lang"], vp = { class: "header" }, yp = ["aria-label"], bp = ["aria-label"], xp = [
	"href",
	"aria-current",
	"onClick"
], Sp = {
	key: 0,
	class: "status",
	role: "alert"
}, Cp = {
	key: 1,
	class: "introduction"
}, wp = {
	key: 0,
	class: "status",
	role: "status"
}, Tp = {
	key: 1,
	class: "status",
	role: "status"
}, Ep = {
	key: 6,
	class: "status"
}, Dp = ["href"], Op = /* @__PURE__ */ Da(/* @__PURE__ */ go(/* @__PURE__ */ Bn({
	__name: "Panel.ce",
	props: {
		hass: { type: Object },
		narrow: { type: Boolean },
		panel: { type: Object },
		route: { type: Object }
	},
	setup(e) {
		let t = e, n = Aa(), r = mo(() => t.hass, () => t.panel?.config?.entry_id);
		kn(lo, r);
		let i = Z(() => t.hass?.language.toLowerCase().startsWith("de") ? "de" : "en"), a = Z(() => to[i.value]), o = Z(() => !t.hass?.kioskMode && (t.narrow || t.hass?.dockedSidebar === "always_hidden")), s = Z(() => `/${t.panel?.url_path || "sax-power-vue"}`), c = /* @__PURE__ */ B(t.route?.path ?? window.location.pathname), l = $a, u = Z(() => eo(c.value, s.value)), d = Z(() => ["dynamisches-laden", "ladeautomatik"].includes(u.value) ? "stromtarif" : u.value);
		H([() => r.ready.value, () => {
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
		let f = Z(() => $a.find((e) => e.path === d.value)), p = /* @__PURE__ */ B();
		H(() => t.route?.path, (e) => {
			e !== void 0 && (c.value = e);
		}), H([u, d], ([e, t]) => {
			if (e === t) return;
			let n = `${s.value}/${t}`;
			c.value = n, window.history.replaceState(null, "", n), window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: !0 } })), mn(() => p.value?.focus());
		}, { immediate: !0 });
		function m() {
			c.value = window.location.pathname;
		}
		Zn(() => {
			window.addEventListener("popstate", m), window.addEventListener("location-changed", m);
		}), Qn(() => {
			window.removeEventListener("popstate", m), window.removeEventListener("location-changed", m);
		});
		function h(e, t) {
			e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || (e.preventDefault(), window.location.pathname !== t && (window.history.pushState(null, "", t), window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: !1 } }))), m(), mn(() => p.value?.focus()));
		}
		function g() {
			n?.dispatchEvent(new CustomEvent("hass-toggle-menu", {
				bubbles: !0,
				composed: !0
			}));
		}
		return (t, n) => (G(), K("div", {
			class: N(["dashboard", { narrow: e.narrow }]),
			lang: i.value
		}, [
			q("header", vp, [o.value ? (G(), K("button", {
				key: 0,
				class: "menu-button",
				type: "button",
				"aria-label": a.value.menu,
				onClick: g
			}, [...n[1] ||= [q("svg", {
				viewBox: "0 0 24 24",
				"aria-hidden": "true"
			}, [q("path", { d: "M4 6h16M4 12h16M4 18h16" })], -1)]], 8, yp)) : X("", !0), n[2] ||= q("div", { class: "brand" }, [q("svg", {
				class: "brand-icon",
				viewBox: "0 0 24 24",
				"aria-hidden": "true"
			}, [q("path", { d: "M9 3h6M8 5h8a1 1 0 0 1 1 1v14H7V6a1 1 0 0 1 1-1Z" }), q("path", { d: "m13 8-3 5h4l-3 5" })]), q("span", null, "SAX Power")], -1)]),
			q("nav", {
				class: "navigation",
				"aria-label": a.value.navigation
			}, [(G(!0), K(W, null, U(V(l), (e) => (G(), K("a", {
				key: e.path,
				href: `${s.value}/${e.path}`,
				"aria-current": d.value === e.path ? "page" : void 0,
				onClick: (t) => h(t, `${s.value}/${e.path}`)
			}, I(e[i.value]), 9, xp))), 128))], 8, bp),
			q("main", null, [
				V(r).error.value ? (G(), K("p", Sp, I(V(r).error.value), 1)) : X("", !0),
				d.value === "stromtarif" ? X("", !0) : (G(), K("p", Cp, I(a.value.introduction), 1)),
				(G(), K("section", {
					key: e.panel?.config?.entry_id,
					class: N(["section", { "section--tariff": d.value === "stromtarif" }]),
					"aria-labelledby": "section-heading"
				}, [q("h1", {
					id: "section-heading",
					ref_key: "heading",
					ref: p,
					tabindex: "-1"
				}, I(f.value?.[i.value] ?? a.value.notFound), 513), e.hass ? e.panel?.config?.entry_id ? d.value === "allgemein" ? (G(), oi(os, { key: 2 })) : d.value === "netzdienliches-laden" ? (G(), oi(_c, {
					key: 3,
					hass: e.hass
				}, null, 8, ["hass"])) : d.value === "stromtarif" ? (G(), oi(wf, {
					key: 4,
					hass: e.hass
				}, null, 8, ["hass"])) : d.value === "ersparnis" ? (G(), oi(gp, {
					key: 5,
					hass: e.hass,
					"entry-id": e.panel?.config?.entry_id
				}, null, 8, ["hass", "entry-id"])) : (G(), K("div", Ep, [q("p", null, I(a.value.notFoundDescription), 1), q("a", {
					href: `${s.value}/allgemein`,
					onClick: n[0] ||= (e) => h(e, `${s.value}/allgemein`)
				}, I(a.value.returnToOverview), 9, Dp)])) : (G(), K("p", Tp, I(a.value.missingEntry), 1)) : (G(), K("p", wp, I(a.value.loading), 1))], 2))
			])
		], 10, _p));
	}
}), [["styles", [":host{height:100%;color:var(--primary-text-color,#212121);background:var(--primary-background-color,#fafafa);font-family:var(--paper-font-body1_-_font-family,Roboto, sans-serif);font-size:14px;display:block}*{box-sizing:border-box}.dashboard{min-height:100%;container:sax-panel/inline-size}.header{background:var(--app-header-background-color,var(--primary-color,#03a9f4));min-height:64px;color:var(--app-header-text-color,#fff);align-items:center;gap:14px;padding:8px 24px;display:flex}.brand{align-items:center;gap:10px;font-size:20px;font-weight:500;display:flex}.header svg{fill:none;stroke:currentColor;stroke-width:1.7px;stroke-linecap:round;stroke-linejoin:round}.brand-icon{width:30px;height:30px}.menu-button{width:44px;height:44px;color:inherit;cursor:pointer;background:0 0;border:0;border-radius:50%;place-items:center;margin-left:-10px;display:grid}.menu-button svg{width:24px;height:24px}.navigation{border-bottom:1px solid var(--divider-color,#e0e0e0);background:var(--card-background-color,#fff);padding:0 16px;display:flex;overflow-x:auto}.navigation a{min-height:56px;color:var(--secondary-text-color,#666);white-space:nowrap;border-bottom:3px solid #0000;align-items:center;padding:12px 16px;text-decoration:none;display:flex}.navigation a[aria-current=page]{border-color:var(--primary-color,#03a9f4);color:var(--primary-text-color,#212121);font-weight:600}a{color:var(--primary-text-color,#212121);text-underline-offset:3px}a:focus-visible,button:focus-visible{outline-offset:-4px;outline:2px solid}main{max-width:1120px;margin:0 auto;padding:28px 24px 48px}.introduction{color:var(--secondary-text-color,#666);margin:0 0 24px;line-height:1.6}.section{overflow-wrap:anywhere;border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));box-shadow:var(--ha-card-box-shadow,none);padding:28px;container:sax-content/inline-size}.section.section--tariff{box-shadow:none;background:0 0;border:0;padding:0}h1{margin:0;font-size:24px;font-weight:500;line-height:1.35}h1:focus{outline:none}h2{margin:0 0 12px;font-size:18px;font-weight:500;line-height:1.5}.status{margin-top:24px;line-height:1.7}.narrow .header{padding-left:16px;padding-right:16px}.narrow main{padding:16px 12px 32px}@container sax-panel (width>=940px){.header{min-height:56px;padding:6px 20px}.navigation a{min-height:48px;padding:8px 14px}main{max-width:1360px;padding:16px 20px 20px}.introduction{margin-bottom:12px}.section{padding:20px}h1{font-size:22px}}@media (max-width:600px){.header{gap:8px;padding:8px 16px}.brand{gap:6px;font-size:18px}.brand-icon{display:none}.navigation{padding:0 4px}main{padding:16px 12px 32px}.introduction{margin-bottom:16px}.section{padding:20px}h1{font-size:22px}}"]]]));
customElements.get("sax-power-vue-panel") || customElements.define("sax-power-vue-panel", Op);
//#endregion
export { Op as SaxPowerVuePanel };
