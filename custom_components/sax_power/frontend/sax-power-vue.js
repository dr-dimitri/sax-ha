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
}, l = Object.prototype.hasOwnProperty, u = (e, t) => l.call(e, t), d = Array.isArray, f = (e) => x(e) === "[object Map]", p = (e) => x(e) === "[object Set]", m = (e) => x(e) === "[object Date]", h = (e) => typeof e == "function", g = (e) => typeof e == "string", _ = (e) => typeof e == "symbol", v = (e) => typeof e == "object" && !!e, y = (e) => (v(e) || h(e)) && h(e.then) && h(e.catch), b = Object.prototype.toString, x = (e) => b.call(e), S = (e) => x(e).slice(8, -1), C = (e) => x(e) === "[object Object]", w = (e) => g(e) && e !== "NaN" && e[0] !== "-" && "" + parseInt(e, 10) === e, ee = /* @__PURE__ */ e(",key,ref,ref_for,ref_key,onVnodeBeforeMount,onVnodeMounted,onVnodeBeforeUpdate,onVnodeUpdated,onVnodeBeforeUnmount,onVnodeUnmounted"), T = (e) => {
	let t = /* @__PURE__ */ Object.create(null);
	return ((n) => t[n] || (t[n] = e(n)));
}, E = /-\w/g, D = T((e) => e.replace(E, (e) => e.slice(1).toUpperCase())), O = /\B([A-Z])/g, k = T((e) => e.replace(O, "-$1").toLowerCase()), te = T((e) => e.charAt(0).toUpperCase() + e.slice(1)), ne = T((e) => e ? `on${te(e)}` : ""), A = (e, t) => !Object.is(e, t), re = (e, ...t) => {
	for (let n = 0; n < e.length; n++) e[n](...t);
}, ie = (e, t, n, r = !1) => {
	Object.defineProperty(e, t, {
		configurable: !0,
		enumerable: !1,
		writable: r,
		value: n
	});
}, ae = (e) => {
	let t = parseFloat(e);
	return isNaN(t) ? e : t;
}, oe = (e) => {
	let t = g(e) ? Number(e) : NaN;
	return isNaN(t) ? e : t;
}, se, ce = () => se ||= typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : typeof global < "u" ? global : {};
function le(e) {
	if (d(e)) {
		let t = {};
		for (let n = 0; n < e.length; n++) {
			let r = e[n], i = g(r) ? pe(r) : le(r);
			if (i) for (let e in i) t[e] = i[e];
		}
		return t;
	}
	if (g(e) || v(e)) return e;
}
var ue = /;(?![^(]*\))/g, de = /:([^]+)/, fe = /\/\*[^]*?\*\//g;
function pe(e) {
	let t = {};
	return e.replace(fe, "").split(ue).forEach((e) => {
		if (e) {
			let n = e.split(de);
			n.length > 1 && (t[n[0].trim()] = n[1].trim());
		}
	}), t;
}
function j(e) {
	let t = "";
	if (g(e)) t = e;
	else if (d(e)) for (let n = 0; n < e.length; n++) {
		let r = j(e[n]);
		r && (t += r + " ");
	}
	else if (v(e)) for (let n in e) e[n] && (t += n + " ");
	return t.trim();
}
var me = "itemscope,allowfullscreen,formnovalidate,ismap,nomodule,novalidate,readonly", he = /* @__PURE__ */ e(me);
me + "";
function ge(e) {
	return !!e || e === "";
}
function _e(e, t) {
	if (e.length !== t.length) return !1;
	let n = !0;
	for (let r = 0; n && r < e.length; r++) n = ye(e[r], t[r]);
	return n;
}
function ve(e, t) {
	if (e.size !== t.size) return !1;
	let n = Array.from(t), r = new Uint8Array(n.length);
	for (let t of e) {
		let e = -1;
		for (let i = 0; i < n.length; i++) if (!r[i] && ye(t, n[i])) {
			e = i;
			break;
		}
		if (e < 0) return !1;
		r[e] = 1;
	}
	return !0;
}
function ye(e, t) {
	if (e === t) return !0;
	let n = m(e), r = m(t);
	if (n || r) return n && r ? e.getTime() === t.getTime() : !1;
	if (n = _(e), r = _(t), n || r) return e === t;
	if (n = d(e), r = d(t), n || r) return n && r ? _e(e, t) : !1;
	if (n = v(e), r = v(t), n || r) {
		if (!n || !r) return !1;
		if (n = f(e), r = f(t), n || r || (n = p(e), r = p(t), n || r)) return n && r ? ve(e, t) : !1;
		if (Object.keys(e).length !== Object.keys(t).length) return !1;
		for (let n in e) {
			let r = e.hasOwnProperty(n), i = t.hasOwnProperty(n);
			if (r && !i || !r && i || !ye(e[n], t[n])) return !1;
		}
	}
	return String(e) === String(t);
}
var be = (e) => !!(e && e.__v_isRef === !0), M = (e) => g(e) ? e : e == null ? "" : d(e) || v(e) && (e.toString === b || !h(e.toString)) ? be(e) ? M(e.value) : JSON.stringify(e, xe, 2) : String(e), xe = (e, t) => be(t) ? xe(e, t.value) : f(t) ? { [`Map(${t.size})`]: [...t.entries()].reduce((e, [t, n], r) => (e[Se(t, r) + " =>"] = n, e), {}) } : p(t) ? { [`Set(${t.size})`]: [...t.values()].map((e) => Se(e)) } : _(t) ? Se(t) : v(t) && !d(t) && !C(t) ? String(t) : t, Se = (e, t = "") => _(e) ? `Symbol(${e.description ?? t})` : e, N, Ce = class {
	constructor(e = !1) {
		this.detached = e, this._active = !0, this._on = 0, this.effects = [], this.cleanups = [], this._isPaused = !1, this._warnOnRun = !0, this.__v_skip = !0, !e && N && (N.active ? (this.parent = N, this.index = (N.scopes || (N.scopes = [])).push(this) - 1) : (this._active = !1, this._warnOnRun = !1));
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
			let t = N;
			try {
				return N = this, e();
			} finally {
				N = t;
			}
		}
	}
	on() {
		++this._on === 1 && (this.prevScope = N, N = this);
	}
	off() {
		if (this._on > 0 && --this._on === 0) {
			if (N === this) N = this.prevScope;
			else {
				let e = N;
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
function we() {
	return N;
}
function Te(e, t = !1) {
	N && N.cleanups.push(e);
}
var P, Ee = /* @__PURE__ */ new WeakSet(), De = class {
	constructor(e) {
		this.fn = e, this.deps = void 0, this.depsTail = void 0, this.flags = 5, this.next = void 0, this.cleanup = void 0, this.scheduler = void 0, N && (N.active ? N.effects.push(this) : this.flags &= -2);
	}
	pause() {
		this.flags |= 64;
	}
	resume() {
		this.flags & 64 && (this.flags &= -65, Ee.has(this) && (Ee.delete(this), this.trigger()));
	}
	notify() {
		this.flags & 2 && !(this.flags & 32) || this.flags & 8 || je(this);
	}
	run() {
		if (!(this.flags & 1)) return this.fn();
		this.flags |= 2, We(this), Pe(this);
		let e = P, t = Be;
		P = this, Be = !0;
		try {
			return this.fn();
		} finally {
			Fe(this), P = e, Be = t, this.flags &= -3;
		}
	}
	stop() {
		if (this.flags & 1) {
			for (let e = this.deps; e; e = e.nextDep) Re(e);
			this.deps = this.depsTail = void 0, We(this), this.onStop && this.onStop(), this.flags &= -2;
		}
	}
	trigger() {
		this.flags & 64 ? Ee.add(this) : this.scheduler ? this.scheduler() : this.runIfDirty();
	}
	runIfDirty() {
		Ie(this) && this.run();
	}
	get dirty() {
		return Ie(this);
	}
}, Oe = 0, ke, Ae;
function je(e, t = !1) {
	if (e.flags |= 8, t) {
		e.next = Ae, Ae = e;
		return;
	}
	e.next = ke, ke = e;
}
function Me() {
	Oe++;
}
function Ne() {
	if (--Oe > 0) return;
	if (Ae) {
		let e = Ae;
		for (Ae = void 0; e;) {
			let t = e.next;
			e.next = void 0, e.flags &= -9, e = t;
		}
	}
	let e;
	for (; ke;) {
		let t = ke;
		for (ke = void 0; t;) {
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
function Pe(e) {
	for (let t = e.deps; t; t = t.nextDep) t.version = -1, t.prevActiveLink = t.dep.activeLink, t.dep.activeLink = t;
}
function Fe(e) {
	let t, n = e.depsTail, r = n;
	for (; r;) {
		let e = r.prevDep;
		r.version === -1 ? (r === n && (n = e), Re(r), ze(r)) : t = r, r.dep.activeLink = r.prevActiveLink, r.prevActiveLink = void 0, r = e;
	}
	e.deps = t, e.depsTail = n;
}
function Ie(e) {
	for (let t = e.deps; t; t = t.nextDep) if (t.dep.version !== t.version || t.dep.computed && (Le(t.dep.computed) || t.dep.version !== t.version)) return !0;
	return !!e._dirty;
}
function Le(e) {
	if (e.flags & 4 && !(e.flags & 16) || (e.flags &= -17, e.globalVersion === Ge) || (e.globalVersion = Ge, !e.isSSR && e.flags & 128 && (!e.deps && !e._dirty || !Ie(e)))) return;
	e.flags |= 2;
	let t = e.dep, n = P, r = Be;
	P = e, Be = !0;
	try {
		Pe(e);
		let n = e.fn(e._value);
		(t.version === 0 || A(n, e._value)) && (e.flags |= 128, e._value = n, t.version++);
	} catch (e) {
		throw t.version++, e;
	} finally {
		P = n, Be = r, Fe(e), e.flags &= -3;
	}
}
function Re(e, t = !1) {
	let { dep: n, prevSub: r, nextSub: i } = e;
	if (r && (r.nextSub = i, e.prevSub = void 0), i && (i.prevSub = r, e.nextSub = void 0), n.subs === e && (n.subs = r, !r && n.computed)) {
		n.computed.flags &= -5;
		for (let e = n.computed.deps; e; e = e.nextDep) Re(e, !0);
	}
	!t && !--n.sc && n.map && n.map.delete(n.key);
}
function ze(e) {
	let { prevDep: t, nextDep: n } = e;
	t && (t.nextDep = n, e.prevDep = void 0), n && (n.prevDep = t, e.nextDep = void 0);
}
var Be = !0, Ve = [];
function He() {
	Ve.push(Be), Be = !1;
}
function Ue() {
	let e = Ve.pop();
	Be = e === void 0 || e;
}
function We(e) {
	let { cleanup: t } = e;
	if (e.cleanup = void 0, t) {
		let e = P;
		P = void 0;
		try {
			t();
		} finally {
			P = e;
		}
	}
}
var Ge = 0, Ke = class {
	constructor(e, t) {
		this.sub = e, this.dep = t, this.version = t.version, this.nextDep = this.prevDep = this.nextSub = this.prevSub = this.prevActiveLink = void 0;
	}
}, qe = class {
	constructor(e) {
		this.computed = e, this.version = 0, this.activeLink = void 0, this.subs = void 0, this.map = void 0, this.key = void 0, this.sc = 0, this.__v_skip = !0;
	}
	track(e) {
		if (!P || !Be || P === this.computed) return;
		let t = this.activeLink;
		if (t === void 0 || t.sub !== P) t = this.activeLink = new Ke(P, this), P.deps ? (t.prevDep = P.depsTail, P.depsTail.nextDep = t, P.depsTail = t) : P.deps = P.depsTail = t, Je(t);
		else if (t.version === -1 && (t.version = this.version, t.nextDep)) {
			let e = t.nextDep;
			e.prevDep = t.prevDep, t.prevDep && (t.prevDep.nextDep = e), t.prevDep = P.depsTail, t.nextDep = void 0, P.depsTail.nextDep = t, P.depsTail = t, P.deps === t && (P.deps = e);
		}
		return t;
	}
	trigger(e) {
		this.version++, Ge++, this.notify(e);
	}
	notify(e) {
		Me();
		try {
			for (let e = this.subs; e; e = e.prevSub) e.sub.notify() && e.sub.dep.notify();
		} finally {
			Ne();
		}
	}
};
function Je(e) {
	if (e.dep.sc++, e.sub.flags & 4) {
		let t = e.dep.computed;
		if (t && !e.dep.subs) {
			t.flags |= 20;
			for (let e = t.deps; e; e = e.nextDep) Je(e);
		}
		let n = e.dep.subs;
		n !== e && (e.prevSub = n, n && (n.nextSub = e)), e.dep.subs = e;
	}
}
var Ye = /* @__PURE__ */ new WeakMap(), Xe = /* @__PURE__ */ Symbol(""), Ze = /* @__PURE__ */ Symbol(""), Qe = /* @__PURE__ */ Symbol("");
function F(e, t, n) {
	if (Be && P) {
		let t = Ye.get(e);
		t || Ye.set(e, t = /* @__PURE__ */ new Map());
		let r = t.get(n);
		r || (t.set(n, r = new qe()), r.map = t, r.key = n), r.track();
	}
}
function $e(e, t, n, r, i, a) {
	let o = Ye.get(e);
	if (!o) {
		Ge++;
		return;
	}
	let s = (e) => {
		e && e.trigger();
	};
	if (Me(), t === "clear") o.forEach(s);
	else {
		let i = d(e), a = i && w(n);
		if (i && n === "length") {
			let e = Number(r);
			o.forEach((t, n) => {
				(n === "length" || n === Qe || !_(n) && n >= e) && s(t);
			});
		} else switch ((n !== void 0 || o.has(void 0)) && s(o.get(n)), a && s(o.get(Qe)), t) {
			case "add":
				i ? a && s(o.get("length")) : (s(o.get(Xe)), f(e) && s(o.get(Ze)));
				break;
			case "delete":
				i || (s(o.get(Xe)), f(e) && s(o.get(Ze)));
				break;
			case "set": f(e) && s(o.get(Xe));
		}
	}
	Ne();
}
function et(e) {
	let t = /* @__PURE__ */ I(e);
	return t === e ? t : (F(t, "iterate", Qe), /* @__PURE__ */ zt(e) ? t : t.map(Ht));
}
function tt(e) {
	return F(e = /* @__PURE__ */ I(e), "iterate", Qe), e;
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
	let r = /* @__PURE__ */ I(e);
	F(r, "iterate", Qe);
	let i = r[t](...n);
	return (i === -1 || i === !1) && /* @__PURE__ */ Bt(n[0]) ? (n[0] = /* @__PURE__ */ I(n[0]), r[t](...n)) : i;
}
function lt(e, t, n = []) {
	He(), Me();
	let r = (/* @__PURE__ */ I(e))[t].apply(e, n);
	return Ne(), Ue(), r;
}
var ut = /* @__PURE__ */ e("__proto__,__v_isRef,__isVue"), dt = new Set(/* @__PURE__ */ Object.getOwnPropertyNames(Symbol).filter((e) => e !== "arguments" && e !== "caller").map((e) => Symbol[e]).filter(_));
function ft(e) {
	_(e) || (e = String(e));
	let t = /* @__PURE__ */ I(this);
	return F(t, "has", e), t.hasOwnProperty(e);
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
		let o = Reflect.get(e, t, /* @__PURE__ */ L(e) ? e : n);
		if ((_(t) ? dt.has(t) : ut(t)) || (r || F(e, "get", t), i)) return o;
		if (/* @__PURE__ */ L(o)) {
			let e = a && w(t) ? o : o.value;
			return r && v(e) ? /* @__PURE__ */ Ft(e) : e;
		}
		return v(o) ? r ? /* @__PURE__ */ Ft(o) : /* @__PURE__ */ Nt(o) : o;
	}
}, mt = class extends pt {
	constructor(e = !1) {
		super(!1, e);
	}
	set(e, t, n, r) {
		let i = e[t], a = d(e) && w(t);
		if (!this._isShallow) {
			let e = /* @__PURE__ */ Rt(i);
			if (!/* @__PURE__ */ zt(n) && !/* @__PURE__ */ Rt(n) && (i = /* @__PURE__ */ I(i), n = /* @__PURE__ */ I(n)), !a && /* @__PURE__ */ L(i) && !/* @__PURE__ */ L(n)) return e || (i.value = n), !0;
		}
		let o = a ? Number(t) < e.length : u(e, t), s = Reflect.set(e, t, n, /* @__PURE__ */ L(e) ? e : r);
		return e === /* @__PURE__ */ I(r) && s && (o ? A(n, i) && $e(e, "set", t, n, i) : $e(e, "add", t, n)), s;
	}
	deleteProperty(e, t) {
		let n = u(e, t), r = e[t], i = Reflect.deleteProperty(e, t);
		return i && n && $e(e, "delete", t, void 0, r), i;
	}
	has(e, t) {
		let n = Reflect.has(e, t);
		return (!_(t) || !dt.has(t)) && F(e, "has", t), n;
	}
	ownKeys(e) {
		return F(e, "iterate", d(e) ? "length" : Xe), Reflect.ownKeys(e);
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
		let i = this.__v_raw, a = /* @__PURE__ */ I(i), o = f(a), c = e === "entries" || e === Symbol.iterator && o, l = e === "keys" && o, u = i[e](...r), d = n ? yt : t ? Ut : Ht;
		return !t && F(a, "iterate", l ? Ze : Xe), s(Object.create(u), { next() {
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
			let r = this.__v_raw, i = /* @__PURE__ */ I(r), a = /* @__PURE__ */ I(n);
			e || (A(n, a) && F(i, "get", n), F(i, "get", a));
			let { has: o } = bt(i), s = t ? yt : e ? Ut : Ht;
			if (o.call(i, n)) return s(r.get(n));
			if (o.call(i, a)) return s(r.get(a));
			r !== i && r.get(n);
		},
		get size() {
			let t = this.__v_raw;
			return !e && F(/* @__PURE__ */ I(t), "iterate", Xe), t.size;
		},
		has(t) {
			let n = this.__v_raw, r = /* @__PURE__ */ I(n), i = /* @__PURE__ */ I(t);
			return e || (A(t, i) && F(r, "has", t), F(r, "has", i)), t === i ? n.has(t) : n.has(t) || n.has(i);
		},
		forEach(n, r) {
			let i = this, a = i.__v_raw, o = /* @__PURE__ */ I(a), s = t ? yt : e ? Ut : Ht;
			return !e && F(o, "iterate", Xe), a.forEach((e, t) => n.call(r, s(e), s(t), i));
		}
	};
	return s(n, e ? {
		add: St("add"),
		set: St("set"),
		delete: St("delete"),
		clear: St("clear")
	} : {
		add(e) {
			let n = /* @__PURE__ */ I(this), r = bt(n), i = /* @__PURE__ */ I(e), a = !t && !/* @__PURE__ */ zt(e) && !/* @__PURE__ */ Rt(e) ? i : e;
			return r.has.call(n, a) || A(e, a) && r.has.call(n, e) || A(i, a) && r.has.call(n, i) || (n.add(a), $e(n, "add", a, a)), this;
		},
		set(e, n) {
			!t && !/* @__PURE__ */ zt(n) && !/* @__PURE__ */ Rt(n) && (n = /* @__PURE__ */ I(n));
			let r = /* @__PURE__ */ I(this), { has: i, get: a } = bt(r), o = i.call(r, e);
			o ||= (e = /* @__PURE__ */ I(e), i.call(r, e));
			let s = a.call(r, e);
			return r.set(e, n), o ? A(n, s) && $e(r, "set", e, n, s) : $e(r, "add", e, n), this;
		},
		delete(e) {
			let t = /* @__PURE__ */ I(this), { has: n, get: r } = bt(t), i = n.call(t, e);
			i ||= (e = /* @__PURE__ */ I(e), n.call(t, e));
			let a = r ? r.call(t, e) : void 0, o = t.delete(e);
			return i && $e(t, "delete", e, void 0, a), o;
		},
		clear() {
			let e = /* @__PURE__ */ I(this), t = e.size !== 0, n = e.clear();
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
	if (!v(e) || e.__v_raw && !(t && e.__v_isReactive) || e.__v_skip || !Object.isExtensible(e)) return e;
	let a = i.get(e);
	if (a) return a;
	let o = Mt(S(e));
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
function I(e) {
	let t = e && e.__v_raw;
	return t ? /* @__PURE__ */ I(t) : e;
}
function Vt(e) {
	return !u(e, "__v_skip") && Object.isExtensible(e) && ie(e, "__v_skip", !0), e;
}
var Ht = (e) => v(e) ? /* @__PURE__ */ Nt(e) : e, Ut = (e) => v(e) ? /* @__PURE__ */ Ft(e) : e;
// @__NO_SIDE_EFFECTS__
function L(e) {
	return e ? e.__v_isRef === !0 : !1;
}
// @__NO_SIDE_EFFECTS__
function R(e) {
	return Gt(e, !1);
}
// @__NO_SIDE_EFFECTS__
function Wt(e) {
	return Gt(e, !0);
}
function Gt(e, t) {
	return /* @__PURE__ */ L(e) ? e : new Kt(e, t);
}
var Kt = class {
	constructor(e, t) {
		this.dep = new qe(), this.__v_isRef = !0, this.__v_isShallow = !1, this._rawValue = t ? e : /* @__PURE__ */ I(e), this._value = t ? e : Ht(e), this.__v_isShallow = t;
	}
	get value() {
		return this.dep.track(), this._value;
	}
	set value(e) {
		let t = this._rawValue, n = this.__v_isShallow || /* @__PURE__ */ zt(e) || /* @__PURE__ */ Rt(e);
		e = n ? e : /* @__PURE__ */ I(e), A(e, t) && (this._rawValue = e, this._value = n ? e : Ht(e), this.dep.trigger());
	}
};
function z(e) {
	return /* @__PURE__ */ L(e) ? e.value : e;
}
var qt = {
	get: (e, t, n) => t === "__v_raw" ? e : z(Reflect.get(e, t, n)),
	set: (e, t, n, r) => {
		let i = e[t];
		return /* @__PURE__ */ L(i) && !/* @__PURE__ */ L(n) ? (i.value = n, !0) : Reflect.set(e, t, n, r);
	}
};
function Jt(e) {
	return /* @__PURE__ */ Lt(e) ? e : new Proxy(e, qt);
}
var Yt = class {
	constructor(e, t, n) {
		this.fn = e, this.setter = t, this._value = void 0, this.dep = new qe(this), this.__v_isRef = !0, this.deps = void 0, this.depsTail = void 0, this.flags = 16, this.globalVersion = Ge - 1, this.next = void 0, this.effect = this, this.__v_isReadonly = !t, this.isSSR = n;
	}
	notify() {
		if (this.flags |= 16, !(this.flags & 8) && P !== this) return je(this, !0), !0;
	}
	get value() {
		let e = this.dep.track();
		return Le(this), e && (e.version = this.dep.version), this._value;
	}
	set value(e) {
		this.setter && this.setter(e);
	}
};
// @__NO_SIDE_EFFECTS__
function Xt(e, t, n = !1) {
	let r, i;
	return h(e) ? r = e : (r = e.get, i = e.set), new Yt(r, i, n);
}
var Zt = {}, Qt = /* @__PURE__ */ new WeakMap(), $t = void 0;
function en(e, t = !1, n = $t) {
	if (n) {
		let t = Qt.get(n);
		t || Qt.set(n, t = []), t.push(e);
	}
}
function tn(e, n, i = t) {
	let { immediate: a, deep: o, once: s, scheduler: l, augmentJob: u, call: f } = i, p = (e) => o ? e : /* @__PURE__ */ zt(e) || o === !1 || o === 0 ? nn(e, 1) : nn(e), m, g, _, v, y = !1, b = !1;
	if (/* @__PURE__ */ L(e) ? (g = () => e.value, y = /* @__PURE__ */ zt(e)) : /* @__PURE__ */ Lt(e) ? (g = () => p(e), y = !0) : d(e) ? (b = !0, y = e.some((e) => /* @__PURE__ */ Lt(e) || /* @__PURE__ */ zt(e)), g = () => e.map((e) => {
		if (/* @__PURE__ */ L(e)) return e.value;
		if (/* @__PURE__ */ Lt(e)) return p(e);
		if (h(e)) return f ? f(e, 2) : e();
	})) : g = h(e) ? n ? f ? () => f(e, 2) : e : () => {
		if (_) {
			He();
			try {
				_();
			} finally {
				Ue();
			}
		}
		let t = $t;
		$t = m;
		try {
			return f ? f(e, 3, [v]) : e(v);
		} finally {
			$t = t;
		}
	} : r, n && o) {
		let e = g, t = o === !0 ? Infinity : o;
		g = () => nn(e(), t);
	}
	let x = we(), S = () => {
		m.stop(), x && x.active && c(x.effects, m);
	};
	if (s && n) {
		let e = n;
		n = (...t) => {
			let n = e(...t);
			return S(), n;
		};
	}
	let C = b ? Array(e.length).fill(Zt) : Zt, w = (e) => {
		if (m.flags & 1 && (m.dirty || e)) {
			if (n) {
				let t = m.run();
				if (e || o || y || (b ? t.some((e, t) => A(e, C[t])) : A(t, C))) {
					_ && _();
					let e = $t;
					$t = m;
					try {
						let e = [
							t,
							C === Zt ? void 0 : b && C[0] === Zt ? [] : C,
							v
						];
						C = t, f ? f(n, 3, e) : n(...e);
					} finally {
						$t = e;
					}
				}
			} else m.run();
		}
	};
	return u && u(w), m = new De(g), m.scheduler = l ? () => l(w, !1) : w, v = (e) => en(e, !1, m), _ = m.onStop = () => {
		let e = Qt.get(m);
		if (e) {
			if (f) f(e, 4);
			else for (let t of e) t();
			Qt.delete(m);
		}
	}, n ? a ? w(!0) : C = m.run() : l ? l(w.bind(null, !0), !0) : m.run(), S.pause = m.pause.bind(m), S.resume = m.resume.bind(m), S.stop = S, S;
}
function nn(e, t = Infinity, n) {
	if (t <= 0 || !v(e) || e.__v_skip || (n ||= /* @__PURE__ */ new Map(), (n.get(e) || 0) >= t)) return e;
	if (n.set(e, t), t--, /* @__PURE__ */ L(e)) nn(e.value, t, n);
	else if (d(e)) for (let r = 0; r < e.length; r++) nn(e[r], t, n);
	else if (p(e) || f(e)) e.forEach((e) => {
		nn(e, t, n);
	});
	else if (C(e)) {
		for (let r in e) nn(e[r], t, n);
		for (let r of Object.getOwnPropertySymbols(e)) Object.prototype.propertyIsEnumerable.call(e, r) && nn(e[r], t, n);
	}
	return e;
}
//#endregion
//#region node_modules/@vue/runtime-core/dist/runtime-core.esm-bundler.js
function rn(e, t, n, r) {
	try {
		return r ? e(...r) : e();
	} catch (e) {
		on(e, t, n);
	}
}
function an(e, t, n, r) {
	if (h(e)) {
		let i = rn(e, t, n, r);
		return i && y(i) && i.catch((e) => {
			on(e, t, n);
		}), i;
	}
	if (d(e)) {
		let i = [];
		for (let a = 0; a < e.length; a++) i.push(an(e[a], t, n, r));
		return i;
	}
}
function on(e, n, r, i = !0) {
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
			He(), rn(o, null, 10, [
				e,
				i,
				a
			]), Ue();
			return;
		}
	}
	sn(e, r, a, i, s);
}
function sn(e, t, n, r = !0, i = !1) {
	if (i) throw e;
	console.error(e);
}
var B = [], cn = -1, ln = [], un = null, dn = 0, fn = /* @__PURE__ */ Promise.resolve(), pn = null;
function mn(e) {
	let t = pn || fn;
	return e ? t.then(this ? e.bind(this) : e) : t;
}
function hn(e) {
	let t = cn + 1, n = B.length;
	for (; t < n;) {
		let r = t + n >>> 1, i = B[r], a = xn(i);
		a < e || a === e && i.flags & 2 ? t = r + 1 : n = r;
	}
	return t;
}
function gn(e) {
	if (!(e.flags & 1)) {
		let t = xn(e), n = B[B.length - 1];
		!n || !(e.flags & 2) && t >= xn(n) ? B.push(e) : B.splice(hn(t), 0, e), e.flags |= 1, _n();
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
	for (; n < B.length; n++) {
		let t = B[n];
		if (t && t.flags & 2) {
			if (e && t.id !== e.uid) continue;
			B.splice(n, 1), n--, t.flags & 4 && (t.flags &= -2), t(), t.flags & 4 || (t.flags &= -2);
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
		for (cn = 0; cn < B.length; cn++) {
			let e = B[cn];
			e && !(e.flags & 8) && (e.flags & 4 && (e.flags &= -2), rn(e, e.i, e.i ? 15 : 14), e.flags & 4 || (e.flags &= -2));
		}
	} finally {
		for (; cn < B.length; cn++) {
			let e = B[cn];
			e && (e.flags &= -2);
		}
		cn = -1, B.length = 0, bn(e), pn = null, (B.length || ln.length) && Sn(e);
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
		r._d && ei(-1);
		let i = Tn(t), a = Zr.length, o;
		try {
			o = e(...n);
		} finally {
			for (let e = Zr.length; e > a; e--) Qr();
			Tn(i), r._d && ei(1);
		}
		return o;
	};
	return r._n = !0, r._c = !0, r._d = !0, r;
}
function Dn(e, n) {
	if (Cn === null) return e;
	let r = ji(Cn), i = e.dirs ||= [];
	for (let e = 0; e < n.length; e++) {
		let [a, o, s, c = t] = n[e];
		a && (h(a) && (a = {
			mounted: a,
			updated: a
		}), a.deep && nn(o), i.push({
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
		c && (He(), an(c, n, 8, [
			e.el,
			s,
			e,
			t
		]), Ue());
	}
}
function kn(e, t) {
	if (_i) {
		let n = _i.provides, r = _i.parent && _i.parent.provides;
		r === n && (n = _i.provides = Object.create(r)), n[e] = t;
	}
}
function An(e, t, n = !1) {
	let r = vi();
	if (r || sr) {
		let i = sr ? sr._context.provides : r ? r.parent == null || r.ce ? r.vnode.appContext && r.vnode.appContext.provides : r.parent.provides : void 0;
		if (i && e in i) return i[e];
		if (arguments.length > 1) return n && h(t) ? t.call(r && r.proxy) : t;
	}
}
var jn = /* @__PURE__ */ Symbol.for("v-scx"), Mn = () => An(jn);
function Nn(e, t, n) {
	return Pn(e, t, n);
}
function Pn(e, n, i = t) {
	let { immediate: a, deep: o, flush: c, once: l } = i, u = s({}, i), d = n && a || !n && c !== "post", f;
	if (wi) {
		if (c === "sync") {
			let e = Mn();
			f = e.__watcherHandles ||= [];
		} else if (!d) {
			let e = () => {};
			return e.stop = r, e.resume = r, e.pause = r, e;
		}
	}
	let p = _i;
	u.call = (e, t, n) => an(e, p, t, n);
	let m = !1;
	c === "post" ? u.scheduler = (e) => {
		U(e, p && p.suspense);
	} : c !== "sync" && (m = !0, u.scheduler = (e, t) => {
		t ? e() : gn(e);
	}), u.augmentJob = (e) => {
		n && (e.flags |= 4), m && (e.flags |= 2, p && (e.id = p.uid, e.i = p));
	};
	let h = tn(e, n, u);
	return wi && (f ? f.push(h) : d && h()), h;
}
var Fn = /* @__PURE__ */ Symbol("_vte"), In = (e) => e.__isTeleport, Ln = /* @__PURE__ */ Symbol("_leaveCb");
function Rn(e) {
	let t = e[0];
	if (e.length > 1) {
		for (let n of e) if (n.type !== Yr) {
			t = n;
			break;
		}
	}
	return t;
}
function zn(e) {
	if (!Jn(e)) return In(e.type) && e.children ? Rn(e.children) : e;
	if (e.component) return e.component.subTree;
	let { shapeFlag: t, children: n } = e;
	if (n) {
		if (t & 16) return n[0];
		if (t & 32 && h(n.default)) return n.default();
	}
}
function Bn(e, t) {
	if (e.shapeFlag & 6 && e.component) {
		e.transition = t;
		let n = e.component.subTree;
		Bn(In(n.type) && zn(n) || n, t);
	} else e.shapeFlag & 128 ? (e.ssContent.transition = t.clone(e.ssContent), e.ssFallback.transition = t.clone(e.ssFallback)) : e.transition = t;
}
// @__NO_SIDE_EFFECTS__
function V(e, t) {
	return h(e) ? /* @__PURE__ */ s({ name: e.name }, t, { setup: e }) : e;
}
function Vn() {
	let e = vi();
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
	let s = a.shapeFlag & 4 ? ji(a.component) : a.el, l = o ? null : s, { i: f, r: p } = e, m = n && n.r, _ = f.refs === t ? f.refs = {} : f.refs, v = f.setupState, y = /* @__PURE__ */ I(v), b = v === t ? i : (e) => !Un(_, e) && u(y, e), x = (e, t) => !(t && Un(_, t));
	if (m != null && m !== p) {
		if (Kn(n), g(m)) _[m] = null, b(m) && (v[m] = null);
		else if (/* @__PURE__ */ L(m)) {
			let e = n;
			x(m, e.k) && (m.value = null), e.k && (_[e.k] = null);
		}
	}
	if (h(p)) rn(p, f, 12, [l, _]);
	else {
		let t = g(p), n = /* @__PURE__ */ L(p);
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
				t.id = -1, Wn.set(e, t), U(t, r);
			} else Kn(e), i();
		}
	}
}
function Kn(e) {
	let t = Wn.get(e);
	t && (t.flags |= 8, Wn.delete(e));
}
ce().requestIdleCallback, ce().cancelIdleCallback;
var qn = (e) => !!e.type.__asyncLoader, Jn = (e) => e.type.__isKeepAlive;
function Yn(e, t, n = _i, r = !1) {
	if (n) {
		let i = n[e] || (n[e] = []), a = t.__weh ||= (...r) => {
			He();
			let i = xi(n), a = an(t, n, e, r);
			return i(), Ue(), a;
		};
		return r ? i.unshift(a) : i.push(a), a;
	}
}
var Xn = (e) => (t, n = _i) => {
	(!wi || e === "sp") && Yn(e, (...e) => t(...e), n);
}, Zn = Xn("m"), Qn = Xn("bum"), $n = /* @__PURE__ */ Symbol.for("v-ndc");
function H(e, t, n, r) {
	let i, a = n && n[r], o = d(e);
	if (o || g(e)) {
		let n = o && /* @__PURE__ */ Lt(e), r = !1, s = !1;
		n && (r = !/* @__PURE__ */ zt(e), s = /* @__PURE__ */ Rt(e), e = tt(e)), i = Array(e.length);
		for (let n = 0, o = e.length; n < o; n++) i[n] = t(r ? s ? Ut(Ht(e[n])) : Ht(e[n]) : e[n], n, void 0, a && a[n]);
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
var er = (e) => e ? Ci(e) ? ji(e) : er(e.parent) : null, tr = /* @__PURE__ */ s(/* @__PURE__ */ Object.create(null), {
	$: (e) => e,
	$el: (e) => e.vnode.el,
	$data: (e) => e.data,
	$props: (e) => e.props,
	$attrs: (e) => e.attrs,
	$slots: (e) => e.slots,
	$refs: (e) => e.refs,
	$parent: (e) => er(e.parent),
	$root: (e) => er(e.root),
	$host: (e) => e.ce,
	$emit: (e) => e.emit,
	$options: (e) => e.type,
	$forceUpdate: (e) => e.f ||= () => {
		gn(e.update);
	},
	$nextTick: (e) => e.n ||= mn.bind(e.proxy),
	$watch: (e) => r
}), nr = (e, n) => e !== t && !e.__isScriptSetup && u(e, n), rr = {
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
			else if (nr(i, n)) return s[n] = 1, i[n];
			else if (u(o, n)) return s[n] = 3, o[n];
			else if (r !== t && u(r, n)) return s[n] = 4, r[n];
			else s[n] = 0;
		}
		let d = tr[n], f, p;
		if (d) return n === "$attrs" && F(e.attrs, "get", ""), d(e);
		if ((f = c.__cssModules) && (f = f[n])) return f;
		if (r !== t && u(r, n)) return s[n] = 4, r[n];
		if (p = l.config.globalProperties, u(p, n)) return p[n];
	},
	set({ _: e }, t, n) {
		let { data: r, setupState: i, ctx: a } = e;
		return nr(i, t) ? (i[t] = n, !0) : u(e.props, t) || t[0] === "$" && t.slice(1) in e ? !1 : (a[t] = n, !0);
	},
	has({ _: { data: e, setupState: t, accessCache: n, ctx: r, appContext: i, props: a, type: o } }, s) {
		let c;
		return !!(n[s] || nr(t, s) || u(a, s) || u(r, s) || u(tr, s) || u(i.config.globalProperties, s) || (c = o.__cssModules) && c[s]);
	},
	defineProperty(e, t, n) {
		return n.get == null ? u(n, "value") && this.set(e, t, n.value, null) : e._.accessCache[t] = 0, Reflect.defineProperty(e, t, n);
	}
};
function ir() {
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
var ar = 0;
function or(e, t) {
	return function(n, r = null) {
		h(n) || (n = s({}, n)), r != null && !v(r) && (r = null);
		let i = ir(), a = /* @__PURE__ */ new WeakSet(), o = [], c = !1, l = i.app = {
			_uid: ar++,
			_component: n,
			_props: r,
			_container: null,
			_context: i,
			_instance: null,
			version: Ni,
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
					let u = l._ceVNode || X(n, r);
					return u.appContext = i, s === !0 ? s = "svg" : s === !1 && (s = void 0), o && t ? t(u, a) : e(u, a, s), c = !0, l._container = a, a.__vue_app__ = l, ji(u.component);
				}
			},
			onUnmount(e) {
				o.push(e);
			},
			unmount() {
				c && (an(o, l._instance, 16), e(null, l._container), delete l._container.__vue_app__);
			},
			provide(e, t) {
				return i.provides[e] = t, l;
			},
			runWithContext(e) {
				let t = sr;
				sr = l;
				try {
					return e();
				} finally {
					sr = t;
				}
			}
		};
		return l;
	};
}
var sr = null, cr = (e, t) => t === "modelValue" || t === "model-value" ? e.modelModifiers : e[`${t}Modifiers`] || e[`${D(t)}Modifiers`] || e[`${k(t)}Modifiers`];
function lr(e, n, ...r) {
	if (e.isUnmounted) return;
	let i = e.vnode.props || t, a = r, o = n.startsWith("update:"), s = o && cr(i, n.slice(7));
	s && (s.trim && (a = r.map((e) => g(e) ? e.trim() : e)), s.number && (a = a.map(ae)));
	let c, l = i[c = ne(n)] || i[c = ne(D(n))];
	!l && o && (l = i[c = ne(k(n))]), l && an(l, e, 6, a);
	let u = i[c + "Once"];
	if (u) {
		if (!e.emitted) e.emitted = {};
		else if (e.emitted[c]) return;
		e.emitted[c] = !0, an(u, e, 6, a);
	}
}
function ur(e, t, n = !1) {
	let r = t.emitsCache, i = r.get(e);
	if (i !== void 0) return i;
	let a = e.emits, o = {};
	return a ? (d(a) ? a.forEach((e) => o[e] = null) : s(o, a), v(e) && r.set(e, o), o) : (v(e) && r.set(e, null), null);
}
function dr(e, t) {
	return !e || !a(t) ? !1 : (t = t.slice(2), t = t === "Once" ? t : t.replace(/Once$/, ""), u(e, t[0].toLowerCase() + t.slice(1)) || u(e, k(t)) || u(e, t));
}
function fr(e) {
	let { type: t, vnode: n, proxy: r, withProxy: i, propsOptions: [a], slots: s, attrs: c, emit: l, render: u, renderCache: d, props: f, data: p, setupState: m, ctx: h, inheritAttrs: g } = e, _ = Tn(e), v, y;
	try {
		if (n.shapeFlag & 4) {
			let e = i || r, t = e;
			v = li(u.call(t, e, d, f, m, p, h)), y = c;
		} else {
			let e = t;
			v = li(e.length > 1 ? e(f, {
				attrs: c,
				slots: s,
				emit: l
			}) : e(f, null)), y = t.props ? c : pr(c);
		}
	} catch (t) {
		Zr.length = 0, on(t, e, 1), v = X(Yr);
	}
	let b = v;
	if (y && g !== !1) {
		let e = Object.keys(y), { shapeFlag: t } = b;
		e.length && t & 7 && (a && e.some(o) && (y = mr(y, a)), b = ci(b, y, !1, !0));
	}
	return n.dirs && (b = ci(b, null, !1, !0), b.dirs = b.dirs ? b.dirs.concat(n.dirs) : n.dirs), n.transition && Bn(In(b.type) && zn(b) || b, n.transition), v = b, Tn(_), v;
}
var pr = (e) => {
	let t;
	for (let n in e) (n === "class" || n === "style" || a(n)) && ((t ||= {})[n] = e[n]);
	return t;
}, mr = (e, t) => {
	let n = {};
	for (let r in e) (!o(r) || !(r.slice(9) in t)) && (n[r] = e[r]);
	return n;
};
function hr(e, t, n) {
	let { props: r, children: i, component: a } = e, { props: o, children: s, patchFlag: c } = t, l = a.emitsOptions;
	if (t.dirs || t.transition) return !0;
	if (n && c >= 0) {
		if (c & 1024) return !0;
		if (c & 16) return r ? gr(r, o, l) : !!o;
		if (c & 8) {
			let e = t.dynamicProps;
			for (let t = 0; t < e.length; t++) {
				let n = e[t];
				if (_r(o, r, n) && !dr(l, n)) return !0;
			}
		}
	} else return (i || s) && (!s || !s.$stable) ? !0 : r === o ? !1 : r ? !o || gr(r, o, l) : !!o;
	return !1;
}
function gr(e, t, n) {
	let r = Object.keys(t);
	if (r.length !== Object.keys(e).length) return !0;
	for (let i = 0; i < r.length; i++) {
		let a = r[i];
		if (_r(t, e, a) && !dr(n, a)) return !0;
	}
	return !1;
}
function _r(e, t, n) {
	let r = e[n], i = t[n];
	return n === "style" && v(r) && v(i) ? !ye(r, i) : r !== i;
}
function vr({ vnode: e, parent: t, suspense: n }, r) {
	for (; t;) {
		let n = t.subTree;
		if (n.suspense && n.suspense.activeBranch === e && (n.suspense.vnode.el = n.el = r, e = n), n === e) (e = t.vnode).el = r, t = t.parent;
		else break;
	}
	n && n.activeBranch === e && (n.vnode.el = r);
}
var yr = {}, br = () => Object.create(yr), xr = (e) => Object.getPrototypeOf(e) === yr;
function Sr(e, t, n, r = !1) {
	let i = {}, a = br();
	e.propsDefaults = /* @__PURE__ */ Object.create(null), wr(e, t, i, a);
	for (let t in e.propsOptions[0]) t in i || (i[t] = void 0);
	e.props = n ? r ? i : /* @__PURE__ */ Pt(i) : e.type.props ? i : a, e.attrs = a;
}
function Cr(e, t, n, r) {
	let { props: i, attrs: a, vnode: { patchFlag: o } } = e, s = /* @__PURE__ */ I(i), [c] = e.propsOptions, l = !1;
	if ((r || o > 0) && !(o & 16)) {
		if (o & 8) {
			let n = e.vnode.dynamicProps;
			for (let r = 0; r < n.length; r++) {
				let o = n[r];
				if (dr(e.emitsOptions, o)) continue;
				let d = t[o];
				if (c) {
					if (u(a, o)) d !== a[o] && (a[o] = d, l = !0);
					else {
						let t = D(o);
						i[t] = Tr(c, s, t, d, e, !1);
					}
				} else d !== a[o] && (a[o] = d, l = !0);
			}
		}
	} else {
		wr(e, t, i, a) && (l = !0);
		let r;
		for (let a in s) (!t || !u(t, a) && ((r = k(a)) === a || !u(t, r))) && (c ? n && (n[a] !== void 0 || n[r] !== void 0) && (i[a] = Tr(c, s, a, void 0, e, !0)) : delete i[a]);
		if (a !== s) for (let e in a) (!t || !u(t, e)) && (delete a[e], l = !0);
	}
	l && $e(e.attrs, "set", "");
}
function wr(e, n, r, i) {
	let [a, o] = e.propsOptions, s = !1, c;
	if (n) for (let t in n) {
		if (ee(t)) continue;
		let l = n[t], d;
		a && u(a, d = D(t)) ? !o || !o.includes(d) ? r[d] = l : (c ||= {})[d] = l : dr(e.emitsOptions, t) || (!(t in i) || l !== i[t]) && (i[t] = l, s = !0);
	}
	if (o) {
		let n = /* @__PURE__ */ I(r), i = c || t;
		for (let t = 0; t < o.length; t++) {
			let s = o[t];
			r[s] = Tr(a, n, s, i[s], e, !u(i, s));
		}
	}
	return s;
}
function Tr(e, t, n, r, i, a) {
	let o = e[n];
	if (o != null) {
		let e = u(o, "default");
		if (e && r === void 0) {
			let e = o.default;
			if (o.type !== Function && !o.skipFactory && h(e)) {
				let { propsDefaults: a } = i;
				if (n in a) r = a[n];
				else {
					let o = xi(i);
					r = a[n] = e.call(null, t), o();
				}
			} else r = e;
			i.ce && i.ce._setProp(n, r);
		}
		o[0] && (a && !e ? r = !1 : o[1] && (r === "" || r === k(n)) && (r = !0));
	}
	return r;
}
function Er(e, r, i = !1) {
	let a = r.propsCache, o = a.get(e);
	if (o) return o;
	let c = e.props, l = {}, f = [];
	if (!c) return v(e) && a.set(e, n), n;
	if (d(c)) for (let e = 0; e < c.length; e++) {
		let n = D(c[e]);
		Dr(n) && (l[n] = t);
	}
	else if (c) for (let e in c) {
		let t = D(e);
		if (Dr(t)) {
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
function Dr(e) {
	return e[0] !== "$" && !ee(e);
}
var Or = (e) => e === "_" || e === "_ctx" || e === "$stable", kr = (e) => d(e) ? e.map(li) : [li(e)], Ar = (e, t, n) => {
	if (t._n) return t;
	let r = En((...e) => kr(t(...e)), n);
	return r._c = !1, r;
}, jr = (e, t, n) => {
	let r = e._ctx;
	for (let n in e) {
		if (Or(n)) continue;
		let i = e[n];
		if (h(i)) t[n] = Ar(n, i, r);
		else if (i != null) {
			let e = kr(i);
			t[n] = () => e;
		}
	}
}, Mr = (e, t) => {
	let n = kr(t);
	e.slots.default = () => n;
}, Nr = (e, t, n) => {
	for (let r in t) (n || !Or(r)) && (e[r] = t[r]);
}, Pr = (e, t, n) => {
	let r = e.slots = br();
	if (e.vnode.shapeFlag & 32) {
		let e = t._;
		e ? (Nr(r, t, n), n && ie(r, "_", e, !0)) : jr(t, r);
	} else t && Mr(e, t);
}, Fr = (e, n, r) => {
	let { vnode: i, slots: a } = e, o = !0, s = t;
	if (i.shapeFlag & 32) {
		let e = n._;
		e ? r && e === 1 ? o = !1 : Nr(a, n, r) : (o = !n.$stable, jr(n, a)), s = n;
	} else n && (Mr(e, n), s = { default: 1 });
	if (o) for (let e in a) !Or(e) && s[e] == null && delete a[e];
}, U = qr;
function Ir(e) {
	return Lr(e);
}
function Lr(e, i) {
	let a = ce();
	a.__VUE__ = !0;
	let { insert: o, remove: s, patchProp: c, createElement: l, createText: u, createComment: d, setText: f, setElementText: p, parentNode: m, nextSibling: h, setScopeId: g = r, insertStaticContent: _ } = e, v = (e, t, n, r = null, i = null, a = null, o = void 0, s = null, c = !!t.dynamicChildren) => {
		if (e === t) return;
		e && !ri(e, t) && (r = _e(e), pe(e, i, a, !0), e = null), t.patchFlag === -2 && (c = !1, t.dynamicChildren = null);
		let { type: l, ref: u, shapeFlag: d } = t;
		switch (l) {
			case Jr:
				y(e, t, n, r);
				break;
			case Yr:
				b(e, t, n, r);
				break;
			case Xr:
				e ?? x(t, n, r, o);
				break;
			case W:
				ne(e, t, n, r, i, a, o, s, c);
				break;
			default: d & 1 ? w(e, t, n, r, i, a, o, s, c) : d & 6 ? A(e, t, n, r, i, a, o, s, c) : (d & 64 || d & 128) && l.process(e, t, n, r, i, a, o, s, c, be);
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
		if (t.type === "svg" ? o = "svg" : t.type === "math" && (o = "mathml"), e == null) T(t, n, r, i, a, o, s, c);
		else {
			let n = e.el && e.el._isVueCE ? e.el : null;
			try {
				n && n._beginPatch(), O(e, t, i, a, o, s, c);
			} finally {
				n && n._endPatch();
			}
		}
	}, T = (e, t, n, r, i, a, s, u) => {
		let d, f, { props: m, shapeFlag: h, transition: g, dirs: _ } = e;
		if (d = e.el = l(e.type, a, m && m.is, m), h & 8 ? p(d, e.children) : h & 16 && D(e.children, d, null, r, i, Rr(e, a), s, u), _ && On(e, null, r, "created"), E(d, e, e.scopeId, s, r), m) {
			for (let e in m) e !== "value" && !ee(e) && c(d, e, null, m[e], a, r);
			"value" in m && c(d, "value", null, m.value, a), (f = m.onVnodeBeforeMount) && pi(f, r, e);
		}
		_ && On(e, null, r, "beforeMount");
		let v = Br(i, g);
		v && g.beforeEnter(d), o(d, t, n), ((f = m && m.onVnodeMounted) || v || _) && U(() => {
			try {
				f && pi(f, r, e), v && g.enter(d), _ && On(e, null, r, "mounted");
			} finally {}
		}, i);
	}, E = (e, t, n, r, i) => {
		if (n && g(e, n), r) for (let t = 0; t < r.length; t++) g(e, r[t]);
		if (i) {
			let n = i.subTree;
			if (t === n || Kr(n.type) && (n.ssContent === t || n.ssFallback === t)) {
				let t = i.vnode;
				E(e, t, t.scopeId, t.slotScopeIds, i.parent);
			}
		}
	}, D = (e, t, n, r, i, a, o, s, c = 0) => {
		for (let l = c; l < e.length; l++) {
			let c = e[l] = s ? ui(e[l]) : li(e[l]);
			v(null, c, t, n, r, i, a, o, s);
		}
	}, O = (e, n, r, i, a, o, s) => {
		let l = n.el = e.el, { patchFlag: u, dynamicChildren: d, dirs: f } = n;
		u |= e.patchFlag & 16;
		let m = e.props || t, h = n.props || t, g;
		if (r && zr(r, !1), (g = h.onVnodeBeforeUpdate) && pi(g, r, n, e), f && On(n, e, r, "beforeUpdate"), r && zr(r, !0), d && (!e.dynamicChildren || e.dynamicChildren.length !== d.length) && (u = 0, s = !1, d = null), (m.innerHTML && h.innerHTML == null || m.textContent && h.textContent == null) && p(l, ""), d ? k(e.dynamicChildren, d, l, r, i, Rr(n, a), o) : s || le(e, n, l, null, r, i, Rr(n, a), o, !1), u > 0) {
			if (u & 16) te(l, m, h, r, a);
			else if (u & 2 && m.class !== h.class && c(l, "class", null, h.class, a), u & 4 && c(l, "style", m.style, h.style, a), u & 8) {
				let e = n.dynamicProps;
				for (let t = 0; t < e.length; t++) {
					let n = e[t], i = m[n], o = h[n];
					(o !== i || n === "value") && c(l, n, i, o, a, r);
				}
			}
			u & 1 && e.children !== n.children && p(l, n.children);
		} else !s && d == null && te(l, m, h, r, a);
		((g = h.onVnodeUpdated) || f) && U(() => {
			g && pi(g, r, n, e), f && On(n, e, r, "updated");
		}, i);
	}, k = (e, t, n, r, i, a, o) => {
		for (let s = 0; s < t.length; s++) {
			let c = e[s], l = t[s], u = c.el && (c.type === W || !ri(c, l) || c.shapeFlag & 198) ? m(c.el) : n;
			v(c, l, u, null, r, i, a, o, !0);
		}
	}, te = (e, n, r, i, a) => {
		if (n !== r) {
			if (n !== t) for (let t in n) !ee(t) && !(t in r) && c(e, t, n[t], null, a, i);
			for (let t in r) {
				if (ee(t)) continue;
				let o = r[t], s = n[t];
				o !== s && t !== "value" && c(e, t, s, o, a, i);
			}
			"value" in r && c(e, "value", n.value, r.value, a);
		}
	}, ne = (e, t, n, r, i, a, s, c, l) => {
		let d = t.el = e ? e.el : u(""), f = t.anchor = e ? e.anchor : u(""), { patchFlag: p, dynamicChildren: m, slotScopeIds: h } = t;
		h && (c = c ? c.concat(h) : h), e == null ? (o(d, n, r), o(f, n, r), D(t.children || [], n, f, i, a, s, c, l)) : p > 0 && p & 64 && m && e.dynamicChildren && e.dynamicChildren.length === m.length ? (k(e.dynamicChildren, m, n, i, a, s, c), (t.key != null || i && t === i.subTree) && Vr(e, t, !0)) : le(e, t, n, f, i, a, s, c, l);
	}, A = (e, t, n, r, i, a, o, s, c) => {
		t.slotScopeIds = s, e == null ? t.shapeFlag & 512 ? i.ctx.activate(t, n, r, o, c) : ie(t, n, r, i, a, o, c) : ae(e, t, c);
	}, ie = (e, t, n, r, i, a, o) => {
		let s = e.component = gi(e, r, i);
		if (Jn(e) && (s.ctx.renderer = be), Ti(s, !1, o), s.asyncDep) {
			if (i && i.registerDep(s, oe, o), !e.el) {
				let r = s.subTree = X(Yr);
				b(null, r, t, n), e.placeholder = r.el;
			}
		} else oe(s, e, t, n, i, a, o);
	}, ae = (e, t, n) => {
		let r = t.component = e.component;
		if (hr(e, t, n)) {
			if (r.asyncDep && !r.asyncResolved) {
				se(r, t, n);
				return;
			}
			r.next = t, r.update();
		} else t.el = e.el, r.vnode = t;
	}, oe = (e, t, n, r, i, a, o) => {
		let s = () => {
			if (e.isMounted) {
				let { next: t, bu: n, u: r, parent: s, vnode: c } = e;
				{
					let n = Ur(e);
					if (n) {
						t && (t.el = c.el, se(e, t, o)), n.asyncDep.then(() => {
							U(() => {
								e.isUnmounted || l();
							}, i);
						});
						return;
					}
				}
				let u = t, d;
				zr(e, !1), t ? (t.el = c.el, se(e, t, o)) : t = c, n && re(n), (d = t.props && t.props.onVnodeBeforeUpdate) && pi(d, s, t, c), zr(e, !0);
				let f = fr(e), p = e.subTree;
				e.subTree = f, v(p, f, m(p.el), _e(p), e, i, a), t.el = f.el, u === null && vr(e, f.el), r && U(r, i), (d = t.props && t.props.onVnodeUpdated) && U(() => pi(d, s, t, c), i);
			} else {
				let o, { el: s, props: c } = t, { bm: l, m: u, parent: d, root: f, type: p } = e, m = qn(t);
				if (zr(e, !1), l && re(l), !m && (o = c && c.onVnodeBeforeMount) && pi(o, d, t), zr(e, !0), s && xe) {
					let t = () => {
						e.subTree = fr(e), xe(s, e.subTree, e, i, null);
					};
					m && p.__asyncHydrate ? p.__asyncHydrate(s, e, t) : t();
				} else {
					f.ce && f.ce._hasShadowRoot() && f.ce._injectChildStyle(p, e.parent ? e.parent.type : void 0);
					let o = e.subTree = fr(e);
					v(null, o, n, r, e, i, a), t.el = o.el;
				}
				if (u && U(u, i), !m && (o = c && c.onVnodeMounted)) {
					let e = t;
					U(() => pi(o, d, e), i);
				}
				(t.shapeFlag & 256 || d && qn(d.vnode) && d.vnode.shapeFlag & 256) && e.a && U(e.a, i), e.isMounted = !0, t = n = r = null;
			}
		};
		e.scope.on();
		let c = e.effect = new De(s);
		e.scope.off();
		let l = e.update = c.run.bind(c), u = e.job = c.runIfDirty.bind(c);
		u.i = e, u.id = e.uid, c.scheduler = () => gn(u), zr(e, !0), l();
	}, se = (e, t, n) => {
		t.component = e;
		let r = e.vnode.props;
		e.vnode = t, e.next = null, Cr(e, t.props, r, n), Fr(e, t.children, n), He(), yn(e), Ue();
	}, le = (e, t, n, r, i, a, o, s, c = !1) => {
		let l = e && e.children, u = e ? e.shapeFlag : 0, d = t.children, { patchFlag: f, shapeFlag: m } = t;
		if (f > 0) {
			if (f & 128) {
				de(l, d, n, r, i, a, o, s, c);
				return;
			}
			if (f & 256) {
				ue(l, d, n, r, i, a, o, s, c);
				return;
			}
		}
		m & 8 ? (u & 16 && ge(l, i, a), d !== l && p(n, d)) : u & 16 ? m & 16 ? de(l, d, n, r, i, a, o, s, c) : ge(l, i, a, !0) : (u & 8 && p(n, ""), m & 16 && D(d, n, r, i, a, o, s, c));
	}, ue = (e, t, r, i, a, o, s, c, l) => {
		e ||= n, t ||= n;
		let u = e.length, d = t.length, f = Math.min(u, d), p = 0;
		for (; p < f; p++) {
			let n = t[p] = l ? ui(t[p]) : li(t[p]);
			v(e[p], n, r, null, a, o, s, c, l);
		}
		u > d ? ge(e, a, o, !0, !1, f) : D(t, r, i, a, o, s, c, l, f);
	}, de = (e, t, r, i, a, o, s, c, l) => {
		let u = 0, d = t.length, f = e.length - 1, p = d - 1;
		for (; u <= f && u <= p;) {
			let n = e[u], i = t[u] = l ? ui(t[u]) : li(t[u]);
			if (ri(n, i)) v(n, i, r, null, a, o, s, c, l);
			else break;
			u++;
		}
		for (; u <= f && u <= p;) {
			let n = e[f], i = t[p] = l ? ui(t[p]) : li(t[p]);
			if (ri(n, i)) v(n, i, r, null, a, o, s, c, l);
			else break;
			f--, p--;
		}
		if (u > f) {
			if (u <= p) {
				let e = p + 1, n = e < d ? t[e].el : i;
				for (; u <= p;) v(null, t[u] = l ? ui(t[u]) : li(t[u]), r, n, a, o, s, c, l), u++;
			}
		} else if (u > p) for (; u <= f;) pe(e[u], a, o, !0), u++;
		else {
			let m = u, h = u, g = /* @__PURE__ */ new Map();
			for (u = h; u <= p; u++) {
				let e = t[u] = l ? ui(t[u]) : li(t[u]);
				e.key != null && g.set(e.key, u);
			}
			let _, y = 0, b = p - h + 1, x = !1, S = 0, C = Array(b);
			for (u = 0; u < b; u++) C[u] = 0;
			for (u = m; u <= f; u++) {
				let n = e[u];
				if (y >= b) {
					pe(n, a, o, !0);
					continue;
				}
				let i;
				if (n.key != null) i = g.get(n.key);
				else for (_ = h; _ <= p; _++) if (C[_ - h] === 0 && ri(n, t[_])) {
					i = _;
					break;
				}
				i === void 0 ? pe(n, a, o, !0) : (C[i - h] = u + 1, i >= S ? S = i : x = !0, v(n, t[i], r, null, a, o, s, c, l), y++);
			}
			let w = x ? Hr(C) : n;
			for (_ = w.length - 1, u = b - 1; u >= 0; u--) {
				let e = h + u, n = t[e], f = t[e + 1], p = e + 1 < d ? f.el || Gr(f) : i;
				C[u] === 0 ? v(null, n, r, p, a, o, s, c, l) : x && (_ < 0 || u !== w[_] ? fe(n, r, p, 2) : _--);
			}
		}
	}, fe = (e, t, n, r, i = null) => {
		let { el: a, type: c, transition: l, children: u, shapeFlag: d } = e;
		if (d & 6) {
			fe(e.component.subTree, t, n, r);
			return;
		}
		if (d & 128) {
			e.suspense.move(t, n, r);
			return;
		}
		if (d & 64) {
			c.move(e, t, n, be);
			return;
		}
		if (c === W) {
			o(a, t, n);
			for (let e = 0; e < u.length; e++) fe(u[e], t, n, r);
			o(e.anchor, t, n);
			return;
		}
		if (c === Xr) {
			S(e, t, n);
			return;
		}
		if (r !== 2 && d & 1 && l) {
			if (r === 0) l.persisted && !a[Ln] ? o(a, t, n) : (l.beforeEnter(a), o(a, t, n), U(() => l.enter(a), i));
			else {
				let { leave: r, delayLeave: i, afterLeave: c } = l, u = () => {
					e.ctx.isUnmounted ? s(a) : o(a, t, n);
				}, d = () => {
					let e = a._isLeaving || !!a[Ln];
					a._isLeaving && a[Ln](!0), l.persisted && !e ? u() : r(a, () => {
						u(), c && c();
					});
				};
				i ? i(a, u, d) : d();
			}
		} else o(a, t, n);
	}, pe = (e, t, n, r = !1, i = !1) => {
		let { type: a, props: o, ref: s, children: c, dynamicChildren: l, shapeFlag: u, patchFlag: d, dirs: f, cacheIndex: p, memo: m } = e;
		if (d === -2 && (i = !1), s != null && (He(), Gn(s, null, n, e, !0), Ue()), p != null && (t.renderCache[p] = void 0), u & 256) {
			t.ctx.deactivate(e);
			return;
		}
		let h = u & 1 && f, g = !qn(e), _;
		if (g && (_ = o && o.onVnodeBeforeUnmount) && pi(_, t, e), u & 6) he(e.component, n, r);
		else {
			if (u & 128) {
				e.suspense.unmount(n, r);
				return;
			}
			h && On(e, null, t, "beforeUnmount"), u & 64 ? e.type.remove(e, t, n, be, r) : l && !l.hasOnce && (a !== W || d > 0 && d & 64) ? ge(l, t, n, !1, !0) : (a === W && d & 384 || !i && u & 16) && ge(c, t, n), r && j(e);
		}
		let v = m != null && p == null;
		(g && (_ = o && o.onVnodeUnmounted) || h || v) && U(() => {
			_ && pi(_, t, e), h && On(e, null, t, "unmounted"), v && (e.el = null);
		}, n);
	}, j = (e) => {
		let { type: t, el: n, anchor: r, transition: i } = e;
		if (t === W) {
			me(n, r);
			return;
		}
		if (t === Xr) {
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
	}, me = (e, t) => {
		let n;
		for (; e !== t;) n = h(e), s(e), e = n;
		s(t);
	}, he = (e, t, n) => {
		let { bum: r, scope: i, job: a, subTree: o, um: s, m: c, a: l } = e;
		Wr(c), Wr(l), r && re(r), i.stop(), a && (a.flags |= 8, pe(o, e, t, n)), s && U(s, t), U(() => {
			e.isUnmounted = !0;
		}, t);
	}, ge = (e, t, n, r = !1, i = !1, a = 0) => {
		for (let o = a; o < e.length; o++) pe(e[o], t, n, r, i);
	}, _e = (e) => {
		if (e.shapeFlag & 6) return _e(e.component.subTree);
		if (e.shapeFlag & 128) return e.suspense.next();
		let t = h(e.anchor || e.el), n = t && t[Fn];
		return n ? h(n) : t;
	}, ve = !1, ye = (e, t, n) => {
		let r;
		e == null ? t._vnode && (pe(t._vnode, null, null, !0), r = t._vnode.component) : v(t._vnode || null, e, t, null, null, null, n), t._vnode = e, ve ||= (ve = !0, yn(r), bn(), !1);
	}, be = {
		p: v,
		um: pe,
		m: fe,
		r: j,
		mt: ie,
		mc: D,
		pc: le,
		pbc: k,
		n: _e,
		o: e
	}, M, xe;
	return i && ([M, xe] = i(be)), {
		render: ye,
		hydrate: M,
		createApp: or(ye, M)
	};
}
function Rr({ type: e, props: t }, n) {
	return n === "svg" && e === "foreignObject" || n === "mathml" && e === "annotation-xml" && t && t.encoding && t.encoding.includes("html") ? void 0 : n;
}
function zr({ effect: e, job: t }, n) {
	n ? (e.flags |= 32, t.flags |= 4) : (e.flags &= -33, t.flags &= -5);
}
function Br(e, t) {
	return (!e || e && !e.pendingBranch) && t && !t.persisted;
}
function Vr(e, t, n = !1) {
	let r = e.children, i = t.children;
	if (d(r) && d(i)) for (let e = 0; e < r.length; e++) {
		let t = r[e], a = i[e];
		a.shapeFlag & 1 && !a.dynamicChildren && ((a.patchFlag <= 0 || a.patchFlag === 32) && (a = i[e] = ui(i[e]), a.el = t.el), !n && a.patchFlag !== -2 && Vr(t, a)), a.type === Jr && (a.patchFlag === -1 && (a = i[e] = ui(a)), a.el = t.el), a.type === Yr && !a.el && (a.el = t.el);
	}
}
function Hr(e) {
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
function Ur(e) {
	let t = e.subTree.component;
	if (t) return t.asyncDep && !t.asyncResolved ? t : Ur(t);
}
function Wr(e) {
	if (e) for (let t = 0; t < e.length; t++) e[t].flags |= 8;
}
function Gr(e) {
	if (e.placeholder) return e.placeholder;
	let t = e.component;
	return t ? Gr(t.subTree) : null;
}
var Kr = (e) => e.__isSuspense;
function qr(e, t) {
	t && t.pendingBranch ? d(e) ? t.effects.push(...e) : t.effects.push(e) : vn(e);
}
var W = /* @__PURE__ */ Symbol.for("v-fgt"), Jr = /* @__PURE__ */ Symbol.for("v-txt"), Yr = /* @__PURE__ */ Symbol.for("v-cmt"), Xr = /* @__PURE__ */ Symbol.for("v-stc"), Zr = [], G = null;
function K(e = !1) {
	Zr.push(G = e ? null : []);
}
function Qr() {
	Zr.pop(), G = Zr[Zr.length - 1] || null;
}
var $r = 1;
function ei(e, t = !1) {
	$r += e, e < 0 && G && t && (G.hasOnce = !0);
}
function ti(e) {
	return e.dynamicChildren = $r > 0 ? G || n : null, Qr(), $r > 0 && G && G.push(e), e;
}
function q(e, t, n, r, i, a) {
	return ti(Y(e, t, n, r, i, a, !0));
}
function J(e, t, n, r, i) {
	return ti(X(e, t, n, r, i, !0));
}
function ni(e) {
	return e ? e.__v_isVNode === !0 : !1;
}
function ri(e, t) {
	return e.type === t.type && e.key === t.key;
}
var ii = ({ key: e }) => e ?? null, ai = ({ ref: e, ref_key: t, ref_for: n }) => (typeof e == "number" && (e = "" + e), e == null ? null : g(e) || /* @__PURE__ */ L(e) || h(e) ? {
	i: Cn,
	r: e,
	k: t,
	f: !!n
} : e);
function Y(e, t = null, n = null, r = 0, i = null, a = e === W ? 0 : 1, o = !1, s = !1) {
	let c = {
		__v_isVNode: !0,
		__v_skip: !0,
		type: e,
		props: t,
		key: t && ii(t),
		ref: t && ai(t),
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
	return s ? (di(c, n), a & 128 && e.normalize(c)) : n && (c.shapeFlag |= g(n) ? 8 : 16), $r > 0 && !o && G && (c.patchFlag > 0 || a & 6) && c.patchFlag !== 32 && G.push(c), c;
}
var X = oi;
function oi(e, t = null, n = null, r = 0, i = null, a = !1) {
	if ((!e || e === $n) && (e = Yr), ni(e)) {
		let r = ci(e, t, !0);
		return n && di(r, n), $r > 0 && !a && G && (r.shapeFlag & 6 ? G[G.indexOf(e)] = r : G.push(r)), r.patchFlag = -2, r;
	}
	if (Mi(e) && (e = e.__vccOpts), t) {
		t = si(t);
		let { class: e, style: n } = t;
		e && !g(e) && (t.class = j(e)), v(n) && (/* @__PURE__ */ Bt(n) && !d(n) && (n = s({}, n)), t.style = le(n));
	}
	let o = g(e) ? 1 : Kr(e) ? 128 : In(e) ? 64 : v(e) ? 4 : h(e) ? 2 : 0;
	return Y(e, t, n, r, i, o, a, !0);
}
function si(e) {
	return e ? /* @__PURE__ */ Bt(e) || xr(e) ? s({}, e) : e : null;
}
function ci(e, t, n = !1, r = !1) {
	let { props: i, ref: a, patchFlag: o, children: s, transition: c } = e, l = t ? fi(i || {}, t) : i, u = {
		__v_isVNode: !0,
		__v_skip: !0,
		type: e.type,
		props: l,
		key: l && ii(l),
		ref: t && t.ref ? n && a ? d(a) ? a.concat(ai(t)) : [a, ai(t)] : ai(t) : a,
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
		ssContent: e.ssContent && ci(e.ssContent),
		ssFallback: e.ssFallback && ci(e.ssFallback),
		placeholder: e.placeholder,
		el: e.el,
		anchor: e.anchor,
		ctx: e.ctx,
		ce: e.ce
	};
	return c && r && Bn(u, c.clone(u)), u;
}
function Z(e = " ", t = 0) {
	return X(Jr, null, e, t);
}
function Q(e = "", t = !1) {
	return t ? (K(), J(Yr, null, e)) : X(Yr, null, e);
}
function li(e) {
	return e == null || typeof e == "boolean" ? X(Yr) : d(e) ? X(W, null, e.slice()) : ni(e) ? ui(e) : X(Jr, null, String(e));
}
function ui(e) {
	return e.el === null && e.patchFlag !== -1 || e.memo ? e : ci(e);
}
function di(e, t) {
	let n = 0, { shapeFlag: r } = e;
	if (t == null) t = null;
	else if (d(t)) n = 16;
	else if (typeof t == "object") {
		if (r & 65) {
			let n = t.default;
			n && (n._c && (n._d = !1), di(e, n()), n._c && (n._d = !0));
			return;
		}
		{
			n = 32;
			let r = t._;
			!r && !xr(t) ? t._ctx = Cn : r === 3 && Cn && (Cn.slots._ === 1 ? t._ = 1 : (t._ = 2, e.patchFlag |= 1024));
		}
	} else if (h(t)) {
		if (r & 65) {
			di(e, { default: t });
			return;
		}
		t = {
			default: t,
			_ctx: Cn
		}, n = 32;
	} else t = String(t), r & 64 ? (n = 16, t = [Z(t)]) : n = 8;
	e.children = t, e.shapeFlag |= n;
}
function fi(...e) {
	let t = {};
	for (let n = 0; n < e.length; n++) {
		let r = e[n];
		for (let e in r) if (e === "class") t.class !== r.class && (t.class = j([t.class, r.class]));
		else if (e === "style") t.style = le([t.style, r.style]);
		else if (a(e)) {
			let n = t[e], i = r[e];
			i && n !== i && !(d(n) && n.includes(i)) ? t[e] = n ? [].concat(n, i) : i : i == null && n == null && !o(e) && (t[e] = i);
		} else e !== "" && (t[e] = r[e]);
	}
	return t;
}
function pi(e, t, n, r = null) {
	an(e, t, 7, [n, r]);
}
var mi = ir(), hi = 0;
function gi(e, n, r) {
	let i = e.type, a = (n ? n.appContext : e.appContext) || mi, o = {
		uid: hi++,
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
		scope: new Ce(!0),
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
		propsOptions: Er(i, a),
		emitsOptions: ur(i, a),
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
	return o.ctx = { _: o }, o.root = n ? n.root : o, o.emit = lr.bind(null, o), e.ce && e.ce(o), o;
}
var _i = null, vi = () => _i || Cn, yi, bi;
{
	let e = ce(), t = (t, n) => {
		let r;
		return (r = e[t]) || (r = e[t] = []), r.push(n), (e) => {
			r.length > 1 ? r.forEach((t) => t(e)) : r[0](e);
		};
	};
	yi = t("__VUE_INSTANCE_SETTERS__", (e) => _i = e), bi = t("__VUE_SSR_SETTERS__", (e) => wi = e);
}
var xi = (e) => {
	let t = _i;
	return yi(e), e.scope.on(), () => {
		e.scope.off(), yi(t);
	};
}, Si = () => {
	_i && _i.scope.off(), yi(null);
};
function Ci(e) {
	return e.vnode.shapeFlag & 4;
}
var wi = !1;
function Ti(e, t = !1, n = !1) {
	t && bi(t);
	let { props: r, children: i } = e.vnode, a = Ci(e);
	Sr(e, r, a, t), Pr(e, i, n || t);
	let o = a ? Ei(e, t) : void 0;
	return t && bi(!1), o;
}
function Ei(e, t) {
	let n = e.type;
	e.accessCache = /* @__PURE__ */ Object.create(null), e.proxy = new Proxy(e.ctx, rr);
	let { setup: r } = n;
	if (r) {
		He();
		let n = e.setupContext = r.length > 1 ? Ai(e) : null, i = xi(e), a = rn(r, e, 0, [e.props, n]), o = y(a);
		if (Ue(), i(), (o || e.sp) && !qn(e) && Hn(e), o) {
			if (a.then(Si, Si), t) return a.then((n) => {
				bi(!0);
				try {
					Di(e, n, t);
				} finally {
					bi(!1);
				}
			}).catch((t) => {
				on(t, e, 0);
			});
			e.asyncDep = a;
		} else Di(e, a, t);
	} else Oi(e, t);
}
function Di(e, t, n) {
	h(t) ? e.type.__ssrInlineRender ? e.ssrRender = t : e.render = t : v(t) && (e.setupState = Jt(t)), Oi(e, n);
}
function Oi(e, t, n) {
	let i = e.type;
	e.render ||= i.render || r;
}
var ki = { get(e, t) {
	return F(e, "get", ""), e[t];
} };
function Ai(e) {
	return {
		attrs: new Proxy(e.attrs, ki),
		slots: e.slots,
		emit: e.emit,
		expose: (t) => {
			e.exposed = t || {};
		}
	};
}
function ji(e) {
	return e.exposed ? e.exposeProxy ||= new Proxy(Jt(Vt(e.exposed)), {
		get(t, n) {
			if (n in t) return t[n];
			if (n in tr) return tr[n](e);
		},
		has(e, t) {
			return t in e || t in tr;
		}
	}) : e.proxy;
}
function Mi(e) {
	return h(e) && "__vccOpts" in e;
}
var $ = (e, t) => /* @__PURE__ */ Xt(e, t, wi), Ni = "3.5.42", Pi = void 0, Fi = typeof window < "u" && window.trustedTypes;
if (Fi) try {
	Pi = /* @__PURE__ */ Fi.createPolicy("vue", { createHTML: (e) => e });
} catch {}
var Ii = Pi ? (e) => Pi.createHTML(e) : (e) => e, Li = "http://www.w3.org/2000/svg", Ri = "http://www.w3.org/1998/Math/MathML", zi = typeof document < "u" ? document : null, Bi = zi && /* @__PURE__ */ zi.createElement("template"), Vi = {
	insert: (e, t, n) => {
		t.insertBefore(e, n || null);
	},
	remove: (e) => {
		let t = e.parentNode;
		t && t.removeChild(e);
	},
	createElement: (e, t, n, r) => {
		let i = t === "svg" ? zi.createElementNS(Li, e) : t === "mathml" ? zi.createElementNS(Ri, e) : n ? zi.createElement(e, { is: n }) : zi.createElement(e);
		return e === "select" && r && r.multiple != null && i.setAttribute("multiple", r.multiple), i;
	},
	createText: (e) => zi.createTextNode(e),
	createComment: (e) => zi.createComment(e),
	setText: (e, t) => {
		e.nodeValue = t;
	},
	setElementText: (e, t) => {
		e.textContent = t;
	},
	parentNode: (e) => e.parentNode,
	nextSibling: (e) => e.nextSibling,
	querySelector: (e) => zi.querySelector(e),
	setScopeId(e, t) {
		e.setAttribute(t, "");
	},
	insertStaticContent(e, t, n, r, i, a) {
		let o = n ? n.previousSibling : t.lastChild;
		if (i && (i === a || i.nextSibling)) for (; t.insertBefore(i.cloneNode(!0), n), i !== a && (i = i.nextSibling););
		else {
			Bi.innerHTML = Ii(r === "svg" ? `<svg>${e}</svg>` : r === "mathml" ? `<math>${e}</math>` : e);
			let i = Bi.content;
			if (r === "svg" || r === "mathml") {
				let e = i.firstChild;
				for (; e.firstChild;) i.appendChild(e.firstChild);
				i.removeChild(e);
			}
			t.insertBefore(i, n);
		}
		return [o ? o.nextSibling : t.firstChild, n ? n.previousSibling : t.lastChild];
	}
}, Hi = /* @__PURE__ */ Symbol("_vtc");
function Ui(e, t, n) {
	let r = e[Hi];
	r && (t = (t ? [t, ...r] : [...r]).join(" ")), t == null ? e.removeAttribute("class") : n ? e.setAttribute("class", t) : e.className = t;
}
var Wi = /* @__PURE__ */ Symbol("_vod"), Gi = /* @__PURE__ */ Symbol("_vsh"), Ki = {
	name: "show",
	beforeMount(e, { value: t }, { transition: n }) {
		e[Wi] = e.style.display === "none" ? "" : e.style.display, n && t ? n.beforeEnter(e) : qi(e, t);
	},
	mounted(e, { value: t }, { transition: n }) {
		n && t && n.enter(e);
	},
	updated(e, { value: t, oldValue: n }, { transition: r }) {
		!t != !n && (r ? t ? (r.beforeEnter(e), qi(e, !0), r.enter(e)) : r.leave(e, () => {
			qi(e, !1);
		}) : qi(e, t));
	},
	beforeUnmount(e, { value: t }) {
		qi(e, t);
	}
};
function qi(e, t) {
	e.style.display = t ? e[Wi] : "none", e[Gi] = !t;
}
var Ji = /* @__PURE__ */ Symbol(""), Yi = /(?:^|;)\s*display\s*:/;
function Xi(e, t, n) {
	let r = e.style, i = g(n), a = !1;
	if (n && !i) {
		if (t) {
			if (g(t)) for (let e of t.split(";")) {
				let t = e.slice(0, e.indexOf(":")).trim();
				n[t] ?? Qi(r, t, "");
			}
			else for (let e in t) n[e] ?? Qi(r, e, "");
		}
		for (let i in n) {
			i === "display" && (a = !0);
			let o = n[i];
			o == null ? Qi(r, i, "") : na(e, i, !g(t) && t ? t[i] : void 0, o) || Qi(r, i, o);
		}
	} else if (i) {
		if (t !== n) {
			let e = r[Ji];
			e && (n += ";" + e), r.cssText = n, a = Yi.test(n);
		}
	} else t && e.removeAttribute("style");
	Wi in e && (e[Wi] = a ? r.display : "", e[Gi] && (r.display = "none"));
}
var Zi = /\s*!important$/;
function Qi(e, t, n) {
	if (d(n)) n.forEach((n) => Qi(e, t, n));
	else if (n ??= "", t.startsWith("--")) Zi.test(n) ? e.setProperty(t, n.replace(Zi, ""), "important") : e.setProperty(t, n);
	else {
		let r = ta(e, t);
		Zi.test(n) ? e.setProperty(k(r), n.replace(Zi, ""), "important") : e[r] = n;
	}
}
var $i = [
	"Webkit",
	"Moz",
	"ms"
], ea = {};
function ta(e, t) {
	let n = ea[t];
	if (n) return n;
	let r = D(t);
	if (r !== "filter" && r in e) return ea[t] = r;
	r = te(r);
	for (let n = 0; n < $i.length; n++) {
		let i = $i[n] + r;
		if (i in e) return ea[t] = i;
	}
	return t;
}
function na(e, t, n, r) {
	return e.tagName === "TEXTAREA" && (t === "width" || t === "height") && g(r) && n === r;
}
var ra = "http://www.w3.org/1999/xlink";
function ia(e, t, n, r, i, a = he(t)) {
	r && t.startsWith("xlink:") ? n == null ? e.removeAttributeNS(ra, t.slice(6, t.length)) : e.setAttributeNS(ra, t, n) : n == null || a && !ge(n) ? e.removeAttribute(t) : e.setAttribute(t, a ? "" : _(n) ? String(n) : n);
}
function aa(e, t, n, r, i) {
	if (t === "innerHTML" || t === "textContent") {
		n != null && (e[t] = t === "innerHTML" ? Ii(n) : n);
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
		r === "boolean" ? n = ge(n) : n == null && r === "string" ? (n = "", o = !0) : r === "number" && (n = 0, o = !0);
	}
	try {
		e[t] = n;
	} catch {}
	o && e.removeAttribute(i || t);
}
function oa(e, t, n, r) {
	e.addEventListener(t, n, r);
}
function sa(e, t, n, r) {
	e.removeEventListener(t, n, r);
}
var ca = /* @__PURE__ */ Symbol("_vei");
function la(e, t, n, r, i = null) {
	let a = e[ca] || (e[ca] = {}), o = a[t];
	if (r && o) o.value = r;
	else {
		let [n, s] = fa(t);
		r ? oa(e, n, a[t] = ga(r, i), s) : o && (sa(e, n, o, s), a[t] = void 0);
	}
}
var ua = /(Once|Passive|Capture)$/, da = /^on:?(?:Once|Passive|Capture)$/;
function fa(e) {
	let t, n;
	for (; (n = e.match(ua)) && !da.test(e);) t ||= {}, e = e.slice(0, e.length - n[1].length), t[n[1].toLowerCase()] = !0;
	return [e[2] === ":" ? e.slice(3) : k(e.slice(2)), t];
}
var pa = 0, ma = /* @__PURE__ */ Promise.resolve(), ha = () => pa ||= (ma.then(() => pa = 0), Date.now());
function ga(e, t) {
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
				e && an(e, t, 5, a);
			}
		} else an(r, t, 5, [e]);
	};
	return n.value = e, n.attached = ha(), n;
}
var _a = (e) => e.charCodeAt(0) === 111 && e.charCodeAt(1) === 110 && e.charCodeAt(2) > 96 && e.charCodeAt(2) < 123, va = (e, t, n, r, i, s) => {
	let c = i === "svg";
	t === "class" ? Ui(e, r, c) : t === "style" ? Xi(e, n, r) : a(t) ? o(t) || la(e, t, n, r, s) : (t[0] === "." ? (t = t.slice(1), 1) : t[0] === "^" ? (t = t.slice(1), 0) : ya(e, t, r, c)) ? (aa(e, t, r), !e.tagName.includes("-") && (t === "value" || t === "checked" || t === "selected") && ia(e, t, r, c, s, t !== "value")) : e._isVueCE && (ba(e, t) || e._def.__asyncLoader && (/[A-Z]/.test(t) || !g(r))) ? aa(e, D(t), r, s, t) : (t === "true-value" ? e._trueValue = r : t === "false-value" && (e._falseValue = r), ia(e, t, r, c));
};
function ya(e, t, n, r) {
	if (r) return !!(t === "innerHTML" || t === "textContent" || t in e && _a(t) && h(n));
	if (t === "spellcheck" || t === "draggable" || t === "translate" || t === "autocorrect" || t === "sandbox" && e.tagName === "IFRAME" || t === "form" || t === "list" && e.tagName === "INPUT" || t === "type" && e.tagName === "TEXTAREA") return !1;
	if (t === "width" || t === "height") {
		let t = e.tagName;
		if (t === "IMG" || t === "VIDEO" || t === "CANVAS" || t === "SOURCE") return !1;
	}
	return _a(t) && g(n) ? !1 : t in e;
}
function ba(e, t) {
	let n = e._def.props;
	if (!n) return !1;
	let r = D(t);
	return Array.isArray(n) ? n.some((e) => D(e) === r) : Object.keys(n).some((e) => D(e) === r);
}
var xa = {};
// @__NO_SIDE_EFFECTS__
function Sa(e, t, n) {
	let r = /* @__PURE__ */ V(e, t);
	C(r) && (r = s({}, r, t));
	class i extends wa {
		constructor(e) {
			super(r, e, n);
		}
	}
	return i.def = r, i;
}
var Ca = typeof HTMLElement < "u" ? HTMLElement : class {}, wa = class e extends Ca {
	constructor(e, t = {}, n = Ba) {
		super(), this._def = e, this._props = t, this._createApp = n, this._isVueCE = !0, this._instance = null, this._app = null, this._nonce = this._def.nonce, this._connected = !1, this._resolved = !1, this._patching = !1, this._dirty = !1, this._numberProps = null, this._styleChildren = /* @__PURE__ */ new WeakSet(), this._styleAnchors = /* @__PURE__ */ new WeakMap(), this._ob = null, this.shadowRoot && n !== Ba ? this._root = this.shadowRoot : e.shadowRoot === !1 ? this._root = this : (this.attachShadow(s({}, e.shadowRootOptions, { mode: "open" })), this._root = this.shadowRoot);
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
				(t === Number || t && t.type === Number) && (e in this._props && (this._props[e] = oe(this._props[e])), (i ||= /* @__PURE__ */ Object.create(null))[D(e)] = !0);
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
		if (t) for (let e in t) u(this, e) || Object.defineProperty(this, e, { get: () => z(t[e]) });
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
		let t = this.hasAttribute(e), n = t ? this.getAttribute(e) : xa, r = D(e);
		t && this._numberProps && this._numberProps[r] && (n = oe(n)), this._setProp(r, n, !1, !0);
	}
	_getProp(e) {
		return this._props[e];
	}
	_setProp(e, t, n = !0, r = !1) {
		if (t !== this._props[e] && (this._dirty = !0, t === xa ? delete this._props[e] : (this._props[e] = t, e === "key" && this._app && (this._app._ceVNode.key = t)), r && this._instance && this._update(), n)) {
			let n = this._ob;
			n && (this._processMutations(n.takeRecords()), n.disconnect()), t === !0 ? this.setAttribute(k(e), "") : typeof t == "string" || typeof t == "number" ? this.setAttribute(k(e), t + "") : t || this.removeAttribute(k(e)), n && n.observe(this, { attributes: !0 });
		}
	}
	_update() {
		let e = this._createVNode();
		this._app && (e.appContext = this._app._context), za(e, this._root);
	}
	_createVNode() {
		let e = {};
		this.shadowRoot || (e.onVnodeMounted = e.onVnodeUpdated = this._renderSlots.bind(this));
		let t = X(this._def, s(e, this._props));
		return this._instance || (t.ce = (e) => {
			this._instance = e, e.ce = this, e.isCE = !0;
			let t = (e, t) => {
				this.dispatchEvent(new CustomEvent(e, C(t[0]) ? s({ detail: t }, t[0]) : { detail: t }));
			};
			e.emit = (e, ...n) => {
				t(e, n), k(e) !== e && t(k(e), n);
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
function Ta(e) {
	let t = vi();
	return t && t.ce || null;
}
var Ea = (e) => {
	let t = e.props["onUpdate:modelValue"] || !1;
	return d(t) ? (e) => re(t, e) : t;
};
function Da(e) {
	e.target.composing = !0;
}
function Oa(e) {
	let t = e.target;
	t.composing && (t.composing = !1, t.dispatchEvent(new Event("input")));
}
var ka = /* @__PURE__ */ Symbol("_assign"), Aa = /* @__PURE__ */ Symbol("_initialValue");
function ja(e, t, n) {
	return t && (e = e.trim()), n && (e = ae(e)), e;
}
var Ma = {
	created(e, { modifiers: { lazy: t, trim: n, number: r } }, i) {
		e.parentNode && (e.type === "text" ? e[Aa] = e.defaultValue.replace(/[\r\n]/g, "") : e.type === "textarea" && (e[Aa] = e.defaultValue.replace(/\r\n?/g, "\n"))), e[ka] = Ea(i);
		let a = r || i.props && i.props.type === "number";
		oa(e, t ? "change" : "input", (t) => {
			t.target.composing || e[ka](ja(e.value, n, a));
		}), (n || a) && oa(e, "change", () => {
			e.value = ja(e.value, n, a);
		}), t || (oa(e, "compositionstart", Da), oa(e, "compositionend", Oa), oa(e, "change", Oa));
	},
	mounted(e, { value: t, modifiers: { trim: n, number: r } }) {
		let i = t ?? "", a = e[Aa];
		delete e[Aa], a !== void 0 && (e.type === "text" || e.type === "textarea") && e.value !== a ? e[ka](ja(e.value, n, r)) : e.value = i;
	},
	beforeUpdate(e, { value: t, oldValue: n, modifiers: { lazy: r, trim: i, number: a } }, o) {
		if (e[ka] = Ea(o), e.composing) return;
		let s = (a || e.type === "number") && !/^0\d/.test(e.value) ? ae(e.value) : e.value, c = t ?? "";
		if (s === c) return;
		let l = e.getRootNode();
		(l instanceof Document || l instanceof ShadowRoot) && l.activeElement === e && e.type !== "range" && (r && t === n || i && e.value.trim() === c) || (e.value = c);
	}
}, Na = [
	"ctrl",
	"shift",
	"alt",
	"meta"
], Pa = {
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
	exact: (e, t) => Na.some((n) => e[`${n}Key`] && !t.includes(n))
}, Fa = (e, t) => {
	if (!e) return e;
	let n = e._withMods ||= {}, r = t.join(".");
	return n[r] || (n[r] = ((n, ...r) => {
		for (let e = 0; e < t.length; e++) {
			let r = Pa[t[e]];
			if (r && r(n, t)) return;
		}
		return e(n, ...r);
	}));
}, Ia = /* @__PURE__ */ s({ patchProp: va }, Vi), La;
function Ra() {
	return La ||= Ir(Ia);
}
var za = ((...e) => {
	Ra().render(...e);
}), Ba = ((...e) => {
	let t = Ra().createApp(...e), { mount: n } = t;
	return t.mount = (e) => {
		let r = Ha(e);
		if (!r) return;
		let i = t._component;
		!h(i) && !i.render && !i.template && (i.template = r.innerHTML), r.nodeType === 1 && (r.textContent = "");
		let a = n(r, !1, Va(r));
		return r instanceof Element && (r.removeAttribute("v-cloak"), r.setAttribute("data-v-app", "")), a;
	}, t;
});
function Va(e) {
	if (e instanceof SVGElement) return "svg";
	if (typeof MathMLElement == "function" && e instanceof MathMLElement) return "mathml";
}
function Ha(e) {
	return g(e) ? document.querySelector(e) : e;
}
//#endregion
//#region src/tabs.ts
var Ua = [
	{
		path: "allgemein",
		de: "Allgemeine Informationen",
		en: "General information"
	},
	{
		path: "ladeautomatik",
		de: "Zeitvariabler Tarif",
		en: "Time-of-use tariff"
	},
	{
		path: "dynamisches-laden",
		de: "Dynamischer Tarif",
		en: "Dynamic tariff"
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
function Wa(e, t) {
	let n = e.split(/[?#]/, 1)[0].replace(/\/+$/, "");
	return (n.startsWith(`${t}/`) ? n.slice(t.length) : n === t ? "" : n).replace(/^\//, "") || Ua[0].path;
}
var Ga = {
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
}, Ka = {
	de: {
		unavailable: "Nicht verfügbar",
		unknown: "Unbekannt",
		disconnected: "Keine Verbindung zu Home Assistant.",
		loadFailed: "Die SAX Power Entitäten konnten nicht geladen werden.",
		forbidden: "Diese Entität kann derzeit nicht bedient werden.",
		invalid: "Bitte einen gültigen Wert im erlaubten Bereich eingeben.",
		failed: "Die Änderung ist fehlgeschlagen. Bitte den aktuellen Zustand prüfen und erneut versuchen.",
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
		failed: "The change failed. Please check the current state and try again.",
		on: "On",
		off: "Off"
	}
}, qa = Symbol("sax-dashboard");
function Ja(e) {
	return typeof e != "string" || e.length !== 5 && e.length !== 8 || !/^([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(e) ? null : e.length === 5 ? `${e}:00` : e;
}
function Ya(e, t, n, r, i) {
	let a = Ka[r];
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
function Xa(e, t) {
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
			let e = Ja(t);
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
function Za(e, t) {
	let n = $(() => e()?.language.toLowerCase().startsWith("de") ? "de" : "en"), r = /* @__PURE__ */ R(!1), i = /* @__PURE__ */ R(!1), a = /* @__PURE__ */ R(null), o = $(() => a.value ? Ka[n.value][a.value] : null), s = /* @__PURE__ */ Wt([]), c = /* @__PURE__ */ Nt(/* @__PURE__ */ new Map()), l = /* @__PURE__ */ Nt(/* @__PURE__ */ new Map()), u = (e, n) => JSON.stringify([
		t(),
		e,
		n
	]), d = 0;
	function f(e = !0) {
		e && (d += 1), r.value = !1, s.value = [];
		for (let [e, t] of c) t.pending ? t.error = null : c.delete(e);
	}
	let p = Nn([
		() => e()?.connection,
		t,
		() => e()?.language
	], ([n, o, l], u, d) => {
		if (f(n !== u?.[0] || o !== u?.[1]), a.value = null, i.value = n?.connected ?? !1, !n || !o) return;
		let p = !1, m, h = 0;
		function g(e) {
			try {
				Promise.resolve(e()).catch(() => {});
			} catch {}
		}
		function _(e = !0) {
			h += 1, f(e), m && g(m), m = void 0;
		}
		function v() {
			if (p || !n || !n.connected) return;
			_(!1), i.value = !0, a.value = null;
			let e = h;
			n.subscribeMessage((t) => {
				if (p || e !== h || !i.value) return;
				s.value = t.entities;
				let n = new Set(t.entities.map((e) => e.entity_id));
				for (let e of c.keys()) !n.has(e) && !c.get(e)?.pending && c.delete(e);
				r.value = !0, a.value = null;
			}, {
				type: "sax_power/dashboard/subscribe",
				entry_id: o,
				language: l || "en"
			}, { resubscribe: !1 }).then((t) => {
				p || e !== h ? g(t) : m = t;
			}).catch(() => {
				!p && e === h && (f(), a.value = "loadFailed");
			});
		}
		function y() {
			p || (i.value = !1, _(), a.value = "disconnected");
		}
		n.addEventListener("ready", v), n.addEventListener("disconnected", y), n.addEventListener("reconnect-error", y), n.connected ? v() : a.value = "disconnected", d(() => {
			p = !0, n.removeEventListener("ready", v), n.removeEventListener("disconnected", y), n.removeEventListener("reconnect-error", y), _(e()?.connection !== n || t() !== o);
		});
	}, {
		immediate: !0,
		flush: "sync"
	});
	Te(() => {
		p(), f(), i.value = !1;
	});
	function m(t, r) {
		let a = s.value.find((e) => e.domain === t && e.key === r);
		if (!a) return null;
		let o = e(), d = o?.states[a.entity_id], f = i.value && !!d && d.state !== "unknown" && d.state !== "unavailable", p = l.get(u(t, r)) ?? c.get(a.entity_id);
		return {
			metadata: a,
			state: d,
			available: f,
			name: a.name ?? (typeof d?.attributes.friendly_name == "string" ? d.attributes.friendly_name : a.key),
			displayValue: Ya(o, a, d, n.value, i.value),
			canControl: f && a.can_control && !!o?.callService,
			pending: p?.pending ?? !1,
			error: p?.error ? Ka[n.value][p.error] : null
		};
	}
	async function h(t, n, i) {
		let a = m(t, n);
		if (!a || a.pending) return !1;
		let o = /* @__PURE__ */ Nt({
			pending: !1,
			error: null
		});
		c.set(a.metadata.entity_id, o);
		let s = e();
		if (!a.canControl || !s?.callService || !r.value) return o.error = "forbidden", !1;
		let f = Xa(a, i);
		if (!f) return o.error = "invalid", !1;
		o.pending = !0;
		let p = u(t, n);
		l.set(p, o);
		let h = d, g = () => h === d && c.get(a.metadata.entity_id) === o && m(t, n)?.metadata.entity_id === a.metadata.entity_id;
		try {
			return await s.callService(t, f.service, f.data, { entity_id: a.metadata.entity_id }, !1), g();
		} catch {
			return g() && (o.error = "failed"), !1;
		} finally {
			o.pending = !1, l.get(p) === o && l.delete(p);
		}
	}
	async function g(t, n, i) {
		let a = [`${t}_start`, `${t}_end`], o = a.map((e) => m("time", e));
		if (o.some((e) => e?.pending)) return !1;
		let s = /* @__PURE__ */ Nt({
			pending: !1,
			error: null
		});
		for (let e of o) e && c.set(e.metadata.entity_id, s);
		let f = o[0]?.metadata.device_id, p = e();
		if (!r.value || !p?.callService || !f || o.some((e) => !e?.canControl || e.metadata.device_id !== f)) return s.error = "forbidden", !1;
		let h = Ja(n), g = Ja(i);
		if (!h || !g) return s.error = "invalid", !1;
		let _ = o.map((e) => e.metadata.entity_id), v = a.map((e) => u("time", e));
		s.pending = !0;
		for (let e of v) l.set(e, s);
		let y = d, b = () => y === d && _.every((e, t) => {
			let n = m("time", a[t]);
			return c.get(e) === s && n?.metadata.entity_id === e && n.metadata.device_id === f;
		});
		try {
			return await p.callService("sax_power", `set_${t}_window`, {
				device_id: f,
				start: h,
				end: g
			}, void 0, !1), b();
		} catch {
			return b() && (s.error = "failed"), !1;
		} finally {
			s.pending = !1;
			for (let e of v) l.get(e) === s && l.delete(e);
		}
	}
	return {
		language: n,
		ready: /* @__PURE__ */ Ft(r),
		connected: /* @__PURE__ */ Ft(i),
		error: o,
		entity: m,
		perform: h,
		performTimeWindow: g
	};
}
//#endregion
//#region src/components/EntityControl.vue?vue&type=script&setup=true&lang.ts
var Qa = ["aria-busy"], $a = { class: "entity-control__name" }, eo = [
	"checked",
	"indeterminate",
	"disabled"
], to = { class: "entity-control__description" }, no = { key: 0 }, ro = { class: "entity-control__input" }, io = [
	"checked",
	"disabled",
	"aria-describedby"
], ao = [
	"value",
	"disabled",
	"aria-describedby"
], oo = {
	key: 0,
	value: "",
	disabled: ""
}, so = ["value"], co = [
	"value",
	"type",
	"min",
	"max",
	"step",
	"disabled",
	"aria-describedby"
], lo = ["disabled"], uo = {
	key: 0,
	class: "entity-control__error",
	role: "alert"
}, fo = {
	key: 1,
	role: "status"
}, po = ["aria-labelledby", "aria-describedby"], mo = ["id"], ho = ["id"], go = { class: "entity-control__confirmation-actions" }, _o = ["disabled"], vo = /*@__PURE__*/ V({
	__name: "EntityControl",
	props: {
		domain: { type: String },
		entityKey: { type: String },
		confirmSwitch: { type: Boolean },
		hideConfirmedLabel: { type: Boolean },
		monthTile: { type: Boolean },
		timeUnit: { type: Boolean }
	},
	setup(e) {
		let t = e, n = An(qa), r = $(() => n?.entity(t.domain, t.entityKey)), i = Vn(), a = `sax-control-${i}`, o = `sax-status-${i}`, s = `sax-value-${i}`, c = /* @__PURE__ */ R(""), l = /* @__PURE__ */ R(), u = /* @__PURE__ */ Wt(null), d = $(() => r.value?.state?.state ?? ""), f = $(() => r.value?.state?.attributes ?? {}), p = $(() => {
			let e = f.value.options;
			return Array.isArray(e) ? e.filter((e) => typeof e == "string") : [];
		}), m = $(() => n?.language.value ?? "en"), h = $(() => t.domain === "switch" ? o : `${s} ${o}`), g = $(() => {
			let e = r.value?.displayValue;
			return t.timeUnit && t.domain === "time" && m.value === "de" && r.value?.available && /^(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(d.value) ? `${e} Uhr` : e;
		}), _ = $(() => m.value === "de" ? {
			apply: "Übernehmen",
			confirmed: "Bestätigter Wert",
			disconnected: "Keine Verbindung zu Home Assistant",
			unavailable: "Nicht verfügbar",
			readOnly: "Keine Berechtigung zum Ändern",
			pending: "Änderung wird an Home Assistant gesendet …",
			cancel: "Abbrechen",
			turnOn: "Einschalten",
			turnOff: "Ausschalten",
			confirmationTitle: u.value?.desired ? "Speicher einschalten?" : "Speicher ausschalten?",
			confirmationQuestion: u.value?.desired ? "Möchten Sie den Speicher wirklich einschalten?" : "Möchten Sie den Speicher wirklich ausschalten?"
		} : {
			apply: "Apply",
			confirmed: "Confirmed value",
			disconnected: "Disconnected from Home Assistant",
			unavailable: "Unavailable",
			readOnly: "You do not have permission to change this setting",
			pending: "Sending change to Home Assistant …",
			cancel: "Cancel",
			turnOn: "Turn on",
			turnOff: "Turn off",
			confirmationTitle: u.value?.desired ? "Turn on the battery?" : "Turn off the battery?",
			confirmationQuestion: u.value?.desired ? "Do you really want to turn on the battery?" : "Do you really want to turn off the battery?"
		}), v = $(() => !r.value?.canControl || r.value.pending || t.monthTile && d.value !== "on" && d.value !== "off"), y = $(() => n?.connected.value ? !r.value?.available || t.monthTile && d.value !== "on" && d.value !== "off" ? _.value.unavailable : r.value.metadata.can_control ? r.value.pending ? _.value.pending : "" : _.value.readOnly : _.value.disconnected);
		function b(e) {
			return r.value?.available ? t.domain === "time" ? x(e) : e : "";
		}
		function x(e) {
			return /^(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(e) ? e.slice(0, 5) : "";
		}
		function S(e) {
			let n = e.target;
			c.value = t.domain === "time" ? x(n.value) : n.value, n.value = c.value;
		}
		Nn([() => r.value?.metadata.entity_id, () => d.value], ([, e]) => {
			c.value = b(e);
		}, { immediate: !0 });
		function C(e) {
			let t = f.value[e];
			return typeof t == "number" && Number.isFinite(t) ? t : void 0;
		}
		function w(e) {
			return r.value?.metadata.states[e] ?? e;
		}
		async function ee() {
			v.value || !n || t.domain !== "number" && t.domain !== "time" || await n.perform(t.domain, t.entityKey, t.domain === "time" && c.value ? `${c.value}:00` : c.value);
		}
		function T() {
			u.value = null, l.value?.open && l.value.close();
		}
		function E() {
			l.value?.open || (u.value = null);
		}
		Nn([
			() => r.value?.metadata.entity_id,
			d,
			v,
			() => t.domain,
			() => t.entityKey,
			() => t.confirmSwitch
		], T, { flush: "sync" }), Qn(T);
		async function D() {
			let e = u.value;
			T(), e && !v.value && n && e.entityId === r.value?.metadata.entity_id && e.sourceState === d.value && e.domain === t.domain && e.key === t.entityKey && await n.perform(t.domain, t.entityKey, e.desired);
		}
		async function O(e) {
			let i = e.target, a = i.checked;
			if (i.checked = d.value === "on", !v.value && n) {
				if (t.confirmSwitch && r.value) {
					let e = {
						entityId: r.value.metadata.entity_id,
						domain: t.domain,
						key: t.entityKey,
						sourceState: d.value,
						desired: a
					};
					u.value = e, await mn(), u.value === e && !v.value && l.value?.showModal();
					return;
				}
				await n.perform(t.domain, t.entityKey, a);
			}
		}
		async function k(e) {
			let r = e.target, i = r.value;
			r.value = d.value, !v.value && n && await n.perform(t.domain, t.entityKey, i);
		}
		return (t, n) => r.value ? (K(), q("form", {
			key: 0,
			class: j(["entity-control", {
				"entity-control--month": e.monthTile,
				"entity-control--selected": e.monthTile && r.value.available && d.value === "on"
			}]),
			"aria-busy": r.value.pending,
			onSubmit: Fa(ee, ["prevent"])
		}, [
			e.monthTile && e.domain === "switch" ? (K(), q("label", {
				key: 0,
				for: a,
				class: "entity-control__switch-target entity-control__month-target"
			}, [Y("span", $a, M(r.value.name), 1), Y("input", {
				id: a,
				type: "checkbox",
				role: "switch",
				checked: r.value.available && d.value === "on",
				indeterminate: !r.value.available || d.value !== "on" && d.value !== "off",
				disabled: v.value,
				"aria-describedby": o,
				onChange: O
			}, null, 40, eo)])) : (K(), q(W, { key: 1 }, [Y("div", to, [Y("label", {
				for: a,
				class: "entity-control__name"
			}, M(r.value.name), 1), e.domain === "switch" ? Q("", !0) : (K(), q("p", {
				key: 0,
				id: s,
				class: "entity-control__value"
			}, [e.hideConfirmedLabel ? Q("", !0) : (K(), q("span", no, M(_.value.confirmed) + ":", 1)), Z(" " + M(g.value), 1)]))]), Y("div", ro, [e.domain === "switch" ? (K(), q("label", {
				key: 0,
				for: a,
				class: "entity-control__switch-target"
			}, [Y("input", {
				id: a,
				type: "checkbox",
				role: "switch",
				checked: d.value === "on",
				disabled: v.value,
				"aria-describedby": h.value,
				onChange: O
			}, null, 40, io)])) : e.domain === "select" ? (K(), q("select", {
				key: 1,
				id: a,
				value: r.value.available ? d.value : "",
				disabled: v.value,
				"aria-describedby": h.value,
				onChange: k
			}, [r.value.available ? Q("", !0) : (K(), q("option", oo, M(_.value.unavailable), 1)), (K(!0), q(W, null, H(p.value, (e) => (K(), q("option", {
				key: e,
				value: e
			}, M(w(e)), 9, so))), 128))], 40, ao)) : (K(), q(W, { key: 2 }, [Y("input", {
				id: a,
				value: c.value,
				type: e.domain === "number" ? "number" : "time",
				min: e.domain === "number" ? C("min") : void 0,
				max: e.domain === "number" ? C("max") : void 0,
				step: e.domain === "number" ? C("step") : 60,
				disabled: v.value,
				"aria-describedby": h.value,
				required: "",
				onInput: S
			}, null, 40, co), Y("button", {
				type: "submit",
				disabled: v.value || c.value === ""
			}, M(_.value.apply), 9, lo)], 64))])], 64)),
			Y("div", {
				id: o,
				class: "entity-control__feedback"
			}, [r.value.error ? (K(), q("p", uo, M(r.value.error), 1)) : y.value ? (K(), q("p", fo, M(y.value), 1)) : Q("", !0)]),
			e.confirmSwitch ? (K(), q("dialog", {
				key: 2,
				ref_key: "dialog",
				ref: l,
				class: "entity-control__confirmation",
				"aria-labelledby": `${z(i)}-confirmation-title`,
				"aria-describedby": `${z(i)}-confirmation-question`,
				onCancel: Fa(T, ["prevent"]),
				onClose: E
			}, [
				Y("h3", { id: `${z(i)}-confirmation-title` }, M(_.value.confirmationTitle), 9, mo),
				Y("p", { id: `${z(i)}-confirmation-question` }, M(_.value.confirmationQuestion), 9, ho),
				Y("div", go, [Y("button", {
					type: "button",
					autofocus: "",
					onClick: T
				}, M(_.value.cancel), 1), Y("button", {
					type: "button",
					disabled: v.value || !u.value,
					onClick: D
				}, M(u.value?.desired ? _.value.turnOn : _.value.turnOff), 9, _o)])
			], 40, po)) : Q("", !0)
		], 42, Qa)) : Q("", !0);
	}
}), yo = ".entity-control{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));color:var(--primary-text-color,#212121);box-shadow:var(--ha-card-box-shadow,none);flex-wrap:wrap;align-items:center;gap:12px 24px;padding:20px;display:flex}.entity-control__description{overflow-wrap:anywhere;flex:200px;min-width:0}.entity-control__name{font-weight:500;line-height:1.5;display:block}.entity-control__value{color:var(--secondary-text-color,#666);margin:4px 0 0;font-size:.9em;line-height:1.5}.entity-control__input{flex-wrap:wrap;align-items:center;gap:8px;max-width:100%;display:flex}.entity-control__switch-target{cursor:pointer;justify-content:center;align-items:center;min-width:44px;min-height:44px;display:flex}.entity-control__switch-target:has(:disabled){cursor:not-allowed}.entity-control input,.entity-control select,.entity-control button{border:1px solid var(--divider-color,#767676);max-width:100%;min-height:44px;color:inherit;background:var(--card-background-color,#fff);font:inherit;border-radius:6px;padding:8px 12px}.entity-control input[type=number]{width:120px}.entity-control input[type=checkbox]{width:22px;height:22px;min-height:22px;accent-color:var(--primary-color,#03a9f4);cursor:pointer;flex-shrink:0;margin:0;padding:0}.entity-control button{border-color:var(--primary-color,#03a9f4);color:var(--primary-text-color,#212121);cursor:pointer}.entity-control :disabled{cursor:not-allowed;opacity:.6}.entity-control input:focus-visible,.entity-control select:focus-visible,.entity-control button:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.entity-control__feedback{color:var(--secondary-text-color,#666);flex-basis:100%;line-height:1.5}.entity-control__feedback:empty{display:none}.entity-control__feedback p{margin:0}.entity-control__error{color:var(--error-color,#b71c1c)}.entity-control__confirmation{border:1px solid var(--divider-color,#767676);background:var(--card-background-color,#fff);width:min(440px,100vw - 32px);max-height:calc(100vh - 32px);color:var(--primary-text-color,#212121);border-radius:12px;padding:24px;overflow:auto}.entity-control__confirmation::backdrop{background:#0000008c}.entity-control__confirmation h3{margin:0;font-size:20px;line-height:1.4}.entity-control__confirmation p{margin:16px 0 24px;line-height:1.6}.entity-control__confirmation-actions{flex-wrap:wrap;justify-content:flex-end;gap:12px;display:flex}@container sax-content (width>=860px){.entity-control{gap:8px 12px;padding:14px}.entity-control__description{flex-basis:140px}.entity-control__value{margin-top:2px;font-size:14px}.entity-control input[type=number]{width:104px}}", bo = (e, t) => {
	let n = e.__vccOpts || e;
	for (let [e, r] of t) n[e] = r;
	return n;
}, xo = /*#__PURE__*/ bo(vo, [["styles", [yo]]]), So = [
	"role",
	"aria-labelledby",
	"aria-valuemin",
	"aria-valuemax",
	"aria-valuenow",
	"aria-valuetext"
], Co = {
	viewBox: "0 0 240 124",
	"aria-hidden": "true"
}, wo = ["stroke-dasharray", "stroke-dashoffset"], To = ["transform"], Eo = {
	class: "entity-gauge__scale",
	"aria-hidden": "true"
}, Do = { class: "entity-gauge__value" }, Oo = {
	key: 0,
	class: "entity-gauge__range"
}, ko = /*#__PURE__*/ bo(/* @__PURE__ */ V({
	__name: "EntityGauge",
	props: {
		entityKey: { type: String },
		maximum: { type: Number },
		segments: { type: Array }
	},
	setup(e) {
		let t = e, n = An(qa), r = $(() => n?.entity("sensor", t.entityKey)), i = `sax-gauge-${Vn()}`, a = $(() => {
			let e = r.value?.state?.state.trim();
			if (!r.value?.available || !e) return null;
			let t = Number(e);
			return Number.isFinite(t) ? t : null;
		}), o = $(() => a.value === null ? null : Math.max(0, Math.min(t.maximum, a.value))), s = $(() => a.value === null ? null : [...t.segments].reverse().find((e) => a.value >= e.from)?.label ?? t.segments[0]?.label), c = $(() => r.value?.available && a.value === null ? n?.language.value === "de" ? "Unbekannt" : "Unknown" : r.value?.displayValue), l = $(() => t.segments.map((e, n) => ({
			...e,
			offset: -(e.from / t.maximum) * 100,
			length: ((t.segments[n + 1]?.from ?? t.maximum) - e.from) / t.maximum * 100
		})));
		return (t, n) => r.value ? (K(), q("section", {
			key: 0,
			class: "entity-gauge",
			"aria-labelledby": i
		}, [Y("h2", { id: i }, M(r.value.name), 1), Y("div", {
			class: "entity-gauge__meter",
			role: o.value === null ? void 0 : "meter",
			"aria-labelledby": o.value === null ? void 0 : i,
			"aria-valuemin": o.value === null ? void 0 : 0,
			"aria-valuemax": o.value === null ? void 0 : e.maximum,
			"aria-valuenow": o.value ?? void 0,
			"aria-valuetext": o.value === null ? void 0 : `${c.value} · ${s.value}`
		}, [
			(K(), q("svg", Co, [n[1] ||= Y("path", {
				class: "entity-gauge__track",
				d: "M20 110 A100 100 0 0 1 220 110"
			}, null, -1), o.value === null ? Q("", !0) : (K(), q(W, { key: 0 }, [
				(K(!0), q(W, null, H(l.value, (e) => (K(), q("path", {
					key: e.from,
					class: j(["entity-gauge__segment", `entity-gauge__segment--${e.color}`]),
					d: "M20 110 A100 100 0 0 1 220 110",
					pathLength: "100",
					"stroke-dasharray": `${e.length} 100`,
					"stroke-dashoffset": e.offset
				}, null, 10, wo))), 128)),
				Y("line", {
					class: "entity-gauge__needle",
					x1: "120",
					y1: "110",
					x2: "120",
					y2: "33",
					transform: `rotate(${o.value / e.maximum * 180 - 90} 120 110)`
				}, null, 8, To),
				n[0] ||= Y("circle", {
					class: "entity-gauge__pivot",
					cx: "120",
					cy: "110",
					r: "5"
				}, null, -1)
			], 64))])),
			Y("div", Eo, [n[2] ||= Y("span", null, "0", -1), Y("span", null, M(e.maximum), 1)]),
			Y("p", Do, M(c.value), 1),
			s.value ? (K(), q("p", Oo, M(s.value), 1)) : Q("", !0)
		], 8, So)])) : Q("", !0);
	}
}), [["styles", [".entity-gauge{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);text-align:center;padding:24px}.entity-gauge h2{overflow-wrap:anywhere;margin:0 0 20px;font-size:16px;font-weight:500;line-height:1.5}.entity-gauge__meter{max-width:260px;margin:0 auto}.entity-gauge svg{fill:none;width:100%;display:block}.entity-gauge__track,.entity-gauge__segment{stroke-width:15px;stroke-linecap:butt}.entity-gauge__track{stroke:var(--divider-color,#e0e0e0)}.entity-gauge__segment--red{stroke:var(--error-color,#db4437)}.entity-gauge__segment--yellow{stroke:var(--warning-color,#f4b400)}.entity-gauge__segment--green{stroke:var(--success-color,#0f9d58)}.entity-gauge__needle{stroke:var(--primary-text-color,#212121);stroke-width:3px;stroke-linecap:round}.entity-gauge__pivot{stroke:none;fill:var(--primary-text-color,#212121)}.entity-gauge__scale{color:var(--secondary-text-color,#666);justify-content:space-between;padding:2px 7px;font-size:12px;display:flex}.entity-gauge__value{overflow-wrap:anywhere;margin:10px 0 0;font-size:28px;font-weight:500;line-height:1.4}.entity-gauge__range{color:var(--secondary-text-color,#666);margin:4px 0 0;font-size:14px;line-height:1.5}@container sax-content (width>=860px){.entity-gauge{padding:16px}.entity-gauge h2{margin-bottom:8px}.entity-gauge__meter{max-width:180px}.entity-gauge__value{margin-top:6px;font-size:24px}.entity-gauge__range{margin-top:2px}}"]]]), Ao = {
	key: 0,
	class: "entity-value"
}, jo = { class: "entity-value__name" }, Mo = { class: "entity-value__state" }, No = /*#__PURE__*/ bo(/* @__PURE__ */ V({
	__name: "EntityValue",
	props: {
		domain: { type: null },
		entityKey: { type: String }
	},
	setup(e) {
		let t = e, n = An(qa), r = $(() => n?.entity(t.domain, t.entityKey));
		return (e, t) => r.value ? (K(), q("div", Ao, [Y("span", jo, M(r.value.name), 1), Y("span", Mo, M(r.value.displayValue), 1)])) : Q("", !0);
	}
}), [["styles", [".entity-value{color:var(--primary-text-color,#212121);overflow-wrap:anywhere;flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:8px 20px;line-height:1.5;display:flex}.entity-value__name{color:var(--secondary-text-color,#666)}.entity-value__state{font-weight:500}"]]]), Po = { class: "general-view" }, Fo = {
	key: 0,
	class: "general-view__status",
	role: "status"
}, Io = {
	key: 1,
	class: "general-view__status",
	role: "status"
}, Lo = {
	key: 2,
	class: "general-view__gauges"
}, Ro = ["aria-labelledby"], zo = ["id"], Bo = { class: "general-view__rows" }, Vo = /*#__PURE__*/ bo(/* @__PURE__ */ V({
	__name: "GeneralView",
	setup(e) {
		let t = An(qa), n = Vn(), r = $(() => t?.language.value === "de" ? {
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
		}], a = $(() => i.map((e) => ({
			...e,
			entities: e.entities.filter(([e, n]) => t?.entity(e, n))
		})).filter((e) => e.entities.length)), o = $(() => !!(t?.entity("sensor", "soc") || t?.entity("sensor", "storage_max_cell_temp"))), s = $(() => o.value || a.value.length > 0);
		return (e, i) => (K(), q("div", Po, [
			!z(t)?.ready.value && !z(t)?.error.value ? (K(), q("p", Fo, M(r.value.loading), 1)) : z(t)?.ready.value && !s.value ? (K(), q("p", Io, M(r.value.empty), 1)) : Q("", !0),
			o.value ? (K(), q("div", Lo, [X(ko, {
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
			}, null, 8, ["segments"]), X(ko, {
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
			}, null, 8, ["segments"])])) : Q("", !0),
			(K(!0), q(W, null, H(a.value, (e) => (K(), q("section", {
				key: e.title,
				class: j(["general-view__card", `general-view__card--${e.title}`]),
				"aria-labelledby": `${z(n)}-${e.title}`
			}, [Y("h2", { id: `${z(n)}-${e.title}` }, M(r.value[e.title]), 9, zo), Y("div", Bo, [(K(!0), q(W, null, H(e.entities, ([e, t]) => (K(), q(W, { key: `${e}.${t}` }, [e === "number" || e === "switch" ? (K(), J(xo, {
				key: 0,
				domain: e,
				"entity-key": t,
				"confirm-switch": e === "switch" && t === "storage_switch"
			}, null, 8, [
				"domain",
				"entity-key",
				"confirm-switch"
			])) : (K(), J(No, {
				key: 1,
				domain: e,
				"entity-key": t
			}, null, 8, ["domain", "entity-key"]))], 64))), 128))])], 10, Ro))), 128))
		]));
	}
}), [["styles", [".general-view{gap:20px;min-width:0;margin-top:24px;display:grid}.general-view__gauges{grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr));gap:20px;display:grid}.general-view__card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.general-view__card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.general-view__rows{gap:16px;display:grid}.general-view__rows .entity-control{border:0;border-bottom:1px solid var(--divider-color,#e0e0e0);box-shadow:none;border-radius:0;padding:0 0 16px}.general-view__rows .entity-control:last-child{border-bottom:0;padding-bottom:0}.general-view__status{color:var(--secondary-text-color,#666);margin:0;line-height:1.6}@container sax-content (width>=860px){.general-view{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;gap:16px;margin-top:16px}.general-view__gauges{grid-column:1;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.general-view__gauges:has(>:only-child){grid-template-columns:minmax(0,1fr)}.general-view__card{padding:18px}.general-view__card--power{grid-column:1}.general-view__card--device{grid-area:1/2/span 2}:is(.general-view:not(:has(.general-view__gauges)) .general-view__card--device,.general-view:not(:has(.general-view__card--power)) .general-view__card--device){grid-row:1}:is(.general-view:has(>:only-child),.general-view:not(:has(.general-view__card--device))){grid-template-columns:minmax(0,1fr)}.general-view__card:only-child{grid-area:auto}.general-view__card h2{margin-bottom:12px;font-size:16px}.general-view__rows{gap:10px}.general-view__rows .entity-control{padding:0 0 10px}.general-view__rows .entity-control:last-child{padding-bottom:0}.general-view__status{grid-column:1/-1}}@media (max-width:600px){.general-view,.general-view__gauges{gap:16px}.general-view__card{padding:20px}}"]]]), Ho = ["aria-busy"], Uo = { class: "month-selection__header" }, Wo = {
	class: "month-selection__overview",
	"aria-live": "polite",
	"aria-atomic": "true"
}, Go = { class: "month-selection__summary" }, Ko = { class: "month-selection__count" }, qo = ["aria-expanded"], Jo = { class: "month-selection__feedback" }, Yo = {
	key: 0,
	role: "status"
}, Xo = {
	key: 1,
	role: "status"
}, Zo = {
	key: 2,
	role: "status"
}, Qo = {
	key: 3,
	role: "status"
}, $o = { class: "month-selection__hint" }, es = { class: "month-selection__quarters" }, ts = { class: "month-selection__options" }, ns = {
	key: 1,
	class: "month-selection__missing"
}, rs = { class: "month-selection__missing-target" }, is = ["aria-describedby"], as = ["id"], os = /*#__PURE__*/ bo(/* @__PURE__ */ V({
	__name: "MonthSelection",
	props: { entityKeys: { type: Array } },
	setup(e) {
		let t = e, n = An(qa), r = /* @__PURE__ */ R(!1), i = `sax-months-${Vn()}`, a = $(() => n?.language.value ?? "en"), o = $(() => a.value === "de" ? {
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
		}), s = $(() => {
			let e = new Intl.DateTimeFormat(a.value, {
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
		}), c = $(() => Array.from({ length: 4 }, (e, t) => ({
			index: t,
			name: a.value === "de" ? `${t + 1}. Quartal` : `Q${t + 1}`,
			months: s.value.slice(t * 3, t * 3 + 3)
		}))), l = $(() => s.value.filter((e) => e.selected).length), u = $(() => s.value.filter((e) => !e.known)), d = $(() => {
			if (l.value === 12) return o.value.allYear;
			if (!l.value) return u.value.length ? o.value.incomplete : o.value.none;
			let e = [], t, n;
			function r() {
				t && n && e.push(t.index === n.index ? t.name : `${t.name}–${n.name}`), t = void 0, n = void 0;
			}
			for (let e of s.value) e.selected ? (t ??= e, n = e) : r();
			return r(), e.join(", ");
		}), f = $(() => {
			let e = l.value, t = u.value.length;
			return t ? a.value === "de" ? `${e} ausgewählt · ${t} unklar` : `${e} selected · ${t} unknown` : a.value === "de" ? `${e} von 12 Monaten ausgewählt` : `${e} of 12 months selected`;
		}), p = $(() => s.value.some((e) => e.entity?.pending)), m = $(() => s.value.flatMap((e) => e.entity?.error ? [`${e.name}: ${e.entity.error}`] : [])), h = $(() => s.value.filter((e) => e.known && !e.entity?.metadata.can_control));
		return (e, t) => (K(), q("div", {
			class: "month-selection",
			"aria-busy": p.value
		}, [
			Y("div", Uo, [Y("div", Wo, [Y("p", Go, M(d.value), 1), Y("p", Ko, M(f.value), 1)]), Y("button", {
				type: "button",
				class: "month-selection__toggle",
				"aria-expanded": r.value,
				"aria-controls": i,
				onClick: t[0] ||= (e) => r.value = !r.value
			}, [Z(M(r.value ? o.value.close : o.value.edit) + " ", 1), (K(), q("svg", {
				viewBox: "0 0 24 24",
				width: "18",
				height: "18",
				"aria-hidden": "true",
				class: j({ "month-selection__chevron--expanded": r.value })
			}, [...t[1] ||= [Y("path", { d: "m6 9 6 6 6-6" }, null, -1)]], 2))], 8, qo)]),
			Y("div", Jo, [
				r.value ? Q("", !0) : (K(), q(W, { key: 0 }, [(K(!0), q(W, null, H(m.value, (e) => (K(), q("p", {
					key: e,
					class: "month-selection__error",
					role: "alert"
				}, M(e), 1))), 128)), p.value ? (K(), q("p", Yo, M(o.value.pending), 1)) : Q("", !0)], 64)),
				z(n)?.connected.value ? Q("", !0) : (K(), q("p", Xo, M(o.value.disconnected), 1)),
				u.value.length ? (K(), q("p", Zo, M(o.value.unknown) + ": " + M(u.value.map((e) => e.name).join(", ")), 1)) : Q("", !0),
				h.value.length ? (K(), q("p", Qo, M(o.value.readOnly) + ": " + M(h.value.map((e) => e.name).join(", ")), 1)) : Q("", !0)
			]),
			Dn(Y("div", {
				id: i,
				class: "month-selection__details"
			}, [Y("p", $o, M(o.value.hint), 1), Y("div", es, [(K(!0), q(W, null, H(c.value, (e) => (K(), q("fieldset", {
				key: e.index,
				class: "month-selection__quarter"
			}, [Y("legend", null, M(e.name), 1), Y("div", ts, [(K(!0), q(W, null, H(e.months, (e) => (K(), q(W, { key: e.index }, [e.entity && e.key ? (K(), J(xo, {
				key: 0,
				domain: "switch",
				"entity-key": e.key,
				"month-tile": ""
			}, null, 8, ["entity-key"])) : (K(), q("div", ns, [Y("label", rs, [Y("span", null, M(e.name), 1), Y("input", {
				type: "checkbox",
				role: "switch",
				disabled: "",
				indeterminate: !0,
				"aria-describedby": `${i}-${e.index}-missing`
			}, null, 8, is)]), Y("p", { id: `${i}-${e.index}-missing` }, M(o.value.unavailable), 9, as)]))], 64))), 128))])]))), 128))])], 512), [[Ki, r.value]])
		], 8, Ho));
	}
}), [["styles", [".month-selection{min-width:0}.month-selection__header{flex-wrap:wrap;justify-content:space-between;align-items:center;gap:16px;display:flex}.month-selection__overview{overflow-wrap:anywhere;flex:180px;min-width:0}.month-selection__summary{margin:0;font-size:16px;font-weight:500;line-height:1.5}.month-selection__count,.month-selection__hint{color:var(--secondary-text-color,#666);margin:4px 0 0;font-size:14px;line-height:1.5}.month-selection__toggle{border:1px solid var(--divider-color,#e0e0e0);background:var(--card-background-color,#fff);min-height:44px;color:var(--primary-text-color,#212121);font:inherit;cursor:pointer;border-radius:8px;flex-shrink:0;justify-content:center;align-items:center;gap:8px;padding:8px 12px;font-size:14px;display:inline-flex}.month-selection__toggle:hover{background:var(--secondary-background-color,#f5f5f5)}:is(.month-selection__toggle:focus-visible,.month-selection .entity-control__month-target:has(input:focus-visible)){outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.month-selection__toggle svg{fill:none;stroke:currentColor;stroke-width:2px;stroke-linecap:round;stroke-linejoin:round}.month-selection__chevron--expanded{transform:rotate(180deg)}.month-selection__details{border-top:1px solid var(--divider-color,#e0e0e0);margin-top:16px;padding-top:16px}.month-selection__hint{margin:0 0 16px}.month-selection__quarters{grid-template-columns:minmax(0,1fr);gap:16px;display:grid}.month-selection__quarter{border:0;min-width:0;margin:0;padding:0}.month-selection__quarter legend{color:var(--secondary-text-color,#666);margin-bottom:8px;padding:0;font-size:13px;font-weight:500}.month-selection__options{grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;display:grid}.month-selection .entity-control.entity-control--month,.month-selection__missing{border:1px solid var(--divider-color,#e0e0e0);background:var(--card-background-color,#fff);border-radius:8px;flex-flow:column;align-items:stretch;gap:0;min-width:0;padding:0;display:flex}.month-selection .entity-control.entity-control--selected{border-color:color-mix(in srgb, var(--primary-color,#03a9f4) 55%, var(--divider-color,#e0e0e0));background:color-mix(in srgb, var(--primary-color,#03a9f4) 12%, var(--card-background-color,#fff))}.month-selection .entity-control__month-target,.month-selection__missing-target{cursor:pointer;border-radius:7px;flex-direction:column-reverse;flex:auto;justify-content:center;align-items:center;gap:8px;min-height:44px;padding:10px 6px;display:flex}.month-selection__missing-target{cursor:not-allowed}.month-selection .entity-control__month-target:has(:disabled){cursor:not-allowed}.month-selection .entity-control__name,.month-selection__missing-target span{text-align:center;overflow-wrap:anywhere;min-width:0;max-width:100%;font-size:14px;font-weight:500;line-height:1.4}.month-selection__missing input[type=checkbox]{width:22px;height:22px;min-height:22px;accent-color:var(--primary-color,#03a9f4);flex-shrink:0;margin:0;padding:0}.month-selection .entity-control__feedback,.month-selection__missing p{overflow-wrap:anywhere;min-width:0;color:var(--secondary-text-color,#666);flex:none;margin:0;padding:0 12px 10px;font-size:13px;line-height:1.5}.month-selection__feedback{color:var(--secondary-text-color,#666);overflow-wrap:anywhere;gap:8px;margin-top:12px;font-size:14px;line-height:1.5;display:grid}.month-selection__feedback:empty{display:none}.month-selection__feedback p{margin:0}.month-selection__error{color:var(--error-color,#b71c1c)}@container sax-content (width>=600px){.month-selection__quarters{grid-template-columns:repeat(2,minmax(0,1fr))}}"]]]), ss = ["aria-busy"], cs = { class: "time-window-control__inputs" }, ls = ["for"], us = [
	"id",
	"value",
	"disabled",
	"aria-describedby",
	"onInput"
], ds = ["disabled"], fs = ["id"], ps = ["aria-label"], ms = [
	"disabled",
	"aria-label",
	"aria-valuenow",
	"aria-valuetext",
	"aria-describedby",
	"onKeydown",
	"onPointerdown"
], hs = {
	class: "time-window-control__marker-label",
	"aria-hidden": "true"
}, gs = { class: "time-window-control__duration" }, _s = ["id"], vs = ["id"], ys = {
	key: 0,
	class: "time-window-control__error",
	role: "alert"
}, bs = {
	key: 1,
	role: "status"
}, xs = /*#__PURE__*/ bo(/* @__PURE__ */ V({
	__name: "TimeWindowControl",
	props: { kind: { type: String } },
	setup(e) {
		let t = e, n = An(qa), r = $(() => n?.entity("time", `${t.kind}_start`)), i = $(() => n?.entity("time", `${t.kind}_end`)), a = `sax-window-${Vn()}`, o = $(() => n?.language.value ?? "en"), s = $(() => o.value === "de" ? {
			start: "Start",
			end: "Ende",
			unit: "Uhr",
			apply: "Übernehmen",
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
			invalid: "Bitte gültige Start- und Endzeiten eingeben.",
			help: "Marken ziehen oder Uhrzeit eingeben. Pfeiltasten ändern um eine Minute, Bild auf und Bild ab um 15 Minuten. Pos1 und Ende wählen Tagesanfang und Tagesende.",
			startMarker: "Startmarke",
			endMarker: "Endmarke",
			timeline: "Zeitfenster auf einer 24-Stunden-Leiste"
		} : {
			start: "Start",
			end: "End",
			unit: "",
			apply: "Apply",
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
			invalid: "Please enter valid start and end times.",
			help: "Drag the markers or enter a time. Arrow keys change by one minute; Page Up and Page Down by 15 minutes. Home and End select the beginning and end of the day.",
			startMarker: "Start marker",
			endMarker: "End marker",
			timeline: "Time window on a 24-hour timeline"
		}), c = /* @__PURE__ */ R(""), l = /* @__PURE__ */ R(""), u = /* @__PURE__ */ R(!1), d = /* @__PURE__ */ R(), f = /* @__PURE__ */ R(!1), p = /* @__PURE__ */ R(!1), m = /* @__PURE__ */ R(!1), h = 0, g = null;
		function _(e) {
			if (!/^(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(e)) return null;
			let [t, n, r = 0] = e.split(":").map(Number);
			return t * 3600 + n * 60 + r;
		}
		function v(e) {
			let t = (e) => String(e).padStart(2, "0");
			return `${t(Math.floor(e / 3600))}:${t(Math.floor(e / 60) % 60)}:${t(e % 60)}`;
		}
		function y(e) {
			let t = _(e);
			if (t === null) return "—";
			let n = v(t);
			return t % 60 ? n : n.slice(0, 5);
		}
		function b(e) {
			return _(e) === null ? "" : e.slice(0, 5);
		}
		let x = $(() => r.value?.state?.state ?? ""), S = $(() => i.value?.state?.state ?? ""), C = $(() => !!r.value?.available && !!i.value?.available && _(x.value) !== null && _(S.value) !== null), w = $(() => typeof r.value?.metadata.device_id == "string" && r.value.metadata.device_id.length > 0 && r.value.metadata.device_id === i.value?.metadata.device_id), ee = $(() => C.value ? `${y(x.value)} – ${y(S.value)}${s.value.unit ? ` ${s.value.unit}` : ""}` : [r.value, i.value].map((e) => e?.available && _(e.state?.state ?? "") !== null ? `${y(e.state.state)}${s.value.unit ? ` ${s.value.unit}` : ""}` : s.value.missingValue).join(" – ")), T = $(() => _(c.value) !== null && _(l.value) !== null), E = $(() => u.value && (_(c.value) !== _(x.value) || _(l.value) !== _(S.value))), D = $(() => f.value || !!r.value?.pending || !!i.value?.pending), O = $(() => !n?.ready.value || !n.connected.value || !C.value || !w.value || !r.value?.canControl || !i.value?.canControl || D.value), k = $(() => r.value?.error || i.value?.error), te = $(() => n?.connected.value ? C.value ? w.value ? !r.value?.canControl || !i.value?.canControl ? s.value.readOnly : D.value ? s.value.pending : p.value ? s.value.awaiting : m.value ? s.value.changed : T.value ? "" : s.value.invalid : s.value.incompatible : s.value.unavailable : s.value.disconnected), ne = $(() => u.value || !C.value ? c.value : x.value), A = $(() => u.value || !C.value ? l.value : S.value), re = $(() => {
			let e = _(ne.value), t = _(A.value);
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
		}), ie = $(() => {
			let e = _(ne.value), t = _(A.value);
			return e === null || t === null || e === t ? [] : (t > e ? [[e, t]] : [[e, 86400], [0, t]]).filter(([e, t]) => e !== t).map(([e, t]) => ({
				left: `${e / 864}%`,
				width: `${(t - e) / 864}%`
			}));
		}), ae = $(() => [{
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
			let e = g;
			g = null, e?.target.hasPointerCapture?.(e.pointerId) && e.target.releasePointerCapture(e.pointerId);
		}
		Nn([
			() => r.value?.metadata.entity_id,
			() => i.value?.metadata.entity_id,
			x,
			S,
			C,
			w,
			() => r.value?.metadata.device_id,
			() => i.value?.metadata.device_id,
			() => t.kind
		], (e, t) => {
			let n = typeof t?.[2] == "string" ? t[2] : "", r = typeof t?.[3] == "string" ? t[3] : "", i = u.value && (_(c.value) !== _(n) || _(l.value) !== _(r)), a = D.value || p.value;
			h += 1, oe(), f.value = !1, p.value = !1, u.value = !1, m.value = !!t?.length && i && !a && C.value, c.value = C.value ? b(x.value) : "", l.value = C.value ? b(S.value) : "";
		}, {
			immediate: !0,
			flush: "sync"
		}), Nn(O, (e) => {
			e && oe();
		}, { flush: "sync" }), Qn(oe);
		function se(e, t) {
			O.value || (e === "start" ? c.value = b(t) : l.value = b(t), u.value = !0, p.value = !1, m.value = !1);
		}
		function ce(e, t) {
			let n = t.target;
			se(e, n.value), n.value = e === "start" ? c.value : l.value;
		}
		function ue(e, t) {
			if (O.value) return;
			let n = _(e === "start" ? c.value : l.value);
			if (n === null) return;
			let r = {
				ArrowRight: 60,
				ArrowUp: 60,
				ArrowLeft: -60,
				ArrowDown: -60,
				PageUp: 900,
				PageDown: -900
			};
			(t.key in r || t.key === "Home" || t.key === "End") && (t.preventDefault(), se(e, v(t.key === "Home" ? 0 : t.key === "End" ? 86340 : Math.max(0, Math.min(86340, Math.floor(n / 60) * 60 + r[t.key])))));
		}
		function de(e) {
			if (!g || g.pointerId !== e.pointerId || O.value || !d.value) return;
			let t = d.value.getBoundingClientRect();
			if (t.width <= 0 || !g.moved && e.clientX === g.originX) return;
			let n = Math.max(0, Math.min(1439, Math.round(g.originSeconds / 60 + (e.clientX - g.originX) / t.width * 1440)));
			g.moved = !0, se(g.boundary, v(n * 60));
		}
		function fe(e, t) {
			if (O.value || !T.value || t.button !== 0 || t.isPrimary === !1) return;
			let n = t.currentTarget;
			n.focus(), g = {
				boundary: e,
				pointerId: t.pointerId,
				target: n,
				moved: !1,
				originX: t.clientX,
				originSeconds: _(e === "start" ? c.value : l.value)
			}, n.setPointerCapture?.(t.pointerId), t.preventDefault();
		}
		function pe(e) {
			g?.pointerId === e.pointerId && (g.moved && de(e), oe());
		}
		async function me() {
			if (!n || O.value || !T.value || !E.value) return;
			let e = h;
			f.value = !0, m.value = !1;
			let r = await n.performTimeWindow(t.kind, `${c.value}:00`, `${l.value}:00`);
			e === h && (f.value = !1, p.value = r && E.value);
		}
		return (e, t) => r.value || i.value ? (K(), q("form", {
			key: 0,
			class: "time-window-control",
			"aria-busy": D.value,
			onSubmit: Fa(me, ["prevent"])
		}, [
			Y("div", cs, [(K(!0), q(W, null, H(ae.value, (e) => (K(), q("label", {
				key: e.key,
				for: `${a}-${e.key}`,
				class: "time-window-control__field"
			}, [Y("span", null, [Z(M(e.name), 1), s.value.unit ? (K(), q(W, { key: 0 }, [Z(" (" + M(s.value.unit) + ")", 1)], 64)) : Q("", !0)]), Y("input", {
				id: `${a}-${e.key}`,
				type: "time",
				step: "60",
				required: "",
				value: e.value,
				disabled: O.value,
				"aria-describedby": `${a}-confirmed ${a}-status`,
				onInput: (t) => ce(e.key, t)
			}, null, 40, us)], 8, ls))), 128)), Y("button", {
				class: "time-window-control__apply",
				type: "submit",
				disabled: O.value || !T.value || !E.value
			}, M(s.value.apply), 9, ds)]),
			Y("p", {
				id: `${a}-confirmed`,
				class: "time-window-control__confirmed"
			}, M(s.value.confirmed) + ": " + M(ee.value), 9, fs),
			Y("div", {
				class: "time-window-control__timeline",
				"aria-label": s.value.timeline,
				role: "group"
			}, [Y("div", {
				ref_key: "rail",
				ref: d,
				class: j(["time-window-control__rail", { "time-window-control__rail--draft": E.value }])
			}, [(K(!0), q(W, null, H(ie.value, (e, t) => (K(), q("span", {
				key: t,
				class: "time-window-control__segment",
				style: le(e)
			}, null, 4))), 128))], 2), (K(!0), q(W, null, H(ae.value, (e) => (K(), q("button", {
				key: e.key,
				type: "button",
				role: "slider",
				class: j(["time-window-control__handle", `time-window-control__handle--${e.key}`]),
				style: le({ left: `${(_(e.value) ?? 0) / 864}%` }),
				disabled: O.value || !T.value,
				"aria-label": e.marker,
				"aria-valuemin": "0",
				"aria-valuemax": "86340",
				"aria-valuenow": _(e.value) ?? 0,
				"aria-valuetext": `${y(e.value)}${s.value.unit ? ` ${s.value.unit}` : ""}`,
				"aria-describedby": `${a}-help ${a}-confirmed`,
				"aria-orientation": "horizontal",
				onKeydown: (t) => ue(e.key, t),
				onPointerdown: (t) => fe(e.key, t),
				onPointermove: de,
				onPointerup: pe,
				onPointercancel: oe,
				onLostpointercapture: oe
			}, [Y("span", hs, M(e.shortName), 1), t[0] ||= Y("span", {
				class: "time-window-control__marker-dot",
				"aria-hidden": "true"
			}, null, -1)], 46, ms))), 128))], 8, ps),
			t[1] ||= Y("div", {
				class: "time-window-control__ticks",
				"aria-hidden": "true"
			}, [
				Y("span", null, "00"),
				Y("span", null, "06"),
				Y("span", null, "12"),
				Y("span", null, "18"),
				Y("span", null, "24")
			], -1),
			Y("p", gs, [Y("span", null, M(E.value ? s.value.draft : s.value.duration) + ":", 1), Z(" " + M(re.value), 1)]),
			Y("p", {
				id: `${a}-help`,
				class: "time-window-control__sr-only"
			}, M(s.value.help), 9, _s),
			Y("div", {
				id: `${a}-status`,
				class: "time-window-control__feedback"
			}, [k.value ? (K(), q("p", ys, M(k.value), 1)) : te.value ? (K(), q("p", bs, M(te.value), 1)) : Q("", !0)], 8, vs)
		], 40, ss)) : Q("", !0);
	}
}), [["styles", [".time-window-control{min-width:0;color:var(--primary-text-color,#212121)}.time-window-control__inputs{flex-wrap:wrap;align-items:end;gap:10px;display:flex}.time-window-control__field{flex:136px;gap:5px;min-width:0;font-size:14px;display:grid}.time-window-control__field input,.time-window-control__apply{box-sizing:border-box;border:1px solid var(--divider-color,#767676);min-width:0;max-width:100%;min-height:44px;color:inherit;background:var(--card-background-color,#fff);font:inherit;border-radius:6px;padding:8px 10px;font-size:16px}.time-window-control__field input{width:100%}.time-window-control__apply{border-color:var(--primary-color,#03a9f4);cursor:pointer;flex:none}.time-window-control__confirmed,.time-window-control__duration{color:var(--secondary-text-color,#666);overflow-wrap:anywhere;margin:9px 0 0;font-size:14px;line-height:1.5}.time-window-control__timeline{height:94px;margin:6px 22px 0;position:relative}.time-window-control__rail{background:var(--divider-color,#ddd);border-radius:3px;height:6px;position:absolute;top:44px;left:0;right:0;overflow:hidden}.time-window-control__segment{background:var(--primary-color,#03a9f4);height:100%;position:absolute}.time-window-control__rail--draft .time-window-control__segment{background-image:repeating-linear-gradient(135deg,#0000 0 5px,#ffffff3d 5px 8px)}.time-window-control__handle{width:44px;height:44px;min-height:0;color:inherit;font:inherit;cursor:ew-resize;touch-action:none;background:0 0;border:0;border-radius:6px;padding:0;display:block;position:absolute;transform:translate(-50%)}.time-window-control__handle--start{top:0}.time-window-control__handle--end{top:50px}.time-window-control__marker-label{white-space:nowrap;width:max-content;font-size:12px;line-height:16px;position:absolute;left:50%;transform:translate(-50%)}.time-window-control__handle--start .time-window-control__marker-label{top:0}.time-window-control__handle--end .time-window-control__marker-label{bottom:0}.time-window-control__marker-dot{box-sizing:border-box;border:2px solid var(--primary-color,#03a9f4);background:var(--card-background-color,#fff);border-radius:50%;width:18px;height:18px;position:absolute;left:13px}.time-window-control__handle--start .time-window-control__marker-dot{bottom:3px}.time-window-control__handle--end .time-window-control__marker-dot{top:3px}.time-window-control__marker-dot:after{content:\"\";background:var(--primary-color,#03a9f4);width:2px;height:6px;position:absolute;left:6px}.time-window-control__handle--start .time-window-control__marker-dot:after{top:14px}.time-window-control__handle--end .time-window-control__marker-dot:after{bottom:14px}.time-window-control__ticks{height:18px;color:var(--secondary-text-color,#666);margin:0 22px;font-size:12px;position:relative}.time-window-control__ticks span{white-space:nowrap;position:absolute;left:0}.time-window-control__ticks span:nth-child(2){left:25%;transform:translate(-50%)}.time-window-control__ticks span:nth-child(3){left:50%;transform:translate(-50%)}.time-window-control__ticks span:nth-child(4){left:75%;transform:translate(-50%)}.time-window-control__ticks span:last-child{left:auto;right:0}.time-window-control :disabled{opacity:.6;cursor:not-allowed}.time-window-control input:focus-visible,.time-window-control button:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.time-window-control__feedback{color:var(--secondary-text-color,#666);overflow-wrap:anywhere;margin-top:6px;font-size:14px;line-height:1.5}.time-window-control__feedback:empty{display:none}.time-window-control__feedback p{margin:0}.time-window-control__error{color:var(--error-color,#b71c1c)}.time-window-control__sr-only{clip-path:inset(50%);white-space:nowrap;border:0;width:1px;height:1px;margin:-1px;padding:0;position:absolute;overflow:hidden}"]]]), Ss = { class: "charging-view" }, Cs = {
	key: 0,
	class: "charging-view__status",
	role: "status"
}, ws = {
	key: 1,
	class: "charging-view__status",
	role: "status"
}, Ts = {
	key: 3,
	class: "charging-view__cards"
}, Es = ["aria-labelledby"], Ds = ["id"], Os = /*#__PURE__*/ bo(/* @__PURE__ */ V({
	__name: "ChargingLayout",
	props: {
		switchKey: { type: String },
		hideConfirmedLabel: { type: Boolean },
		cards: { type: Array }
	},
	setup(e) {
		let t = e, n = An(qa), r = Vn(), i = $(() => n?.language.value ?? "en"), a = $(() => t.cards.map((e) => {
			let r = e.entities.filter(([e, t]) => n?.entity(e, t)), i = e.layout === "months" && (r.length || n?.entity("switch", t.switchKey)) ? e.entities : r;
			return {
				...e,
				showTimeWindow: !!(e.timeWindow && i.some(([e]) => e === "time")),
				entities: i.filter(([t]) => !e.timeWindow || t !== "time")
			};
		}).filter((e) => e.entities.length || e.showTimeWindow)), o = $(() => {
			let e = [];
			for (let t of a.value) {
				let n = t.group ?? t.key, r = e.at(-1);
				r?.key === n ? r.cards.push(t) : e.push({
					key: n,
					cards: [t],
					wide: !1
				});
			}
			let t = e.filter((e) => !e.cards.some((e) => e.layout)).length;
			return e.map((e) => ({
				...e,
				wide: t <= 1 || e.cards.some((e) => e.layout)
			}));
		}), s = $(() => !!n?.entity("switch", t.switchKey)), c = $(() => i.value === "de" ? {
			loading: "Die Entitäten werden geladen …",
			empty: "Für diese Ansicht sind keine Entitäten verfügbar."
		} : {
			loading: "Loading entities …",
			empty: "No entities are available for this view."
		});
		return (t, l) => (K(), q("div", Ss, [
			!z(n)?.ready.value && !z(n)?.error.value ? (K(), q("p", Cs, M(c.value.loading), 1)) : z(n)?.ready.value && !s.value && !a.value.length ? (K(), q("p", ws, M(c.value.empty), 1)) : Q("", !0),
			s.value ? (K(), J(xo, {
				key: 2,
				domain: "switch",
				"entity-key": e.switchKey,
				"hide-confirmed-label": e.hideConfirmedLabel
			}, null, 8, ["entity-key", "hide-confirmed-label"])) : Q("", !0),
			o.value.length ? (K(), q("div", Ts, [(K(!0), q(W, null, H(o.value, (t) => (K(), q("div", {
				key: t.key,
				class: j(["charging-view__group", { "charging-view__group--wide": t.wide }])
			}, [(K(!0), q(W, null, H(t.cards, (t) => (K(), q("section", {
				key: t.key,
				class: "charging-view__card",
				"aria-labelledby": `${z(r)}-${t.key}`
			}, [
				Y("h2", { id: `${z(r)}-${t.key}` }, M(t.title[i.value]), 9, Ds),
				t.showTimeWindow && t.timeWindow ? (K(), J(xs, {
					key: 0,
					kind: t.timeWindow
				}, null, 8, ["kind"])) : Q("", !0),
				t.entities.length ? (K(), q("div", {
					key: 1,
					class: j(["charging-view__rows", {
						"charging-view__rows--columns": t.layout === "columns",
						"charging-view__rows--months": t.layout === "months"
					}])
				}, [t.layout === "months" ? (K(), J(os, {
					key: 0,
					"entity-keys": t.entities.map(([, e]) => e)
				}, null, 8, ["entity-keys"])) : (K(!0), q(W, { key: 1 }, H(t.entities, ([t, n]) => (K(), q(W, { key: `${t}.${n}` }, [t === "switch" || t === "number" || t === "time" || t === "select" ? (K(), J(xo, {
					key: 0,
					domain: t,
					"entity-key": n,
					"hide-confirmed-label": e.hideConfirmedLabel
				}, null, 8, [
					"domain",
					"entity-key",
					"hide-confirmed-label"
				])) : (K(), J(No, {
					key: 1,
					domain: t,
					"entity-key": n
				}, null, 8, ["domain", "entity-key"]))], 64))), 128))], 2)) : Q("", !0)
			], 8, Es))), 128))], 2))), 128))])) : Q("", !0)
		]));
	}
}), [["styles", [".charging-view{gap:20px;min-width:0;margin-top:24px;display:grid}.charging-view__cards,.charging-view__group{align-content:start;gap:20px;min-width:0;display:grid}.charging-view__card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.charging-view__card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.charging-view__rows{gap:16px;display:grid}.charging-view__card>.time-window-control+.charging-view__rows{border-top:1px solid var(--divider-color,#e0e0e0);margin-top:20px;padding-top:16px}.charging-view__rows>.entity-control{border:0;border-bottom:1px solid var(--divider-color,#e0e0e0);box-shadow:none;border-radius:0;padding:0 0 16px}.charging-view__rows>.entity-control:last-child{border-bottom:0;padding-bottom:0}.charging-view__status{color:var(--secondary-text-color,#666);margin:0;line-height:1.6}@media (max-width:600px){.charging-view,.charging-view__cards,.charging-view__group{gap:16px}.charging-view__card{padding:20px}}@container sax-content (width>=860px){.charging-view{gap:14px;margin-top:16px}.charging-view__cards{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;gap:16px}.charging-view__group{gap:14px}.charging-view__group--wide{grid-column:1/-1}.charging-view__card{padding:18px}.charging-view__card h2{margin-bottom:12px;font-size:16px}.charging-view__rows{gap:12px}.charging-view__rows>.entity-control{gap:8px 12px;padding-bottom:12px}.charging-view__rows>.entity-control:last-child{padding-bottom:0}.charging-view__rows>.entity-control .entity-control__description{flex-basis:120px}.charging-view__rows--columns{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;column-gap:24px}.charging-view__rows--columns>:last-child:nth-child(odd){grid-column:1/-1}.charging-view__rows--columns .entity-value{min-height:44px;padding-block:8px}}"]]]);
//#endregion
//#region src/savings.ts
function ks(e) {
	if (typeof e != "number" && typeof e != "string" || typeof e == "string" && !e.trim()) return null;
	let t = Number(e);
	return Number.isFinite(t) ? t : null;
}
function As(e) {
	return {
		comma_decimal: "en-US",
		decimal_comma: "de-DE",
		space_comma: "fr-FR"
	}[e?.locale?.number_format ?? ""] ?? e?.locale?.language ?? e?.language ?? "en";
}
function js(e, t, n = 2) {
	let r = ks(e);
	return r === null ? null : new Intl.NumberFormat(As(t), {
		minimumFractionDigits: n,
		maximumFractionDigits: n,
		useGrouping: t?.locale?.number_format !== "none"
	}).format(r);
}
function Ms(e, t, n = {
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
function Ns(e, t) {
	let n = (e) => /^\d{4}-\d{2}-\d{2}$/.test(e) && Number(e.slice(0, 4)) > 0 && Number.isFinite(Date.parse(`${e}T00:00:00Z`)) && (/* @__PURE__ */ new Date(`${e}T00:00:00Z`)).toISOString().slice(0, 10) === e;
	return n(e) && n(t) && e <= t;
}
function Ps(e) {
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
function Fs(e, t, n) {
	let r = /* @__PURE__ */ Wt(null), i = /* @__PURE__ */ R(!1), a = /* @__PURE__ */ R(null), o, s = 0, c = !1;
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
					first_weekday: Ps(u),
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
		if (!Ns(e, t)) {
			a.value = "invalid";
			return;
		}
		o = {
			start_date: e,
			end_date: t
		}, l();
	}
	return Nn([
		() => e()?.connection,
		t,
		n,
		() => Ps(e()),
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
	}, { immediate: !0 }), Te(() => {
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
//#region src/components/TariffPlan.vue?vue&type=script&setup=true&lang.ts
var Is = ["aria-labelledby"], Ls = ["id"], Rs = { class: "tariff-plan__scroll" }, zs = { class: "tariff-plan__table" }, Bs = ["aria-label"], Vs = { colspan: "2" }, Hs = {
	key: 0,
	class: "tariff-plan__low-status"
}, Us = {
	key: 1,
	class: "tariff-plan__low-unavailable"
}, Ws = { key: 2 }, Gs = { key: 0 }, Ks = { key: 3 }, qs = /*#__PURE__*/ bo(/* @__PURE__ */ V({
	__name: "TariffPlan",
	props: { hass: { type: Object } },
	setup(e) {
		let t = e, n = An(qa), r = Vn(), i = $(() => n?.language.value === "de" ? {
			tariff: "Tarifpreisfenster",
			from: "Von",
			to: "Bis",
			price: "Arbeitspreis",
			status: "Status",
			now: "jetzt",
			base: "Grundpreis",
			low: "Niedertarif",
			lowUntil: "Niedertarif aktiv bis",
			notLow: "Aktuell kein Niedertarif.",
			rule: "Die Tarifpreisfenster bestimmen die verbindlichen Ladezeiten. Niedertarif ist die niedrigste täglich tatsächlich vorkommende Preisstufe, einschließlich des Grundpreises in Fensterlücken. Die SOC-Ladung darf nur im Niedertarif laden; SOC-Grenzen und aktive Monate gelten weiterhin.",
			configure: "Zeiten sind nur unter Konfigurieren → Tarifpreisfenster änderbar. Bisherige separate Netzladezeiten sind bei diesem Tarif unwirksam.",
			noLowTariff: "Tarifdaten fehlen oder sind ungültig. Die SOC-Ladung bleibt gesperrt, bis gültige Tarifdaten vorliegen.",
			feed: "Einspeisevergütung",
			next: "Nächster Preiswechsel",
			unavailable: "Nicht verfügbar",
			noPrice: "Derzeit gilt kein Preis. Bitte die Tarifkonfiguration prüfen."
		} : {
			tariff: "Tariff price windows",
			from: "From",
			to: "To",
			price: "Import price",
			status: "Status",
			now: "now",
			base: "Base price",
			low: "Low tariff",
			lowUntil: "Low tariff active until",
			notLow: "The low tariff is not currently active.",
			rule: "The tariff price windows define the binding charging times. The low tariff is the lowest price level that actually occurs each day, including the base price in gaps between windows. SOC charging is only allowed during the low tariff; SOC limits and active months still apply.",
			configure: "Times can only be changed under Configure → Tariff price windows. Previously configured separate grid charging times have no effect for this tariff.",
			noLowTariff: "Tariff data is missing or invalid. SOC charging remains blocked until valid tariff data is available.",
			feed: "Feed-in remuneration",
			next: "Next price change",
			unavailable: "Unavailable",
			noPrice: "No price currently applies. Please check the tariff configuration."
		}), a = $(() => n?.entity("sensor", "economics_current_import_price")), o = (e) => {
			let n = js(e, t.hass, 4);
			return n === null ? i.value.unavailable : `${n} EUR/kWh`;
		}, s = (e) => Ms(e, t.hass) ?? i.value.unavailable, c = $(() => a.value?.state?.attributes ?? {}), l = $(() => c.value.tariff_type === "time_of_use"), u = $(() => Array.isArray(c.value.windows) ? c.value.windows.filter((e) => !!e && typeof e == "object" && typeof e.start == "string" && typeof e.end == "string") : []), d = $(() => c.value.unavailable_reason), f = $(() => a.value?.available === !0 && ks(a.value.state?.state) !== null && d.value == null), p = $(() => f.value && ks(c.value.low_tariff_price_eur_kwh) !== null && typeof c.value.low_tariff_active == "boolean" && (c.value.low_tariff_active === !1 || m.value !== null) && typeof c.value.base_price_is_low_tariff == "boolean" && Array.isArray(c.value.windows) && u.value.length === c.value.windows.length && u.value.every((e) => typeof e.low_tariff == "boolean" && ks(e.price_eur_kwh) !== null)), m = $(() => Ms(c.value.low_tariff_valid_until, t.hass)), h = $(() => p.value && c.value.low_tariff_active === !0 && m.value !== null), g = (e) => p.value && e.low_tariff === !0, _ = $(() => p.value && c.value.base_price_is_low_tariff === !0), v = (e, t) => [e ? i.value.now : "", t ? i.value.low : ""].filter(Boolean).join(" · "), y = $(() => {
			let e = c.value.active_window;
			return e && typeof e == "object" ? e : null;
		}), b = (e) => f.value && ks(e.price_eur_kwh) !== null && y.value?.start === e.start && y.value?.end === e.end, x = $(() => f.value && y.value === null && ks(c.value.base_price_eur_kwh) !== null), S = (e) => Ms(`2000-01-01T${e.length === 5 ? `${e}:00` : e}Z`, t.hass, {
			timeStyle: "short",
			timeZone: "UTC"
		}) ?? e.slice(0, 5);
		return (e, t) => l.value ? (K(), q("section", {
			key: 0,
			class: "tariff-plan",
			"aria-labelledby": `${z(r)}-tariff`
		}, [
			Y("h2", { id: `${z(r)}-tariff` }, M(i.value.tariff), 9, Ls),
			Y("p", null, M(i.value.rule), 1),
			Y("p", null, M(i.value.configure), 1),
			Y("div", Rs, [Y("table", zs, [Y("thead", null, [Y("tr", null, [
				Y("th", { "aria-label": i.value.status }, null, 8, Bs),
				Y("th", null, M(i.value.from), 1),
				Y("th", null, M(i.value.to), 1),
				Y("th", null, M(i.value.price), 1)
			])]), Y("tbody", null, [(K(!0), q(W, null, H(u.value, (e, t) => (K(), q("tr", {
				key: t,
				class: j({
					"tariff-plan__current": b(e),
					"tariff-plan__low": g(e)
				})
			}, [
				Y("td", null, M(v(b(e), g(e))), 1),
				Y("td", null, M(S(e.start)), 1),
				Y("td", null, M(S(e.end)), 1),
				Y("td", null, M(o(e.price_eur_kwh)), 1)
			], 2))), 128)), Y("tr", { class: j({
				"tariff-plan__current": x.value,
				"tariff-plan__low": _.value
			}) }, [
				Y("td", null, M(v(x.value, _.value)), 1),
				Y("td", Vs, M(i.value.base), 1),
				Y("td", null, M(o(c.value.base_price_eur_kwh)), 1)
			], 2)])])]),
			p.value ? (K(), q("p", Hs, [
				Y("strong", null, M(i.value.low) + ":", 1),
				Z(" " + M(o(c.value.low_tariff_price_eur_kwh)) + ". ", 1),
				h.value ? (K(), q(W, { key: 0 }, [Z(M(i.value.lowUntil) + " " + M(m.value) + ". ", 1)], 64)) : (K(), q(W, { key: 1 }, [Z(M(i.value.notLow), 1)], 64))
			])) : (K(), q("p", Us, M(i.value.noLowTariff), 1)),
			Y("p", null, [Y("strong", null, M(i.value.feed) + ":", 1), Z(" " + M(o(c.value.feed_in_price_eur_kwh)), 1)]),
			f.value ? c.value.next_price_change_at ? (K(), q("p", Ks, [Y("strong", null, M(i.value.next) + ":", 1), Z(" " + M(s(c.value.next_price_change_at)), 1)])) : Q("", !0) : (K(), q("p", Ws, [Z(M(i.value.noPrice), 1), typeof d.value == "string" && d.value ? (K(), q("span", Gs, " (" + M(d.value) + ")", 1)) : Q("", !0)]))
		], 8, Is)) : Q("", !0);
	}
}), [["styles", [".tariff-plan{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.tariff-plan h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.tariff-plan p{overflow-wrap:anywhere;line-height:1.6}.tariff-plan p:last-child{margin-bottom:0}.tariff-plan__scroll{overflow-x:auto}.tariff-plan__table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%;line-height:1.5}.tariff-plan__table th,.tariff-plan__table td{text-align:left;white-space:nowrap;border-bottom:1px solid var(--divider-color,#e0e0e0);padding:10px 8px}.tariff-plan__table th:last-child,.tariff-plan__table td:last-child{text-align:right}.tariff-plan__current{background:var(--secondary-background-color,color-mix(in srgb, currentColor 8%, transparent));font-weight:600}@media (max-width:600px){.tariff-plan{padding:20px}}@container sax-content (width>=860px){.tariff-plan{padding:18px}.tariff-plan h2{margin-bottom:12px;font-size:16px}.tariff-plan p{margin-top:10px;line-height:1.5}.tariff-plan__table th,.tariff-plan__table td{padding:7px 8px}}"]]]), Js = ["aria-labelledby"], Ys = ["id"], Xs = { key: 0 }, Zs = {
	key: 0,
	class: "charge-plan__target"
}, Qs = /*#__PURE__*/ bo(/* @__PURE__ */ V({
	__name: "ChargePlan",
	props: { hass: { type: Object } },
	setup(e) {
		let t = e, n = An(qa), r = Vn(), i = $(() => n?.language.value === "de"), a = $(() => n?.entity("sensor", "bridge_charge_plan")), o = $(() => a.value?.state?.attributes ?? {}), s = $(() => i.value ? {
			title: "Ladeplanung",
			unavailable: "Die Ladeplanung ist derzeit nicht verfügbar.",
			incomplete: "Die Angaben zum Ladeplan sind noch unvollständig. Ladezeiten können derzeit nicht angezeigt werden.",
			off: "Die verbrauchsabhängige Ladeplanung ist ausgeschaltet.",
			waiting_for_data: "Für die Ladeplanung werden noch gültige Verbrauchsdaten und ein PV-Start benötigt. Die Verbrauchsprognose benötigt mindestens eine Minute Beobachtungszeit.",
			paused: "Die Ladeplanung ist pausiert. Die geplante Netzladung ist derzeit nicht freigegeben.",
			complete: "Die geplante Netzladung ist abgeschlossen.",
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
			not_needed: "No grid charging is currently needed.",
			insufficient: "The available grid charging is not expected to cover the entire period until PV starts."
		}), c = $(() => a.value?.available ? a.value.state?.state : "unavailable"), l = $(() => i.value ? {
			pv_start_missing: "Die gewählte PV-Prognose liefert noch keinen Zeitraum, der den Verbrauch mindestens 30 Minuten lang deckt. Bitte die PV-Prognose in den Integrationsoptionen prüfen.",
			consumption_missing: "Für die Verbrauchsprognose wird mindestens eine Minute Entlademessung benötigt.",
			measurements_missing: "Aktuelle Batteriemesswerte fehlen.",
			calibration: "Die Batteriekalibrierung hat Vorrang.",
			pv_surplus: "PV-Überschuss pausiert die geplante Netzladung.",
			manual_charge: "Die manuelle Ladung hat Vorrang.",
			disabled: "Die verbrauchsabhängige Ladeplanung in den Integrationsoptionen aktivieren und den Hauptschalter „Netzladung aktiv“ einschalten."
		} : {
			pv_start_missing: "The selected PV forecast does not yet provide a period covering consumption for at least 30 minutes. Check the PV forecast in the integration options.",
			consumption_missing: "The consumption forecast needs at least one minute of discharge measurements.",
			measurements_missing: "Current battery measurements are missing.",
			calibration: "Battery calibration takes priority.",
			pv_surplus: "PV surplus pauses planned grid charging.",
			manual_charge: "Manual charging takes priority.",
			disabled: "Enable consumption-based charging planning in the integration options and turn on the main grid charging switch."
		}), u = $(() => typeof o.value.reason == "string" ? l.value[o.value.reason] : void 0);
		function d(e, n, r, i = 1) {
			let a = ks(e);
			return a !== null && a >= n && a <= r ? js(a, t.hass, i) : null;
		}
		function f(e) {
			return typeof e == "string" && /^\d{4}-\d{2}-\d{2}T.+(?:Z|[+-]\d{2}:\d{2})$/.test(e) ? Ms(e, t.hass) : null;
		}
		let p = $(() => ({
			discharge: f(o.value.discharge_at),
			start: f(o.value.charge_start),
			end: f(o.value.charge_end),
			pv: f(o.value.pv_start)
		})), m = $(() => {
			let e = d(o.value.observation_minutes, 1, 60);
			if (!e || !p.value.discharge) return null;
			let t = d(o.value.average_discharge_w, 0, Infinity, 0);
			return i.value ? `Aufgrund des Verbrauchs der letzten ${e} Minuten${t ? ` (durchschnittlich ${t} W)` : ""} wird der Speicher voraussichtlich bis ${p.value.discharge} Uhr entleert sein.` : `Based on consumption over the last ${e} minutes${t ? ` (an average of ${t} W)` : ""}, the battery is expected to be depleted by ${p.value.discharge}.`;
		}), h = $(() => {
			let { start: e, end: t, pv: n } = p.value, r = c.value === "charging" && (ks(o.value.shortfall_kwh) ?? 0) > 0;
			switch (r ? "insufficient" : c.value) {
				case "planned":
				case "charging": {
					if (!e || !t || !n) return [s.value.incomplete];
					let r = c.value === "charging", a = i.value ? `${r ? "Die Niedertarifladung läuft seit" : m.value ? "Daher beginnt die Aufladung im Niedertarif um" : "Die Aufladung im Niedertarif beginnt um"} ${e} Uhr und dauert voraussichtlich bis ${t} Uhr, um die Zeit bis zum PV-Start um ${n} Uhr zu überbrücken.` : `${r ? "Low-tariff charging has been running since" : m.value ? "Therefore, low-tariff charging will start at" : "Low-tariff charging will start at"} ${e} and is expected to continue until ${t}, to cover consumption until PV starts at ${n}.`;
					return [m.value, a];
				}
				case "not_needed": return [m.value, n ? i.value ? `Eine Netzladung ist nicht erforderlich: Der Speicher reicht voraussichtlich bis zum PV-Start um ${n} Uhr.` : `No grid charging is needed: the battery is expected to last until PV starts at ${n}.` : s.value.not_needed];
				case "insufficient": {
					let a = d(o.value.shortfall_kwh, 0, Infinity, 2), c = a ? i.value ? ` Voraussichtlicher Fehlbetrag: ${a} kWh.` : ` Expected shortfall: ${a} kWh.` : "", l = e && t ? i.value ? r ? `Eine teilweise Aufladung im Niedertarif läuft seit ${e} Uhr bis voraussichtlich ${t} Uhr.` : `Eine teilweise Aufladung im Niedertarif ist von ${e} Uhr bis voraussichtlich ${t} Uhr geplant.` : r ? `Partial low-tariff charging has been running since ${e} and is expected to continue until ${t}.` : `Partial low-tariff charging is planned from ${e} until approximately ${t}.` : null, u = n ? i.value ? `Der PV-Start wird für ${n} Uhr erwartet.` : `PV is expected to start at ${n}.` : null;
					return [
						m.value,
						s.value.insufficient + c,
						l,
						u
					];
				}
				case "off": return [s.value.off, u.value ?? l.value.disabled];
				case "waiting_for_data": return [u.value ?? s.value.waiting_for_data];
				case "paused": return [s.value.paused, u.value];
				case "complete": return [s.value.complete];
				default: return [s.value.unavailable];
			}
		}), g = $(() => {
			if (![
				"planned",
				"charging",
				"insufficient"
			].includes(c.value ?? "")) return null;
			let e = d(o.value.target_soc, 0, 100);
			return e ? i.value ? `Geplantes Ladeziel: ${e} %.` : `Planned charge target: ${e} %.` : null;
		});
		return (e, t) => a.value ? (K(), q("section", {
			key: 0,
			class: "charge-plan",
			"aria-labelledby": `${z(r)}-charge-plan`
		}, [
			Y("h2", { id: `${z(r)}-charge-plan` }, M(s.value.title), 9, Ys),
			(K(!0), q(W, null, H(h.value, (e, t) => (K(), q(W, { key: t }, [e ? (K(), q("p", Xs, M(e), 1)) : Q("", !0)], 64))), 128)),
			g.value ? (K(), q("p", Zs, M(g.value), 1)) : Q("", !0)
		], 8, Js)) : Q("", !0);
	}
}), [["styles", [".charge-plan{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.charge-plan h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.charge-plan p{overflow-wrap:anywhere;line-height:1.6}.charge-plan p:last-child{margin-bottom:0}.charge-plan__target{color:var(--secondary-text-color,#666)}@media (max-width:600px){.charge-plan{padding:20px}}@container sax-content (width>=860px){.charge-plan{padding:18px}.charge-plan h2{margin-bottom:12px;font-size:16px}}"]]]), $s = { class: "timed-charging-view" }, ec = /*#__PURE__*/ bo(/* @__PURE__ */ V({
	__name: "TimedChargingView",
	props: { hass: { type: Object } },
	setup(e) {
		let t = An(qa), n = $(() => t?.entity("sensor", "bridge_charge_plan")?.state?.attributes.enabled === !0), r = $(() => t?.entity("sensor", "economics_current_import_price")?.state?.attributes.tariff_type === "time_of_use"), i = [
			{
				key: "window",
				group: "schedule",
				timeWindow: "timed_charge",
				title: {
					de: "Netzladezeitfenster",
					en: "Grid charging window"
				},
				entities: [["time", "timed_charge_start"], ["time", "timed_charge_end"]]
			},
			{
				key: "discharge",
				group: "schedule",
				title: {
					de: "Entladestatus",
					en: "Discharge status"
				},
				entities: [["sensor", "timed_charge_discharge_status"]]
			},
			{
				key: "settings",
				title: {
					de: "Einstellungen",
					en: "Settings"
				},
				entities: [["number", "timed_charge_max_soc"], ["number", "timed_charge_min_soc"]]
			},
			{
				key: "months",
				layout: "months",
				title: {
					de: "Aktive Monate",
					en: "Active months"
				},
				entities: Array.from({ length: 12 }, (e, t) => ["switch", `timed_charge_month_${t + 1}`])
			}
		], a = $(() => i.filter((e) => e.key !== "window" || !n.value && !r.value).map((e) => ({
			...e,
			entities: e.entities.filter(([, e]) => !n.value || e !== "timed_charge_min_soc")
		})));
		return (t, n) => (K(), q("div", $s, [
			X(Os, {
				"switch-key": "timed_charge_enabled",
				cards: a.value,
				"hide-confirmed-label": ""
			}, null, 8, ["cards"]),
			X(Qs, {
				hass: e.hass,
				class: "timed-charging-view__tariff"
			}, null, 8, ["hass"]),
			X(qs, {
				hass: e.hass,
				class: "timed-charging-view__tariff"
			}, null, 8, ["hass"])
		]));
	}
}), [["styles", [".timed-charging-view{min-width:0}.timed-charging-view__tariff{margin-top:20px}@media (max-width:600px){.timed-charging-view__tariff{margin-top:16px}}@container sax-content (width>=860px){.timed-charging-view__tariff{margin-top:16px}}"]]]), tc = /* @__PURE__ */ V({
	__name: "GridServingView",
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
		return (e, n) => (K(), J(Os, {
			"switch-key": "grid_serving_enabled",
			cards: t
		}));
	}
}), nc = /* @__PURE__ */ V({
	__name: "DynamicChargingView",
	setup(e) {
		let t = [{
			key: "price",
			layout: "columns",
			title: {
				de: "Preisoptimiertes Laden",
				en: "Price-optimised charging"
			},
			entities: [
				["select", "price_charge_strategy"],
				["number", "price_charge_max_price"],
				["number", "price_charge_neutral_price"],
				["number", "price_charge_hours"],
				["number", "max_soc"],
				["sensor", "price_charge_active_text"],
				["sensor", "price_charge_status_text"],
				["sensor", "grid_serving_forecast"],
				["sensor", "price_charge_next_start"],
				["sensor", "price_charge_current_price"]
			]
		}];
		return (e, n) => (K(), J(Os, {
			"switch-key": "price_charge_enabled",
			cards: t,
			"hide-confirmed-label": ""
		}));
	}
}), rc = { class: "savings-view" }, ic = { class: "savings-overview" }, ac = ["aria-labelledby"], oc = ["id"], sc = ["aria-labelledby"], cc = ["id"], lc = {
	key: 0,
	class: "savings-progress"
}, uc = ["id"], dc = { class: "savings-large" }, fc = [
	"role",
	"aria-labelledby",
	"aria-valuemin",
	"aria-valuemax",
	"aria-valuenow"
], pc = {
	key: 1,
	class: "savings-rows"
}, mc = { key: 0 }, hc = { key: 1 }, gc = { key: 2 }, _c = { key: 3 }, vc = ["aria-label"], yc = { class: "savings-large" }, bc = ["aria-labelledby"], xc = ["id"], Sc = ["for"], Cc = ["id", "max"], wc = ["for"], Tc = ["id", "min"], Ec = { type: "submit" }, Dc = ["disabled"], Oc = {
	key: 0,
	role: "status"
}, kc = {
	key: 1,
	role: "alert"
}, Ac = { class: "savings-selected-dates" }, jc = { class: "savings-large" }, Mc = ["id"], Nc = { class: "savings-chart-hint" }, Pc = [
	"viewBox",
	"aria-labelledby",
	"aria-describedby"
], Fc = ["id"], Ic = [
	"x1",
	"x2",
	"y1",
	"y2"
], Lc = ["x"], Rc = ["x"], zc = ["x"], Bc = ["x"], Vc = [
	"x",
	"y",
	"width",
	"height"
], Hc = { class: "savings-chart-table" }, Uc = { class: "savings-table-scroll" }, Wc = { class: "savings-table" }, Gc = {
	key: 1,
	class: "savings-empty"
}, Kc = { class: "savings-card savings-explanation" }, qc = {
	key: 1,
	class: "savings-card savings-status",
	role: "status"
}, Jc = /*#__PURE__*/ bo(/* @__PURE__ */ V({
	__name: "SavingsView",
	props: {
		hass: { type: Object },
		entryId: { type: String }
	},
	setup(e) {
		let t = e, n = An(qa), r = Vn(), i = $(() => n?.language.value === "de"), a = $(() => i.value ? {
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
			storage_error: "Die Wirtschaftlichkeitsbilanz ist wegen eines Speicherfehlers angehalten. Bitte in den Home-Assistant-Reparaturen das Korrupt-Backup wiederherstellen; bloßes Neuladen startet keine neue Bilanz.",
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
			storage_error: "Accounting has stopped because of a storage error. Restore the corrupt backup in Home Assistant Repairs; reloading alone does not start a new ledger.",
			missing: "Economics data are currently unavailable."
		}), o = $(() => n?.entity("binary_sensor", "economics_investment_configured")), s = $(() => n?.entity("sensor", "economics_amortization_progress")), c = $(() => n?.entity("sensor", "economics_remaining_to_payback")), l = $(() => n?.entity("sensor", "economics_roi")), u = $(() => n?.entity("sensor", "economics_net_savings")), d = $(() => n?.entity("sensor", "economics_status")), f = $(() => s.value?.available ? ks(s.value.state?.state) : null), p = $(() => f.value === null ? null : Math.max(0, Math.min(100, f.value))), m = (e) => {
			let n = js(e, t.hass);
			return n === null ? a.value.unavailable : `${n} €`;
		}, h = (e) => Ms(e, t.hass) ?? a.value.unavailable, g = (e) => Ms(`${e}T12:00:00Z`, t.hass, {
			dateStyle: "medium",
			timeZone: "UTC"
		}) ?? e, _ = $(() => {
			let e = d.value?.available ? d.value.state?.state : void 0;
			return e === "active" ? null : e === "disabled" || e === "price_unavailable" || e === "origin_unavailable" || e === "partial_price_coverage" || e === "storage_error" ? a.value[e] : a.value.missing;
		}), v = Fs(() => t.hass, () => t.entryId, () => u.value?.metadata.entity_id), y = /* @__PURE__ */ R(""), b = /* @__PURE__ */ R(""), x = null;
		Nn(v.data, (e) => {
			e && ((!y.value && !b.value || y.value === x?.start && b.value === x?.end) && (y.value = e.selected.start_date, b.value = e.selected.end_date), x = {
				start: e.selected.start_date,
				end: e.selected.end_date
			});
		}), Nn(() => t.entryId, () => {
			y.value = "", b.value = "", x = null;
		});
		let S = $(() => v.error.value === "invalid" ? a.value.invalid : v.error.value === "failed" ? a.value.failed : v.error.value === "unavailable" || v.data.value?.status === "recorder_unavailable" ? a.value.noRecorder : null), C = [
			"day",
			"week",
			"month",
			"year"
		], w = $(() => v.data.value?.selected.buckets ?? []), ee = /* @__PURE__ */ R(null), T = /* @__PURE__ */ R(720);
		Nn(ee, (e, t, n) => {
			if (!e) return;
			let r = (e) => {
				Number.isFinite(e) && e > 0 && (T.value = e);
			};
			if (r(e.getBoundingClientRect().width), typeof ResizeObserver > "u") return;
			let i = new ResizeObserver((e) => {
				for (let t of e) r(t.contentRect.width);
			});
			i.observe(e), n(() => i.disconnect());
		});
		let E = $(() => {
			let e = w.value.map((e) => ks(e.change)), n = Math.max(0, ...e.map((e) => e ?? 0)), r = Math.min(0, ...e.map((e) => e ?? 0)), i = n - r || 1, a = (e) => 20 + (n - e) / i * 180, o = v.data.value?.selected, s = Date.parse(o?.start ?? ""), c = Date.parse(o?.end ?? ""), l = c - s, u = js(n, t.hass) ?? "", d = js(r, t.hass) ?? "", f = Math.max(56, Math.max(u.length, d.length) * 7.1 + 12), p = T.value - 24, m = Math.max(1, p - f), g = (e) => f + Math.max(0, Math.min(1, (Date.parse(e) - s) / l)) * m;
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
		}), D = $(() => w.value.some((e) => ks(e.change) !== null)), O = (e) => Ms(e, t.hass, v.data.value?.selected.period === "hour" ? { timeStyle: "short" } : v.data.value?.selected.period === "month" ? {
			month: "short",
			year: "numeric"
		} : {
			day: "2-digit",
			month: "short"
		}) ?? e;
		return (t, i) => (K(), q("div", rc, [
			Y("div", ic, [o.value?.available && o.value.state?.state === "off" ? (K(), q("section", {
				key: 0,
				class: "savings-card savings-payback",
				"aria-labelledby": `${z(r)}-investment`
			}, [Y("h2", { id: `${z(r)}-investment` }, M(a.value.payback), 9, oc), Y("p", null, M(a.value.investment), 1)], 8, ac)) : o.value?.available && o.value.state?.state === "on" && (s.value || c.value || l.value || u.value || d.value) ? (K(), q("section", {
				key: 1,
				class: "savings-card savings-payback",
				"aria-labelledby": `${z(r)}-payback`
			}, [
				Y("h2", { id: `${z(r)}-payback` }, M(a.value.payback), 9, cc),
				s.value ? (K(), q("div", lc, [
					Y("h3", { id: `${z(r)}-progress` }, M(s.value.name), 9, uc),
					Y("p", dc, M(f.value === null ? a.value.unavailable : `${z(js)(f.value, e.hass)} %`), 1),
					Y("div", {
						class: "savings-progress__track",
						role: p.value === null ? void 0 : "meter",
						"aria-labelledby": `${z(r)}-progress`,
						"aria-valuemin": p.value === null ? void 0 : 0,
						"aria-valuemax": p.value === null ? void 0 : 100,
						"aria-valuenow": p.value ?? void 0
					}, [p.value === null ? Q("", !0) : (K(), q("span", {
						key: 0,
						style: le({ width: `${p.value}%` })
					}, null, 4))], 8, fc)
				])) : Q("", !0),
				c.value || l.value || u.value || d.value ? (K(), q("dl", pc, [
					c.value ? (K(), q("div", mc, [Y("dt", null, M(c.value.name), 1), Y("dd", null, M(m(c.value.available ? c.value.state?.state : null)), 1)])) : Q("", !0),
					l.value ? (K(), q("div", hc, [Y("dt", null, M(a.value.prior), 1), Y("dd", null, M(m(l.value.available ? l.value.state?.attributes.prior_result_eur ?? l.value.state?.attributes.prior_result_eur_formatted : null)), 1)])) : Q("", !0),
					u.value ? (K(), q("div", gc, [Y("dt", null, M(a.value.net), 1), Y("dd", null, M(m(u.value.available ? u.value.state?.state : null)), 1)])) : Q("", !0),
					d.value ? (K(), q("div", _c, [Y("dt", null, M(a.value.started), 1), Y("dd", null, M(h(d.value.available ? d.value.state?.attributes.economics_started_at : null)), 1)])) : Q("", !0)
				])) : Q("", !0)
			], 8, sc)) : Q("", !0), u.value ? (K(), q("section", {
				key: 2,
				class: "savings-periods",
				"aria-label": a.value.periods
			}, [(K(), q(W, null, H(C, (e) => Y("article", {
				key: e,
				class: "savings-card"
			}, [Y("h2", null, M(a.value[e]), 1), Y("p", yc, M(z(v).loading.value ? "…" : m(z(v).data.value?.periods[e].change)), 1)])), 64))], 8, vc)) : Q("", !0)]),
			X(qs, {
				hass: e.hass,
				class: "savings-tariff"
			}, null, 8, ["hass"]),
			u.value ? (K(), q("section", {
				key: 0,
				class: "savings-card savings-range",
				"aria-labelledby": `${z(r)}-range`
			}, [
				Y("h2", { id: `${z(r)}-range` }, M(a.value.range), 9, xc),
				Y("form", {
					class: "savings-dates",
					onSubmit: i[3] ||= Fa((e) => z(v).select(y.value, b.value), ["prevent"])
				}, [
					Y("label", { for: `${z(r)}-from` }, [Z(M(a.value.from), 1), Dn(Y("input", {
						id: `${z(r)}-from`,
						"onUpdate:modelValue": i[0] ||= (e) => y.value = e,
						type: "date",
						required: "",
						max: b.value || void 0
					}, null, 8, Cc), [[Ma, y.value]])], 8, Sc),
					Y("label", { for: `${z(r)}-to` }, [Z(M(a.value.to), 1), Dn(Y("input", {
						id: `${z(r)}-to`,
						"onUpdate:modelValue": i[1] ||= (e) => b.value = e,
						type: "date",
						required: "",
						min: y.value || void 0
					}, null, 8, Tc), [[Ma, b.value]])], 8, wc),
					Y("button", Ec, M(a.value.apply), 1),
					Y("button", {
						type: "button",
						disabled: z(v).loading.value,
						onClick: i[2] ||= (...e) => z(v).refresh && z(v).refresh(...e)
					}, M(a.value.refresh), 9, Dc)
				], 32),
				z(v).loading.value ? (K(), q("p", Oc, M(a.value.loading), 1)) : S.value ? (K(), q("p", kc, M(S.value), 1)) : z(v).data.value ? (K(), q(W, { key: 2 }, [
					Y("p", Ac, M(g(z(v).data.value.selected.start_date)) + " – " + M(g(z(v).data.value.selected.end_date)), 1),
					Y("h3", null, M(a.value.selected), 1),
					Y("p", jc, M(m(z(v).data.value.selected.change)), 1),
					Y("h3", { id: `${z(r)}-chart` }, M(a.value.chart), 9, Mc),
					Y("p", Nc, M(a.value.chartHint), 1),
					D.value ? (K(), q(W, { key: 0 }, [(K(), q("svg", {
						ref_key: "chartElement",
						ref: ee,
						class: "savings-chart",
						viewBox: `0 0 ${T.value} 240`,
						role: "img",
						"aria-labelledby": `${z(r)}-chart`,
						"aria-describedby": `${z(r)}-chart-description`
					}, [
						Y("desc", { id: `${z(r)}-chart-description` }, M(a.value.net) + ": " + M(m(z(v).data.value.selected.change)) + ". " + M(a.value.table) + ". ", 9, Fc),
						Y("line", {
							x1: E.value.left - 2,
							x2: E.value.right + 2,
							y1: E.value.zero,
							y2: E.value.zero,
							class: "savings-chart__axis"
						}, null, 8, Ic),
						Y("text", {
							x: E.value.left - 8,
							y: "24",
							"text-anchor": "end"
						}, M(E.value.highLabel), 9, Lc),
						Y("text", {
							x: E.value.left - 8,
							y: "204",
							"text-anchor": "end"
						}, M(E.value.lowLabel), 9, Rc),
						i[4] ||= Y("text", {
							x: "10",
							y: "226"
						}, "EUR", -1),
						w.value.length ? (K(), q("text", {
							key: 0,
							x: E.value.left,
							y: "226"
						}, M(O(E.value.start)), 9, zc)) : Q("", !0),
						w.value.length > 1 ? (K(), q("text", {
							key: 1,
							x: E.value.right,
							y: "226",
							"text-anchor": "end"
						}, M(O(E.value.end)), 9, Bc)) : Q("", !0),
						(K(!0), q(W, null, H(E.value.bars, (e, t) => (K(), q("rect", {
							key: t,
							x: e.x,
							y: e.y,
							width: e.width,
							height: e.height,
							class: j(["savings-chart__bar", { "savings-chart__bar--negative": (e.value ?? 0) < 0 }])
						}, [Y("title", null, M(e.label) + ": " + M(m(e.value)), 1)], 10, Vc))), 128))
					], 8, Pc)), Y("details", Hc, [Y("summary", null, M(a.value.table), 1), Y("div", Uc, [Y("table", Wc, [Y("thead", null, [Y("tr", null, [
						Y("th", null, M(a.value.from), 1),
						Y("th", null, M(a.value.to), 1),
						Y("th", null, M(a.value.net), 1)
					])]), Y("tbody", null, [(K(!0), q(W, null, H(E.value.bars, (e, t) => (K(), q("tr", { key: t }, [
						Y("td", null, M(e.label), 1),
						Y("td", null, M(h(e.end)), 1),
						Y("td", null, M(m(e.value)), 1)
					]))), 128))])])])])], 64)) : Q("", !0),
					!D.value || z(v).data.value.selected.change === null ? (K(), q("p", Gc, M(z(v).data.value.selected.change === null ? a.value.noData : a.value.noChartData), 1)) : Q("", !0)
				], 64)) : Q("", !0)
			], 8, bc)) : Q("", !0),
			Y("details", Kc, [
				Y("summary", null, M(a.value.explain), 1),
				Y("p", null, M(a.value.netHint), 1),
				Y("p", null, M(a.value.calendarHint), 1),
				Y("p", null, M(a.value.rangeHint), 1)
			]),
			_.value && z(n)?.ready.value ? (K(), q("p", qc, M(_.value), 1)) : Q("", !0)
		]));
	}
}), [["styles", [".savings-view{gap:20px;min-width:0;margin-top:24px;display:grid}.savings-overview{display:contents}.savings-card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.savings-card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.savings-card h3{margin:20px 0 8px;font-size:16px;font-weight:500}.savings-card p{overflow-wrap:anywhere;line-height:1.6}.savings-card p:last-child{margin-bottom:0}.savings-large{font-variant-numeric:tabular-nums;margin:0 0 12px;font-size:28px;font-weight:500}.savings-progress__track{background:var(--divider-color,#e0e0e0);border-radius:8px;height:16px;overflow:hidden}.savings-progress__track span{background:var(--info-color,#039be5);height:100%;display:block}.savings-rows{margin:20px 0 0}.savings-rows>div{border-bottom:1px solid var(--divider-color,#e0e0e0);justify-content:space-between;gap:16px;padding:12px 0;line-height:1.5;display:flex}.savings-rows>div:last-child{border-bottom:0;padding-bottom:0}.savings-rows dd{text-align:right;font-variant-numeric:tabular-nums;margin:0}.savings-periods{grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:16px;display:grid}.savings-periods h2{font-size:16px}.savings-table-scroll{overflow-x:auto}.savings-table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%;line-height:1.5}.savings-table th,.savings-table td{text-align:left;border-bottom:1px solid var(--divider-color,#e0e0e0);padding:10px 8px}.savings-table th:last-child,.savings-table td:last-child{text-align:right}.savings-dates{flex-wrap:wrap;align-items:end;gap:16px;display:flex}.savings-dates label{flex:180px;gap:8px;min-width:0;display:grid}.savings-dates input,.savings-dates button{box-sizing:border-box;font:inherit;border:1px solid var(--divider-color,#bdbdbd);background:var(--ha-card-background,var(--card-background-color,#fff));min-height:44px;color:var(--primary-text-color,#212121);border-radius:6px;padding:10px 12px}.savings-dates input{--lightningcss-light:initial;--lightningcss-dark: ;color-scheme:light dark;width:100%}@media (prefers-color-scheme:dark){.savings-dates input{--lightningcss-light: ;--lightningcss-dark:initial}}.savings-dates button{cursor:pointer;color:var(--primary-color,#0288d1)}.savings-dates button:disabled{opacity:.6;cursor:default}.savings-dates :focus-visible,.savings-card summary:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:3px}.savings-selected-dates,.savings-empty{color:var(--secondary-text-color,#666)}.savings-chart{width:100%;height:auto;display:block;overflow:visible}.savings-chart text{fill:var(--secondary-text-color,#666);font-size:12px}.savings-chart__axis{stroke:var(--primary-text-color,#212121);stroke-width:1px}.savings-chart__bar{fill:var(--info-color,#039be5)}.savings-chart__bar--negative{fill:var(--error-color,#db4437)}.savings-card summary{cursor:pointer;min-height:24px;font-weight:500;line-height:1.6}.savings-chart-table{margin-top:16px}.savings-status{margin:0;line-height:1.6}@container sax-content (width>=860px){.savings-view{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;gap:16px;margin-top:16px}.savings-view>*{grid-column:1/-1}.savings-overview{gap:16px;min-width:0;display:grid}.savings-overview:empty{display:none}.savings-view:has(>.savings-overview>section):has(>.savings-tariff)>:is(.savings-overview,.savings-tariff){grid-column:auto}.savings-card{padding:18px}.savings-card h2{margin-bottom:12px;font-size:16px}.savings-card h3{margin-top:16px;font-size:14px}.savings-card p{margin-top:10px;line-height:1.5}.savings-progress h3{margin-top:0}.savings-card .savings-large{margin-top:0;margin-bottom:8px;font-size:24px}.savings-rows{margin-top:12px}.savings-rows>div{gap:12px;padding:8px 0}.savings-rows dt{min-width:0}.savings-rows dd{flex-shrink:0;max-width:58%}.savings-periods{grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.savings-view:has(>.savings-tariff) .savings-periods{grid-template-columns:repeat(2,minmax(0,1fr))}.savings-periods .savings-card{padding:14px 16px}.savings-periods h2{margin-bottom:6px;font-size:14px}.savings-periods .savings-large{margin-bottom:0;font-size:22px}.savings-table th,.savings-table td{padding:7px 8px}.savings-dates{gap:12px}.savings-dates label{flex:0 220px;gap:6px}.savings-range .savings-selected-dates{margin-bottom:8px}.savings-range .savings-chart-hint{margin-top:0;margin-bottom:8px}.savings-chart-table{margin-top:12px}}@media (max-width:600px){.savings-view{gap:16px}.savings-card{padding:20px}.savings-rows>div{flex-wrap:wrap;gap:4px 16px}.savings-rows dd{margin-left:auto}}"]]]), Yc = ["lang"], Xc = { class: "header" }, Zc = ["aria-label"], Qc = ["aria-label"], $c = [
	"href",
	"aria-current",
	"onClick"
], el = {
	key: 0,
	class: "status",
	role: "alert"
}, tl = { class: "introduction" }, nl = {
	class: "section",
	"aria-labelledby": "section-heading"
}, rl = {
	key: 0,
	class: "status",
	role: "status"
}, il = {
	key: 1,
	class: "status",
	role: "status"
}, al = {
	key: 7,
	class: "status"
}, ol = ["href"], sl = /* @__PURE__ */ Sa(/* @__PURE__ */ bo(/* @__PURE__ */ V({
	__name: "Panel.ce",
	props: {
		hass: { type: Object },
		narrow: { type: Boolean },
		panel: { type: Object },
		route: { type: Object }
	},
	setup(e) {
		let t = e, n = Ta(), r = Za(() => t.hass, () => t.panel?.config?.entry_id);
		kn(qa, r);
		let i = $(() => t.hass?.language.toLowerCase().startsWith("de") ? "de" : "en"), a = $(() => Ga[i.value]), o = $(() => !t.hass?.kioskMode && (t.narrow || t.hass?.dockedSidebar === "always_hidden")), s = $(() => `/${t.panel?.url_path || "sax-power-vue"}`), c = /* @__PURE__ */ R(t.route?.path ?? window.location.pathname), l = $(() => {
			let e = r.entity("switch", "timed_charge_enabled"), t = r.entity("switch", "price_charge_enabled");
			if (e?.available && t?.available) {
				if (e.state?.state === "on" && t.state?.state === "off") return "ladeautomatik";
				if (t.state?.state === "on" && e.state?.state === "off") return "dynamisches-laden";
			}
		}), u = $(() => Ua.filter((e) => !l.value || !["ladeautomatik", "dynamisches-laden"].includes(e.path) || e.path === l.value)), d = $(() => Wa(c.value, s.value)), f = $(() => l.value && ["ladeautomatik", "dynamisches-laden"].includes(d.value) ? l.value : d.value), p = $(() => Ua.find((e) => e.path === f.value)), m = /* @__PURE__ */ R();
		Nn(() => t.route?.path, (e) => {
			e !== void 0 && (c.value = e);
		}), Nn([d, f], ([e, t]) => {
			if (e === t) return;
			let n = `${s.value}/${t}`;
			c.value = n, window.history.replaceState(null, "", n), window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: !0 } })), mn(() => m.value?.focus());
		}, { immediate: !0 });
		function h() {
			c.value = window.location.pathname;
		}
		Zn(() => {
			window.addEventListener("popstate", h), window.addEventListener("location-changed", h);
		}), Qn(() => {
			window.removeEventListener("popstate", h), window.removeEventListener("location-changed", h);
		});
		function g(e, t) {
			e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || (e.preventDefault(), window.location.pathname !== t && (window.history.pushState(null, "", t), window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: !1 } }))), h(), mn(() => m.value?.focus()));
		}
		function _() {
			n?.dispatchEvent(new CustomEvent("hass-toggle-menu", {
				bubbles: !0,
				composed: !0
			}));
		}
		return (t, n) => (K(), q("div", {
			class: j(["dashboard", { narrow: e.narrow }]),
			lang: i.value
		}, [
			Y("header", Xc, [o.value ? (K(), q("button", {
				key: 0,
				class: "menu-button",
				type: "button",
				"aria-label": a.value.menu,
				onClick: _
			}, [...n[1] ||= [Y("svg", {
				viewBox: "0 0 24 24",
				"aria-hidden": "true"
			}, [Y("path", { d: "M4 6h16M4 12h16M4 18h16" })], -1)]], 8, Zc)) : Q("", !0), n[2] ||= Y("div", { class: "brand" }, [Y("svg", {
				class: "brand-icon",
				viewBox: "0 0 24 24",
				"aria-hidden": "true"
			}, [Y("path", { d: "M9 3h6M8 5h8a1 1 0 0 1 1 1v14H7V6a1 1 0 0 1 1-1Z" }), Y("path", { d: "m13 8-3 5h4l-3 5" })]), Y("span", null, "SAX Power")], -1)]),
			Y("nav", {
				class: "navigation",
				"aria-label": a.value.navigation
			}, [(K(!0), q(W, null, H(u.value, (e) => (K(), q("a", {
				key: e.path,
				href: `${s.value}/${e.path}`,
				"aria-current": f.value === e.path ? "page" : void 0,
				onClick: (t) => g(t, `${s.value}/${e.path}`)
			}, M(e[i.value]), 9, $c))), 128))], 8, Qc),
			Y("main", null, [
				z(r).error.value ? (K(), q("p", el, M(z(r).error.value), 1)) : Q("", !0),
				Y("p", tl, M(a.value.introduction), 1),
				Y("section", nl, [Y("h1", {
					id: "section-heading",
					ref_key: "heading",
					ref: m,
					tabindex: "-1"
				}, M(p.value?.[i.value] ?? a.value.notFound), 513), e.hass ? e.panel?.config?.entry_id ? f.value === "allgemein" ? (K(), J(Vo, { key: 2 })) : f.value === "ladeautomatik" ? (K(), J(ec, {
					key: 3,
					hass: e.hass
				}, null, 8, ["hass"])) : f.value === "netzdienliches-laden" ? (K(), J(tc, { key: 4 })) : f.value === "dynamisches-laden" ? (K(), J(nc, { key: 5 })) : f.value === "ersparnis" ? (K(), J(Jc, {
					key: 6,
					hass: e.hass,
					"entry-id": e.panel?.config?.entry_id
				}, null, 8, ["hass", "entry-id"])) : (K(), q("div", al, [Y("p", null, M(a.value.notFoundDescription), 1), Y("a", {
					href: `${s.value}/allgemein`,
					onClick: n[0] ||= (e) => g(e, `${s.value}/allgemein`)
				}, M(a.value.returnToOverview), 9, ol)])) : (K(), q("p", il, M(a.value.missingEntry), 1)) : (K(), q("p", rl, M(a.value.loading), 1))])
			])
		], 10, Yc));
	}
}), [["styles", [":host{height:100%;color:var(--primary-text-color,#212121);background:var(--primary-background-color,#fafafa);font-family:var(--paper-font-body1_-_font-family,Roboto, sans-serif);font-size:14px;display:block}*{box-sizing:border-box}.dashboard{min-height:100%;container:sax-panel/inline-size}.header{background:var(--app-header-background-color,var(--primary-color,#03a9f4));min-height:64px;color:var(--app-header-text-color,#fff);align-items:center;gap:14px;padding:8px 24px;display:flex}.brand{align-items:center;gap:10px;font-size:20px;font-weight:500;display:flex}.header svg{fill:none;stroke:currentColor;stroke-width:1.7px;stroke-linecap:round;stroke-linejoin:round}.brand-icon{width:30px;height:30px}.menu-button{width:44px;height:44px;color:inherit;cursor:pointer;background:0 0;border:0;border-radius:50%;place-items:center;margin-left:-10px;display:grid}.menu-button svg{width:24px;height:24px}.navigation{border-bottom:1px solid var(--divider-color,#e0e0e0);background:var(--card-background-color,#fff);padding:0 16px;display:flex;overflow-x:auto}.navigation a{min-height:56px;color:var(--secondary-text-color,#666);white-space:nowrap;border-bottom:3px solid #0000;align-items:center;padding:12px 16px;text-decoration:none;display:flex}.navigation a[aria-current=page]{border-color:var(--primary-color,#03a9f4);color:var(--primary-text-color,#212121);font-weight:600}a{color:var(--primary-text-color,#212121);text-underline-offset:3px}a:focus-visible,button:focus-visible{outline-offset:-4px;outline:2px solid}main{max-width:1120px;margin:0 auto;padding:28px 24px 48px}.introduction{color:var(--secondary-text-color,#666);margin:0 0 24px;line-height:1.6}.section{overflow-wrap:anywhere;border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));box-shadow:var(--ha-card-box-shadow,none);padding:28px;container:sax-content/inline-size}h1{margin:0;font-size:24px;font-weight:500;line-height:1.35}h1:focus{outline:none}h2{margin:0 0 12px;font-size:18px;font-weight:500;line-height:1.5}.status{margin-top:24px;line-height:1.7}.narrow .header{padding-left:16px;padding-right:16px}.narrow main{padding:16px 12px 32px}@container sax-panel (width>=940px){.header{min-height:56px;padding:6px 20px}.navigation a{min-height:48px;padding:8px 14px}main{max-width:1360px;padding:16px 20px 20px}.introduction{margin-bottom:12px}.section{padding:20px}h1{font-size:22px}}@media (max-width:600px){.header{gap:8px;padding:8px 16px}.brand{gap:6px;font-size:18px}.brand-icon{display:none}.navigation{padding:0 4px}main{padding:16px 12px 32px}.introduction{margin-bottom:16px}.section{padding:20px}h1{font-size:22px}}"]]]));
customElements.get("sax-power-vue-panel") || customElements.define("sax-power-vue-panel", sl);
//#endregion
export { sl as SaxPowerVuePanel };
