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
}, l = Object.prototype.hasOwnProperty, u = (e, t) => l.call(e, t), d = Array.isArray, f = (e) => x(e) === "[object Map]", p = (e) => x(e) === "[object Set]", m = (e) => x(e) === "[object Date]", h = (e) => typeof e == "function", g = (e) => typeof e == "string", _ = (e) => typeof e == "symbol", v = (e) => typeof e == "object" && !!e, y = (e) => (v(e) || h(e)) && h(e.then) && h(e.catch), b = Object.prototype.toString, x = (e) => b.call(e), ee = (e) => x(e).slice(8, -1), S = (e) => x(e) === "[object Object]", C = (e) => g(e) && e !== "NaN" && e[0] !== "-" && "" + parseInt(e, 10) === e, te = /* @__PURE__ */ e(",key,ref,ref_for,ref_key,onVnodeBeforeMount,onVnodeMounted,onVnodeBeforeUpdate,onVnodeUpdated,onVnodeBeforeUnmount,onVnodeUnmounted"), ne = (e) => {
	let t = /* @__PURE__ */ Object.create(null);
	return ((n) => t[n] || (t[n] = e(n)));
}, re = /-\w/g, w = ne((e) => e.replace(re, (e) => e.slice(1).toUpperCase())), T = /\B([A-Z])/g, E = ne((e) => e.replace(T, "-$1").toLowerCase()), D = ne((e) => e.charAt(0).toUpperCase() + e.slice(1)), ie = ne((e) => e ? `on${D(e)}` : ""), O = (e, t) => !Object.is(e, t), ae = (e, ...t) => {
	for (let n = 0; n < e.length; n++) e[n](...t);
}, oe = (e, t, n, r = !1) => {
	Object.defineProperty(e, t, {
		configurable: !0,
		enumerable: !1,
		writable: r,
		value: n
	});
}, se = (e) => {
	let t = parseFloat(e);
	return isNaN(t) ? e : t;
}, ce = (e) => {
	let t = g(e) ? Number(e) : NaN;
	return isNaN(t) ? e : t;
}, k, le = () => k ||= typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : typeof global < "u" ? global : {};
function ue(e) {
	if (d(e)) {
		let t = {};
		for (let n = 0; n < e.length; n++) {
			let r = e[n], i = g(r) ? me(r) : ue(r);
			if (i) for (let e in i) t[e] = i[e];
		}
		return t;
	}
	if (g(e) || v(e)) return e;
}
var de = /;(?![^(]*\))/g, fe = /:([^]+)/, pe = /\/\*[^]*?\*\//g;
function me(e) {
	let t = {};
	return e.replace(pe, "").split(de).forEach((e) => {
		if (e) {
			let n = e.split(fe);
			n.length > 1 && (t[n[0].trim()] = n[1].trim());
		}
	}), t;
}
function he(e) {
	let t = "";
	if (g(e)) t = e;
	else if (d(e)) for (let n = 0; n < e.length; n++) {
		let r = he(e[n]);
		r && (t += r + " ");
	}
	else if (v(e)) for (let n in e) e[n] && (t += n + " ");
	return t.trim();
}
var ge = "itemscope,allowfullscreen,formnovalidate,ismap,nomodule,novalidate,readonly", _e = /* @__PURE__ */ e(ge);
ge + "";
function ve(e) {
	return !!e || e === "";
}
function ye(e, t) {
	if (e.length !== t.length) return !1;
	let n = !0;
	for (let r = 0; n && r < e.length; r++) n = A(e[r], t[r]);
	return n;
}
function be(e, t) {
	if (e.size !== t.size) return !1;
	let n = Array.from(t), r = new Uint8Array(n.length);
	for (let t of e) {
		let e = -1;
		for (let i = 0; i < n.length; i++) if (!r[i] && A(t, n[i])) {
			e = i;
			break;
		}
		if (e < 0) return !1;
		r[e] = 1;
	}
	return !0;
}
function A(e, t) {
	if (e === t) return !0;
	let n = m(e), r = m(t);
	if (n || r) return n && r ? e.getTime() === t.getTime() : !1;
	if (n = _(e), r = _(t), n || r) return e === t;
	if (n = d(e), r = d(t), n || r) return n && r ? ye(e, t) : !1;
	if (n = v(e), r = v(t), n || r) {
		if (!n || !r) return !1;
		if (n = f(e), r = f(t), n || r || (n = p(e), r = p(t), n || r)) return n && r ? be(e, t) : !1;
		if (Object.keys(e).length !== Object.keys(t).length) return !1;
		for (let n in e) {
			let r = e.hasOwnProperty(n), i = t.hasOwnProperty(n);
			if (r && !i || !r && i || !A(e[n], t[n])) return !1;
		}
	}
	return String(e) === String(t);
}
function xe(e, t) {
	return e.findIndex((e) => A(e, t));
}
var Se = (e) => !!(e && e.__v_isRef === !0), j = (e) => g(e) ? e : e == null ? "" : d(e) || v(e) && (e.toString === b || !h(e.toString)) ? Se(e) ? j(e.value) : JSON.stringify(e, Ce, 2) : String(e), Ce = (e, t) => Se(t) ? Ce(e, t.value) : f(t) ? { [`Map(${t.size})`]: [...t.entries()].reduce((e, [t, n], r) => (e[we(t, r) + " =>"] = n, e), {}) } : p(t) ? { [`Set(${t.size})`]: [...t.values()].map((e) => we(e)) } : _(t) ? we(t) : v(t) && !d(t) && !S(t) ? String(t) : t, we = (e, t = "") => _(e) ? `Symbol(${e.description ?? t})` : e, M, Te = class {
	constructor(e = !1) {
		this.detached = e, this._active = !0, this._on = 0, this.effects = [], this.cleanups = [], this._isPaused = !1, this._warnOnRun = !0, this.__v_skip = !0, !e && M && (M.active ? (this.parent = M, this.index = (M.scopes || (M.scopes = [])).push(this) - 1) : (this._active = !1, this._warnOnRun = !1));
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
			let t = M;
			try {
				return M = this, e();
			} finally {
				M = t;
			}
		}
	}
	on() {
		++this._on === 1 && (this.prevScope = M, M = this);
	}
	off() {
		if (this._on > 0 && --this._on === 0) {
			if (M === this) M = this.prevScope;
			else {
				let e = M;
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
function Ee() {
	return M;
}
function De(e, t = !1) {
	M && M.cleanups.push(e);
}
var N, Oe = /* @__PURE__ */ new WeakSet(), ke = class {
	constructor(e) {
		this.fn = e, this.deps = void 0, this.depsTail = void 0, this.flags = 5, this.next = void 0, this.cleanup = void 0, this.scheduler = void 0, M && (M.active ? M.effects.push(this) : this.flags &= -2);
	}
	pause() {
		this.flags |= 64;
	}
	resume() {
		this.flags & 64 && (this.flags &= -65, Oe.has(this) && (Oe.delete(this), this.trigger()));
	}
	notify() {
		this.flags & 2 && !(this.flags & 32) || this.flags & 8 || Ne(this);
	}
	run() {
		if (!(this.flags & 1)) return this.fn();
		this.flags |= 2, Ke(this), Ie(this);
		let e = N, t = He;
		N = this, He = !0;
		try {
			return this.fn();
		} finally {
			Le(this), N = e, He = t, this.flags &= -3;
		}
	}
	stop() {
		if (this.flags & 1) {
			for (let e = this.deps; e; e = e.nextDep) Be(e);
			this.deps = this.depsTail = void 0, Ke(this), this.onStop && this.onStop(), this.flags &= -2;
		}
	}
	trigger() {
		this.flags & 64 ? Oe.add(this) : this.scheduler ? this.scheduler() : this.runIfDirty();
	}
	runIfDirty() {
		Re(this) && this.run();
	}
	get dirty() {
		return Re(this);
	}
}, Ae = 0, je, Me;
function Ne(e, t = !1) {
	if (e.flags |= 8, t) {
		e.next = Me, Me = e;
		return;
	}
	e.next = je, je = e;
}
function Pe() {
	Ae++;
}
function Fe() {
	if (--Ae > 0) return;
	if (Me) {
		let e = Me;
		for (Me = void 0; e;) {
			let t = e.next;
			e.next = void 0, e.flags &= -9, e = t;
		}
	}
	let e;
	for (; je;) {
		let t = je;
		for (je = void 0; t;) {
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
function Ie(e) {
	for (let t = e.deps; t; t = t.nextDep) t.version = -1, t.prevActiveLink = t.dep.activeLink, t.dep.activeLink = t;
}
function Le(e) {
	let t, n = e.depsTail, r = n;
	for (; r;) {
		let e = r.prevDep;
		r.version === -1 ? (r === n && (n = e), Be(r), Ve(r)) : t = r, r.dep.activeLink = r.prevActiveLink, r.prevActiveLink = void 0, r = e;
	}
	e.deps = t, e.depsTail = n;
}
function Re(e) {
	for (let t = e.deps; t; t = t.nextDep) if (t.dep.version !== t.version || t.dep.computed && (ze(t.dep.computed) || t.dep.version !== t.version)) return !0;
	return !!e._dirty;
}
function ze(e) {
	if (e.flags & 4 && !(e.flags & 16) || (e.flags &= -17, e.globalVersion === qe) || (e.globalVersion = qe, !e.isSSR && e.flags & 128 && (!e.deps && !e._dirty || !Re(e)))) return;
	e.flags |= 2;
	let t = e.dep, n = N, r = He;
	N = e, He = !0;
	try {
		Ie(e);
		let n = e.fn(e._value);
		(t.version === 0 || O(n, e._value)) && (e.flags |= 128, e._value = n, t.version++);
	} catch (e) {
		throw t.version++, e;
	} finally {
		N = n, He = r, Le(e), e.flags &= -3;
	}
}
function Be(e, t = !1) {
	let { dep: n, prevSub: r, nextSub: i } = e;
	if (r && (r.nextSub = i, e.prevSub = void 0), i && (i.prevSub = r, e.nextSub = void 0), n.subs === e && (n.subs = r, !r && n.computed)) {
		n.computed.flags &= -5;
		for (let e = n.computed.deps; e; e = e.nextDep) Be(e, !0);
	}
	!t && !--n.sc && n.map && n.map.delete(n.key);
}
function Ve(e) {
	let { prevDep: t, nextDep: n } = e;
	t && (t.nextDep = n, e.prevDep = void 0), n && (n.prevDep = t, e.nextDep = void 0);
}
var He = !0, Ue = [];
function We() {
	Ue.push(He), He = !1;
}
function Ge() {
	let e = Ue.pop();
	He = e === void 0 || e;
}
function Ke(e) {
	let { cleanup: t } = e;
	if (e.cleanup = void 0, t) {
		let e = N;
		N = void 0;
		try {
			t();
		} finally {
			N = e;
		}
	}
}
var qe = 0, Je = class {
	constructor(e, t) {
		this.sub = e, this.dep = t, this.version = t.version, this.nextDep = this.prevDep = this.nextSub = this.prevSub = this.prevActiveLink = void 0;
	}
}, Ye = class {
	constructor(e) {
		this.computed = e, this.version = 0, this.activeLink = void 0, this.subs = void 0, this.map = void 0, this.key = void 0, this.sc = 0, this.__v_skip = !0;
	}
	track(e) {
		if (!N || !He || N === this.computed) return;
		let t = this.activeLink;
		if (t === void 0 || t.sub !== N) t = this.activeLink = new Je(N, this), N.deps ? (t.prevDep = N.depsTail, N.depsTail.nextDep = t, N.depsTail = t) : N.deps = N.depsTail = t, Xe(t);
		else if (t.version === -1 && (t.version = this.version, t.nextDep)) {
			let e = t.nextDep;
			e.prevDep = t.prevDep, t.prevDep && (t.prevDep.nextDep = e), t.prevDep = N.depsTail, t.nextDep = void 0, N.depsTail.nextDep = t, N.depsTail = t, N.deps === t && (N.deps = e);
		}
		return t;
	}
	trigger(e) {
		this.version++, qe++, this.notify(e);
	}
	notify(e) {
		Pe();
		try {
			for (let e = this.subs; e; e = e.prevSub) e.sub.notify() && e.sub.dep.notify();
		} finally {
			Fe();
		}
	}
};
function Xe(e) {
	if (e.dep.sc++, e.sub.flags & 4) {
		let t = e.dep.computed;
		if (t && !e.dep.subs) {
			t.flags |= 20;
			for (let e = t.deps; e; e = e.nextDep) Xe(e);
		}
		let n = e.dep.subs;
		n !== e && (e.prevSub = n, n && (n.nextSub = e)), e.dep.subs = e;
	}
}
var Ze = /* @__PURE__ */ new WeakMap(), Qe = /* @__PURE__ */ Symbol(""), $e = /* @__PURE__ */ Symbol(""), et = /* @__PURE__ */ Symbol("");
function P(e, t, n) {
	if (He && N) {
		let t = Ze.get(e);
		t || Ze.set(e, t = /* @__PURE__ */ new Map());
		let r = t.get(n);
		r || (t.set(n, r = new Ye()), r.map = t, r.key = n), r.track();
	}
}
function tt(e, t, n, r, i, a) {
	let o = Ze.get(e);
	if (!o) {
		qe++;
		return;
	}
	let s = (e) => {
		e && e.trigger();
	};
	if (Pe(), t === "clear") o.forEach(s);
	else {
		let i = d(e), a = i && C(n);
		if (i && n === "length") {
			let e = Number(r);
			o.forEach((t, n) => {
				(n === "length" || n === et || !_(n) && n >= e) && s(t);
			});
		} else switch ((n !== void 0 || o.has(void 0)) && s(o.get(n)), a && s(o.get(et)), t) {
			case "add":
				i ? a && s(o.get("length")) : (s(o.get(Qe)), f(e) && s(o.get($e)));
				break;
			case "delete":
				i || (s(o.get(Qe)), f(e) && s(o.get($e)));
				break;
			case "set": f(e) && s(o.get(Qe));
		}
	}
	Fe();
}
function nt(e) {
	let t = /* @__PURE__ */ I(e);
	return t === e ? t : (P(t, "iterate", et), /* @__PURE__ */ F(e) ? t : t.map(Ut));
}
function rt(e) {
	return P(e = /* @__PURE__ */ I(e), "iterate", et), e;
}
function it(e, t) {
	return /* @__PURE__ */ Bt(e) ? Wt(/* @__PURE__ */ zt(e) ? Ut(t) : t) : Ut(t);
}
var at = {
	__proto__: null,
	[Symbol.iterator]() {
		return ot(this, Symbol.iterator, (e) => it(this, e));
	},
	concat(...e) {
		return nt(this).concat(...e.map((e) => d(e) ? nt(e) : e));
	},
	entries() {
		return ot(this, "entries", (e) => (e[1] = it(this, e[1]), e));
	},
	every(e, t) {
		return ct(this, "every", e, t, void 0, arguments);
	},
	filter(e, t) {
		return ct(this, "filter", e, t, (e) => e.map((e) => it(this, e)), arguments);
	},
	find(e, t) {
		return ct(this, "find", e, t, (e) => it(this, e), arguments);
	},
	findIndex(e, t) {
		return ct(this, "findIndex", e, t, void 0, arguments);
	},
	findLast(e, t) {
		return ct(this, "findLast", e, t, (e) => it(this, e), arguments);
	},
	findLastIndex(e, t) {
		return ct(this, "findLastIndex", e, t, void 0, arguments);
	},
	forEach(e, t) {
		return ct(this, "forEach", e, t, void 0, arguments);
	},
	includes(...e) {
		return ut(this, "includes", e);
	},
	indexOf(...e) {
		return ut(this, "indexOf", e);
	},
	join(e) {
		return nt(this).join(e);
	},
	lastIndexOf(...e) {
		return ut(this, "lastIndexOf", e);
	},
	map(e, t) {
		return ct(this, "map", e, t, void 0, arguments);
	},
	pop() {
		return dt(this, "pop");
	},
	push(...e) {
		return dt(this, "push", e);
	},
	reduce(e, ...t) {
		return lt(this, "reduce", e, t);
	},
	reduceRight(e, ...t) {
		return lt(this, "reduceRight", e, t);
	},
	shift() {
		return dt(this, "shift");
	},
	some(e, t) {
		return ct(this, "some", e, t, void 0, arguments);
	},
	splice(...e) {
		return dt(this, "splice", e);
	},
	toReversed() {
		return nt(this).toReversed();
	},
	toSorted(e) {
		return nt(this).toSorted(e);
	},
	toSpliced(...e) {
		return nt(this).toSpliced(...e);
	},
	unshift(...e) {
		return dt(this, "unshift", e);
	},
	values() {
		return ot(this, "values", (e) => it(this, e));
	}
};
function ot(e, t, n) {
	let r = rt(e), i = r[t]();
	return r !== e && !/* @__PURE__ */ F(e) && (i._next = i.next, i.next = () => {
		let e = i._next();
		return e.done || (e.value = n(e.value)), e;
	}), i;
}
var st = Array.prototype;
function ct(e, t, n, r, i, a) {
	let o = rt(e), s = o !== e && !/* @__PURE__ */ F(e), c = o[t];
	if (c !== st[t]) {
		let t = c.apply(e, a);
		return s ? Ut(t) : t;
	}
	let l = n;
	o !== e && (s ? l = function(t, r) {
		return n.call(this, it(e, t), r, e);
	} : n.length > 2 && (l = function(t, r) {
		return n.call(this, t, r, e);
	}));
	let u = c.call(o, l, r);
	return s && i ? i(u) : u;
}
function lt(e, t, n, r) {
	let i = rt(e), a = i !== e && !/* @__PURE__ */ F(e), o = n, s = !1;
	i !== e && (a ? (s = r.length === 0, o = function(t, r, i) {
		return s && (s = !1, t = it(e, t)), n.call(this, t, it(e, r), i, e);
	}) : n.length > 3 && (o = function(t, r, i) {
		return n.call(this, t, r, i, e);
	}));
	let c = i[t](o, ...r);
	return s ? it(e, c) : c;
}
function ut(e, t, n) {
	let r = /* @__PURE__ */ I(e);
	P(r, "iterate", et);
	let i = r[t](...n);
	return (i === -1 || i === !1) && /* @__PURE__ */ Vt(n[0]) ? (n[0] = /* @__PURE__ */ I(n[0]), r[t](...n)) : i;
}
function dt(e, t, n = []) {
	We(), Pe();
	let r = (/* @__PURE__ */ I(e))[t].apply(e, n);
	return Fe(), Ge(), r;
}
var ft = /* @__PURE__ */ e("__proto__,__v_isRef,__isVue"), pt = new Set(/* @__PURE__ */ Object.getOwnPropertyNames(Symbol).filter((e) => e !== "arguments" && e !== "caller").map((e) => Symbol[e]).filter(_));
function mt(e) {
	_(e) || (e = String(e));
	let t = /* @__PURE__ */ I(this);
	return P(t, "has", e), t.hasOwnProperty(e);
}
var ht = class {
	constructor(e = !1, t = !1) {
		this._isReadonly = e, this._isShallow = t;
	}
	get(e, t, n) {
		if (t === "__v_skip") return e.__v_skip;
		let r = this._isReadonly, i = this._isShallow;
		if (t === "__v_isReactive") return !r;
		if (t === "__v_isReadonly") return r;
		if (t === "__v_isShallow") return i;
		if (t === "__v_raw") return n === (r ? i ? Nt : Mt : i ? jt : At).get(e) || Object.getPrototypeOf(e) === Object.getPrototypeOf(n) ? e : void 0;
		let a = d(e);
		if (!r) {
			let e;
			if (a && (e = at[t])) return e;
			if (t === "hasOwnProperty") return mt;
		}
		let o = Reflect.get(e, t, /* @__PURE__ */ L(e) ? e : n);
		if ((_(t) ? pt.has(t) : ft(t)) || (r || P(e, "get", t), i)) return o;
		if (/* @__PURE__ */ L(o)) {
			let e = a && C(t) ? o : o.value;
			return r && v(e) ? /* @__PURE__ */ Lt(e) : e;
		}
		return v(o) ? r ? /* @__PURE__ */ Lt(o) : /* @__PURE__ */ Ft(o) : o;
	}
}, gt = class extends ht {
	constructor(e = !1) {
		super(!1, e);
	}
	set(e, t, n, r) {
		let i = e[t], a = d(e) && C(t);
		if (!this._isShallow) {
			let e = /* @__PURE__ */ Bt(i);
			if (!/* @__PURE__ */ F(n) && !/* @__PURE__ */ Bt(n) && (i = /* @__PURE__ */ I(i), n = /* @__PURE__ */ I(n)), !a && /* @__PURE__ */ L(i) && !/* @__PURE__ */ L(n)) return e || (i.value = n), !0;
		}
		let o = a ? Number(t) < e.length : u(e, t), s = Reflect.set(e, t, n, /* @__PURE__ */ L(e) ? e : r);
		return e === /* @__PURE__ */ I(r) && s && (o ? O(n, i) && tt(e, "set", t, n, i) : tt(e, "add", t, n)), s;
	}
	deleteProperty(e, t) {
		let n = u(e, t), r = e[t], i = Reflect.deleteProperty(e, t);
		return i && n && tt(e, "delete", t, void 0, r), i;
	}
	has(e, t) {
		let n = Reflect.has(e, t);
		return (!_(t) || !pt.has(t)) && P(e, "has", t), n;
	}
	ownKeys(e) {
		return P(e, "iterate", d(e) ? "length" : Qe), Reflect.ownKeys(e);
	}
}, _t = class extends ht {
	constructor(e = !1) {
		super(!0, e);
	}
	set(e, t) {
		return !0;
	}
	deleteProperty(e, t) {
		return !0;
	}
}, vt = /* @__PURE__ */ new gt(), yt = /* @__PURE__ */ new _t(), bt = /* @__PURE__ */ new gt(!0), xt = (e) => e, St = (e) => Reflect.getPrototypeOf(e);
function Ct(e, t, n) {
	return function(...r) {
		let i = this.__v_raw, a = /* @__PURE__ */ I(i), o = f(a), c = e === "entries" || e === Symbol.iterator && o, l = e === "keys" && o, u = i[e](...r), d = n ? xt : t ? Wt : Ut;
		return !t && P(a, "iterate", l ? $e : Qe), s(Object.create(u), { next() {
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
function wt(e) {
	return function(...t) {
		return e === "delete" ? !1 : e === "clear" ? void 0 : this;
	};
}
function Tt(e, t) {
	let n = {
		get(n) {
			let r = this.__v_raw, i = /* @__PURE__ */ I(r), a = /* @__PURE__ */ I(n);
			e || (O(n, a) && P(i, "get", n), P(i, "get", a));
			let { has: o } = St(i), s = t ? xt : e ? Wt : Ut;
			if (o.call(i, n)) return s(r.get(n));
			if (o.call(i, a)) return s(r.get(a));
			r !== i && r.get(n);
		},
		get size() {
			let t = this.__v_raw;
			return !e && P(/* @__PURE__ */ I(t), "iterate", Qe), t.size;
		},
		has(t) {
			let n = this.__v_raw, r = /* @__PURE__ */ I(n), i = /* @__PURE__ */ I(t);
			return e || (O(t, i) && P(r, "has", t), P(r, "has", i)), t === i ? n.has(t) : n.has(t) || n.has(i);
		},
		forEach(n, r) {
			let i = this, a = i.__v_raw, o = /* @__PURE__ */ I(a), s = t ? xt : e ? Wt : Ut;
			return !e && P(o, "iterate", Qe), a.forEach((e, t) => n.call(r, s(e), s(t), i));
		}
	};
	return s(n, e ? {
		add: wt("add"),
		set: wt("set"),
		delete: wt("delete"),
		clear: wt("clear")
	} : {
		add(e) {
			let n = /* @__PURE__ */ I(this), r = St(n), i = /* @__PURE__ */ I(e), a = !t && !/* @__PURE__ */ F(e) && !/* @__PURE__ */ Bt(e) ? i : e;
			return r.has.call(n, a) || O(e, a) && r.has.call(n, e) || O(i, a) && r.has.call(n, i) || (n.add(a), tt(n, "add", a, a)), this;
		},
		set(e, n) {
			!t && !/* @__PURE__ */ F(n) && !/* @__PURE__ */ Bt(n) && (n = /* @__PURE__ */ I(n));
			let r = /* @__PURE__ */ I(this), { has: i, get: a } = St(r), o = i.call(r, e);
			o ||= (e = /* @__PURE__ */ I(e), i.call(r, e));
			let s = a.call(r, e);
			return r.set(e, n), o ? O(n, s) && tt(r, "set", e, n, s) : tt(r, "add", e, n), this;
		},
		delete(e) {
			let t = /* @__PURE__ */ I(this), { has: n, get: r } = St(t), i = n.call(t, e);
			i ||= (e = /* @__PURE__ */ I(e), n.call(t, e));
			let a = r ? r.call(t, e) : void 0, o = t.delete(e);
			return i && tt(t, "delete", e, void 0, a), o;
		},
		clear() {
			let e = /* @__PURE__ */ I(this), t = e.size !== 0, n = e.clear();
			return t && tt(e, "clear", void 0, void 0, void 0), n;
		}
	}), [
		"keys",
		"values",
		"entries",
		Symbol.iterator
	].forEach((r) => {
		n[r] = Ct(r, e, t);
	}), n;
}
function Et(e, t) {
	let n = Tt(e, t);
	return (t, r, i) => r === "__v_isReactive" ? !e : r === "__v_isReadonly" ? e : r === "__v_raw" ? t : Reflect.get(u(n, r) && r in t ? n : t, r, i);
}
var Dt = { get: /* @__PURE__ */ Et(!1, !1) }, Ot = { get: /* @__PURE__ */ Et(!1, !0) }, kt = { get: /* @__PURE__ */ Et(!0, !1) }, At = /* @__PURE__ */ new WeakMap(), jt = /* @__PURE__ */ new WeakMap(), Mt = /* @__PURE__ */ new WeakMap(), Nt = /* @__PURE__ */ new WeakMap();
function Pt(e) {
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
function Ft(e) {
	return /* @__PURE__ */ Bt(e) ? e : Rt(e, !1, vt, Dt, At);
}
// @__NO_SIDE_EFFECTS__
function It(e) {
	return Rt(e, !1, bt, Ot, jt);
}
// @__NO_SIDE_EFFECTS__
function Lt(e) {
	return Rt(e, !0, yt, kt, Mt);
}
function Rt(e, t, n, r, i) {
	if (!v(e) || e.__v_raw && !(t && e.__v_isReactive) || e.__v_skip || !Object.isExtensible(e)) return e;
	let a = i.get(e);
	if (a) return a;
	let o = Pt(ee(e));
	if (o === 0) return e;
	let s = new Proxy(e, o === 2 ? r : n);
	return i.set(e, s), s;
}
// @__NO_SIDE_EFFECTS__
function zt(e) {
	return /* @__PURE__ */ Bt(e) ? /* @__PURE__ */ zt(e.__v_raw) : !!(e && e.__v_isReactive);
}
// @__NO_SIDE_EFFECTS__
function Bt(e) {
	return !!(e && e.__v_isReadonly);
}
// @__NO_SIDE_EFFECTS__
function F(e) {
	return !!(e && e.__v_isShallow);
}
// @__NO_SIDE_EFFECTS__
function Vt(e) {
	return e ? !!e.__v_raw : !1;
}
// @__NO_SIDE_EFFECTS__
function I(e) {
	let t = e && e.__v_raw;
	return t ? /* @__PURE__ */ I(t) : e;
}
function Ht(e) {
	return !u(e, "__v_skip") && Object.isExtensible(e) && oe(e, "__v_skip", !0), e;
}
var Ut = (e) => v(e) ? /* @__PURE__ */ Ft(e) : e, Wt = (e) => v(e) ? /* @__PURE__ */ Lt(e) : e;
// @__NO_SIDE_EFFECTS__
function L(e) {
	return e ? e.__v_isRef === !0 : !1;
}
// @__NO_SIDE_EFFECTS__
function R(e) {
	return Kt(e, !1);
}
// @__NO_SIDE_EFFECTS__
function Gt(e) {
	return Kt(e, !0);
}
function Kt(e, t) {
	return /* @__PURE__ */ L(e) ? e : new qt(e, t);
}
var qt = class {
	constructor(e, t) {
		this.dep = new Ye(), this.__v_isRef = !0, this.__v_isShallow = !1, this._rawValue = t ? e : /* @__PURE__ */ I(e), this._value = t ? e : Ut(e), this.__v_isShallow = t;
	}
	get value() {
		return this.dep.track(), this._value;
	}
	set value(e) {
		let t = this._rawValue, n = this.__v_isShallow || /* @__PURE__ */ F(e) || /* @__PURE__ */ Bt(e);
		e = n ? e : /* @__PURE__ */ I(e), O(e, t) && (this._rawValue = e, this._value = n ? e : Ut(e), this.dep.trigger());
	}
};
function z(e) {
	return /* @__PURE__ */ L(e) ? e.value : e;
}
var Jt = {
	get: (e, t, n) => t === "__v_raw" ? e : z(Reflect.get(e, t, n)),
	set: (e, t, n, r) => {
		let i = e[t];
		return /* @__PURE__ */ L(i) && !/* @__PURE__ */ L(n) ? (i.value = n, !0) : Reflect.set(e, t, n, r);
	}
};
function Yt(e) {
	return /* @__PURE__ */ zt(e) ? e : new Proxy(e, Jt);
}
var Xt = class {
	constructor(e, t, n) {
		this.fn = e, this.setter = t, this._value = void 0, this.dep = new Ye(this), this.__v_isRef = !0, this.deps = void 0, this.depsTail = void 0, this.flags = 16, this.globalVersion = qe - 1, this.next = void 0, this.effect = this, this.__v_isReadonly = !t, this.isSSR = n;
	}
	notify() {
		if (this.flags |= 16, !(this.flags & 8) && N !== this) return Ne(this, !0), !0;
	}
	get value() {
		let e = this.dep.track();
		return ze(this), e && (e.version = this.dep.version), this._value;
	}
	set value(e) {
		this.setter && this.setter(e);
	}
};
// @__NO_SIDE_EFFECTS__
function Zt(e, t, n = !1) {
	let r, i;
	return h(e) ? r = e : (r = e.get, i = e.set), new Xt(r, i, n);
}
var Qt = {}, $t = /* @__PURE__ */ new WeakMap(), en = void 0;
function tn(e, t = !1, n = en) {
	if (n) {
		let t = $t.get(n);
		t || $t.set(n, t = []), t.push(e);
	}
}
function nn(e, n, i = t) {
	let { immediate: a, deep: o, once: s, scheduler: l, augmentJob: u, call: f } = i, p = (e) => o ? e : /* @__PURE__ */ F(e) || o === !1 || o === 0 ? rn(e, 1) : rn(e), m, g, _, v, y = !1, b = !1;
	if (/* @__PURE__ */ L(e) ? (g = () => e.value, y = /* @__PURE__ */ F(e)) : /* @__PURE__ */ zt(e) ? (g = () => p(e), y = !0) : d(e) ? (b = !0, y = e.some((e) => /* @__PURE__ */ zt(e) || /* @__PURE__ */ F(e)), g = () => e.map((e) => {
		if (/* @__PURE__ */ L(e)) return e.value;
		if (/* @__PURE__ */ zt(e)) return p(e);
		if (h(e)) return f ? f(e, 2) : e();
	})) : g = h(e) ? n ? f ? () => f(e, 2) : e : () => {
		if (_) {
			We();
			try {
				_();
			} finally {
				Ge();
			}
		}
		let t = en;
		en = m;
		try {
			return f ? f(e, 3, [v]) : e(v);
		} finally {
			en = t;
		}
	} : r, n && o) {
		let e = g, t = o === !0 ? Infinity : o;
		g = () => rn(e(), t);
	}
	let x = Ee(), ee = () => {
		m.stop(), x && x.active && c(x.effects, m);
	};
	if (s && n) {
		let e = n;
		n = (...t) => {
			let n = e(...t);
			return ee(), n;
		};
	}
	let S = b ? Array(e.length).fill(Qt) : Qt, C = (e) => {
		if (m.flags & 1 && (m.dirty || e)) {
			if (n) {
				let t = m.run();
				if (e || o || y || (b ? t.some((e, t) => O(e, S[t])) : O(t, S))) {
					_ && _();
					let e = en;
					en = m;
					try {
						let e = [
							t,
							S === Qt ? void 0 : b && S[0] === Qt ? [] : S,
							v
						];
						S = t, f ? f(n, 3, e) : n(...e);
					} finally {
						en = e;
					}
				}
			} else m.run();
		}
	};
	return u && u(C), m = new ke(g), m.scheduler = l ? () => l(C, !1) : C, v = (e) => tn(e, !1, m), _ = m.onStop = () => {
		let e = $t.get(m);
		if (e) {
			if (f) f(e, 4);
			else for (let t of e) t();
			$t.delete(m);
		}
	}, n ? a ? C(!0) : S = m.run() : l ? l(C.bind(null, !0), !0) : m.run(), ee.pause = m.pause.bind(m), ee.resume = m.resume.bind(m), ee.stop = ee, ee;
}
function rn(e, t = Infinity, n) {
	if (t <= 0 || !v(e) || e.__v_skip || (n ||= /* @__PURE__ */ new Map(), (n.get(e) || 0) >= t)) return e;
	if (n.set(e, t), t--, /* @__PURE__ */ L(e)) rn(e.value, t, n);
	else if (d(e)) for (let r = 0; r < e.length; r++) rn(e[r], t, n);
	else if (p(e) || f(e)) e.forEach((e) => {
		rn(e, t, n);
	});
	else if (S(e)) {
		for (let r in e) rn(e[r], t, n);
		for (let r of Object.getOwnPropertySymbols(e)) Object.prototype.propertyIsEnumerable.call(e, r) && rn(e[r], t, n);
	}
	return e;
}
//#endregion
//#region node_modules/@vue/runtime-core/dist/runtime-core.esm-bundler.js
function an(e, t, n, r) {
	try {
		return r ? e(...r) : e();
	} catch (e) {
		sn(e, t, n);
	}
}
function on(e, t, n, r) {
	if (h(e)) {
		let i = an(e, t, n, r);
		return i && y(i) && i.catch((e) => {
			sn(e, t, n);
		}), i;
	}
	if (d(e)) {
		let i = [];
		for (let a = 0; a < e.length; a++) i.push(on(e[a], t, n, r));
		return i;
	}
}
function sn(e, n, r, i = !0) {
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
			We(), an(o, null, 10, [
				e,
				i,
				a
			]), Ge();
			return;
		}
	}
	cn(e, r, a, i, s);
}
function cn(e, t, n, r = !0, i = !1) {
	if (i) throw e;
	console.error(e);
}
var B = [], ln = -1, un = [], dn = null, fn = 0, pn = /* @__PURE__ */ Promise.resolve(), mn = null;
function hn(e) {
	let t = mn || pn;
	return e ? t.then(this ? e.bind(this) : e) : t;
}
function gn(e) {
	let t = ln + 1, n = B.length;
	for (; t < n;) {
		let r = t + n >>> 1, i = B[r], a = Sn(i);
		a < e || a === e && i.flags & 2 ? t = r + 1 : n = r;
	}
	return t;
}
function _n(e) {
	if (!(e.flags & 1)) {
		let t = Sn(e), n = B[B.length - 1];
		!n || !(e.flags & 2) && t >= Sn(n) ? B.push(e) : B.splice(gn(t), 0, e), e.flags |= 1, vn();
	}
}
function vn() {
	mn ||= pn.then(Cn);
}
function yn(e) {
	if (!d(e)) dn && e.id === -1 ? dn.splice(fn + 1, 0, e) : e.flags & 1 || (un.push(e), e.flags |= 1);
	else for (let t = 0; t < e.length; t++) un.push(e[t]);
	vn();
}
function bn(e, t, n = ln + 1) {
	for (; n < B.length; n++) {
		let t = B[n];
		if (t && t.flags & 2) {
			if (e && t.id !== e.uid) continue;
			B.splice(n, 1), n--, t.flags & 4 && (t.flags &= -2), t(), t.flags & 4 || (t.flags &= -2);
		}
	}
}
function xn(e) {
	if (un.length) {
		let e = [...new Set(un)].sort((e, t) => Sn(e) - Sn(t));
		if (un.length = 0, dn) {
			for (let t = 0; t < e.length; t++) dn.push(e[t]);
			return;
		}
		for (dn = e, fn = 0; fn < dn.length; fn++) {
			let e = dn[fn];
			e.flags & 4 && (e.flags &= -2), e.flags & 8 || e(), e.flags &= -2;
		}
		dn = null, fn = 0;
	}
}
var Sn = (e) => e.id == null ? e.flags & 2 ? -1 : Infinity : e.id;
function Cn(e) {
	try {
		for (ln = 0; ln < B.length; ln++) {
			let e = B[ln];
			e && !(e.flags & 8) && (e.flags & 4 && (e.flags &= -2), an(e, e.i, e.i ? 15 : 14), e.flags & 4 || (e.flags &= -2));
		}
	} finally {
		for (; ln < B.length; ln++) {
			let e = B[ln];
			e && (e.flags &= -2);
		}
		ln = -1, B.length = 0, xn(e), mn = null, (B.length || un.length) && Cn(e);
	}
}
var V = null, wn = null;
function Tn(e) {
	let t = V;
	return V = e, wn = e && e.type.__scopeId || null, t;
}
function En(e, t = V, n) {
	if (!t || e._n) return e;
	let r = (...n) => {
		r._d && ni(-1);
		let i = Tn(t), a = $r.length, o;
		try {
			o = e(...n);
		} finally {
			for (let e = $r.length; e > a; e--) ei();
			Tn(i), r._d && ni(1);
		}
		return o;
	};
	return r._n = !0, r._c = !0, r._d = !0, r;
}
function Dn(e, n) {
	if (V === null) return e;
	let r = Pi(V), i = e.dirs ||= [];
	for (let e = 0; e < n.length; e++) {
		let [a, o, s, c = t] = n[e];
		a && (h(a) && (a = {
			mounted: a,
			updated: a
		}), a.deep && rn(o), i.push({
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
		c && (We(), on(c, n, 8, [
			e.el,
			s,
			e,
			t
		]), Ge());
	}
}
function kn(e, t) {
	if (Z) {
		let n = Z.provides, r = Z.parent && Z.parent.provides;
		r === n && (n = Z.provides = Object.create(r)), n[e] = t;
	}
}
function An(e, t, n = !1) {
	let r = xi();
	if (r || lr) {
		let i = lr ? lr._context.provides : r ? r.parent == null || r.ce ? r.vnode.appContext && r.vnode.appContext.provides : r.parent.provides : void 0;
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
	if (Di) {
		if (c === "sync") {
			let e = Mn();
			f = e.__watcherHandles ||= [];
		} else if (!d) {
			let e = () => {};
			return e.stop = r, e.resume = r, e.pause = r, e;
		}
	}
	let p = Z;
	u.call = (e, t, n) => on(e, p, t, n);
	let m = !1;
	c === "post" ? u.scheduler = (e) => {
		H(e, p && p.suspense);
	} : c !== "sync" && (m = !0, u.scheduler = (e, t) => {
		t ? e() : _n(e);
	}), u.augmentJob = (e) => {
		n && (e.flags |= 4), m && (e.flags |= 2, p && (e.id = p.uid, e.i = p));
	};
	let h = nn(e, n, u);
	return Di && (f ? f.push(h) : d && h()), h;
}
var Fn = /* @__PURE__ */ Symbol("_vte"), In = (e) => e.__isTeleport, Ln = /* @__PURE__ */ Symbol("_leaveCb");
function Rn(e) {
	let t = e[0];
	if (e.length > 1) {
		for (let n of e) if (n.type !== Zr) {
			t = n;
			break;
		}
	}
	return t;
}
function zn(e) {
	if (!Yn(e)) return In(e.type) && e.children ? Rn(e.children) : e;
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
function Vn(e, t) {
	return h(e) ? /* @__PURE__ */ s({ name: e.name }, t, { setup: e }) : e;
}
function Hn() {
	let e = xi();
	return e ? (e.appContext.config.idPrefix || "v") + "-" + e.ids[0] + e.ids[1]++ : "";
}
function Un(e) {
	e.ids = [
		e.ids[0] + e.ids[2]++ + "-",
		0,
		0
	];
}
function Wn(e, t) {
	let n;
	return !!((n = Object.getOwnPropertyDescriptor(e, t)) && !n.configurable);
}
var Gn = /* @__PURE__ */ new WeakMap();
function Kn(e, n, r, a, o = !1) {
	if (d(e)) {
		e.forEach((e, t) => Kn(e, n && (d(n) ? n[t] : n), r, a, o));
		return;
	}
	if (Jn(a) && !o) {
		a.shapeFlag & 512 && a.type.__asyncResolved && a.component.subTree.component && Kn(e, n, r, a.component.subTree);
		return;
	}
	let s = a.shapeFlag & 4 ? Pi(a.component) : a.el, l = o ? null : s, { i: f, r: p } = e, m = n && n.r, _ = f.refs === t ? f.refs = {} : f.refs, v = f.setupState, y = /* @__PURE__ */ I(v), b = v === t ? i : (e) => !Wn(_, e) && u(y, e), x = (e, t) => !(t && Wn(_, t));
	if (m != null && m !== p) {
		if (qn(n), g(m)) _[m] = null, b(m) && (v[m] = null);
		else if (/* @__PURE__ */ L(m)) {
			let e = n;
			x(m, e.k) && (m.value = null), e.k && (_[e.k] = null);
		}
	}
	if (h(p)) an(p, f, 12, [l, _]);
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
					i(), Gn.delete(e);
				};
				t.id = -1, Gn.set(e, t), H(t, r);
			} else qn(e), i();
		}
	}
}
function qn(e) {
	let t = Gn.get(e);
	t && (t.flags |= 8, Gn.delete(e));
}
le().requestIdleCallback, le().cancelIdleCallback;
var Jn = (e) => !!e.type.__asyncLoader, Yn = (e) => e.type.__isKeepAlive;
function Xn(e, t, n = Z, r = !1) {
	if (n) {
		let i = n[e] || (n[e] = []), a = t.__weh ||= (...r) => {
			We();
			let i = wi(n), a = on(t, n, e, r);
			return i(), Ge(), a;
		};
		return r ? i.unshift(a) : i.push(a), a;
	}
}
var Zn = (e) => (t, n = Z) => {
	(!Di || e === "sp") && Xn(e, (...e) => t(...e), n);
}, Qn = Zn("m"), $n = Zn("bum"), er = /* @__PURE__ */ Symbol.for("v-ndc");
function tr(e, t, n, r) {
	let i, a = n && n[r], o = d(e);
	if (o || g(e)) {
		let n = o && /* @__PURE__ */ zt(e), r = !1, s = !1;
		n && (r = !/* @__PURE__ */ F(e), s = /* @__PURE__ */ Bt(e), e = rt(e)), i = Array(e.length);
		for (let n = 0, o = e.length; n < o; n++) i[n] = t(r ? s ? Wt(Ut(e[n])) : Ut(e[n]) : e[n], n, void 0, a && a[n]);
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
var nr = (e) => e ? Ei(e) ? Pi(e) : nr(e.parent) : null, rr = /* @__PURE__ */ s(/* @__PURE__ */ Object.create(null), {
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
		_n(e.update);
	},
	$nextTick: (e) => e.n ||= hn.bind(e.proxy),
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
		if (d) return n === "$attrs" && P(e.attrs, "get", ""), d(e);
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
			version: Ii,
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
					let u = l._ceVNode || Y(n, r);
					return u.appContext = i, s === !0 ? s = "svg" : s === !1 && (s = void 0), o && t ? t(u, a) : e(u, a, s), c = !0, l._container = a, a.__vue_app__ = l, Pi(u.component);
				}
			},
			onUnmount(e) {
				o.push(e);
			},
			unmount() {
				c && (on(o, l._instance, 16), e(null, l._container), delete l._container.__vue_app__);
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
var lr = null, ur = (e, t) => t === "modelValue" || t === "model-value" ? e.modelModifiers : e[`${t}Modifiers`] || e[`${w(t)}Modifiers`] || e[`${E(t)}Modifiers`];
function dr(e, n, ...r) {
	if (e.isUnmounted) return;
	let i = e.vnode.props || t, a = r, o = n.startsWith("update:"), s = o && ur(i, n.slice(7));
	s && (s.trim && (a = r.map((e) => g(e) ? e.trim() : e)), s.number && (a = a.map(se)));
	let c, l = i[c = ie(n)] || i[c = ie(w(n))];
	!l && o && (l = i[c = ie(E(n))]), l && on(l, e, 6, a);
	let u = i[c + "Once"];
	if (u) {
		if (!e.emitted) e.emitted = {};
		else if (e.emitted[c]) return;
		e.emitted[c] = !0, on(u, e, 6, a);
	}
}
function fr(e, t, n = !1) {
	let r = t.emitsCache, i = r.get(e);
	if (i !== void 0) return i;
	let a = e.emits, o = {};
	return a ? (d(a) ? a.forEach((e) => o[e] = null) : s(o, a), v(e) && r.set(e, o), o) : (v(e) && r.set(e, null), null);
}
function pr(e, t) {
	return !e || !a(t) ? !1 : (t = t.slice(2), t = t === "Once" ? t : t.replace(/Once$/, ""), u(e, t[0].toLowerCase() + t.slice(1)) || u(e, E(t)) || u(e, t));
}
function mr(e) {
	let { type: t, vnode: n, proxy: r, withProxy: i, propsOptions: [a], slots: s, attrs: c, emit: l, render: u, renderCache: d, props: f, data: p, setupState: m, ctx: h, inheritAttrs: g } = e, _ = Tn(e), v, y;
	try {
		if (n.shapeFlag & 4) {
			let e = i || r, t = e;
			v = pi(u.call(t, e, d, f, m, p, h)), y = c;
		} else {
			let e = t;
			v = pi(e.length > 1 ? e(f, {
				attrs: c,
				slots: s,
				emit: l
			}) : e(f, null)), y = t.props ? c : hr(c);
		}
	} catch (t) {
		$r.length = 0, sn(t, e, 1), v = Y(Zr);
	}
	let b = v;
	if (y && g !== !1) {
		let e = Object.keys(y), { shapeFlag: t } = b;
		e.length && t & 7 && (a && e.some(o) && (y = gr(y, a)), b = ui(b, y, !1, !0));
	}
	return n.dirs && (b = ui(b, null, !1, !0), b.dirs = b.dirs ? b.dirs.concat(n.dirs) : n.dirs), n.transition && Bn(In(b.type) && zn(b) || b, n.transition), v = b, Tn(_), v;
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
	return n === "style" && v(r) && v(i) ? !A(r, i) : r !== i;
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
	e.props = n ? r ? i : /* @__PURE__ */ It(i) : e.type.props ? i : a, e.attrs = a;
}
function Tr(e, t, n, r) {
	let { props: i, attrs: a, vnode: { patchFlag: o } } = e, s = /* @__PURE__ */ I(i), [c] = e.propsOptions, l = !1;
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
						let t = w(o);
						i[t] = Dr(c, s, t, d, e, !1);
					}
				} else d !== a[o] && (a[o] = d, l = !0);
			}
		}
	} else {
		Er(e, t, i, a) && (l = !0);
		let r;
		for (let a in s) (!t || !u(t, a) && ((r = E(a)) === a || !u(t, r))) && (c ? n && (n[a] !== void 0 || n[r] !== void 0) && (i[a] = Dr(c, s, a, void 0, e, !0)) : delete i[a]);
		if (a !== s) for (let e in a) (!t || !u(t, e)) && (delete a[e], l = !0);
	}
	l && tt(e.attrs, "set", "");
}
function Er(e, n, r, i) {
	let [a, o] = e.propsOptions, s = !1, c;
	if (n) for (let t in n) {
		if (te(t)) continue;
		let l = n[t], d;
		a && u(a, d = w(t)) ? !o || !o.includes(d) ? r[d] = l : (c ||= {})[d] = l : pr(e.emitsOptions, t) || (!(t in i) || l !== i[t]) && (i[t] = l, s = !0);
	}
	if (o) {
		let n = /* @__PURE__ */ I(r), i = c || t;
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
					let o = wi(i);
					r = a[n] = e.call(null, t), o();
				}
			} else r = e;
			i.ce && i.ce._setProp(n, r);
		}
		o[0] && (a && !e ? r = !1 : o[1] && (r === "" || r === E(n)) && (r = !0));
	}
	return r;
}
function Or(e, r, i = !1) {
	let a = r.propsCache, o = a.get(e);
	if (o) return o;
	let c = e.props, l = {}, f = [];
	if (!c) return v(e) && a.set(e, n), n;
	if (d(c)) for (let e = 0; e < c.length; e++) {
		let n = w(c[e]);
		kr(n) && (l[n] = t);
	}
	else if (c) for (let e in c) {
		let t = w(e);
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
	return e[0] !== "$" && !te(e);
}
var Ar = (e) => e === "_" || e === "_ctx" || e === "$stable", jr = (e) => d(e) ? e.map(pi) : [pi(e)], Mr = (e, t, n) => {
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
		e ? (Fr(r, t, n), n && oe(r, "_", e, !0)) : Nr(t, r);
	} else t && Pr(e, t);
}, Lr = (e, n, r) => {
	let { vnode: i, slots: a } = e, o = !0, s = t;
	if (i.shapeFlag & 32) {
		let e = n._;
		e ? r && e === 1 ? o = !1 : Fr(a, n, r) : (o = !n.$stable, Nr(n, a)), s = n;
	} else n && (Pr(e, n), s = { default: 1 });
	if (o) for (let e in a) !Ar(e) && s[e] == null && delete a[e];
}, H = Yr;
function Rr(e) {
	return zr(e);
}
function zr(e, i) {
	let a = le();
	a.__VUE__ = !0;
	let { insert: o, remove: s, patchProp: c, createElement: l, createText: u, createComment: d, setText: f, setElementText: p, parentNode: m, nextSibling: h, setScopeId: g = r, insertStaticContent: _ } = e, v = (e, t, n, r = null, i = null, a = null, o = void 0, s = null, c = !!t.dynamicChildren) => {
		if (e === t) return;
		e && !ai(e, t) && (r = ye(e), me(e, i, a, !0), e = null), t.patchFlag === -2 && (c = !1, t.dynamicChildren = null);
		let { type: l, ref: u, shapeFlag: d } = t;
		switch (l) {
			case Xr:
				y(e, t, n, r);
				break;
			case Zr:
				b(e, t, n, r);
				break;
			case Qr:
				e ?? x(t, n, r, o);
				break;
			case U:
				ie(e, t, n, r, i, a, o, s, c);
				break;
			default: d & 1 ? C(e, t, n, r, i, a, o, s, c) : d & 6 ? O(e, t, n, r, i, a, o, s, c) : (d & 64 || d & 128) && l.process(e, t, n, r, i, a, o, s, c, xe);
		}
		u != null && i ? Kn(u, e && e.ref, a, t || e, !t) : u == null && e && e.ref != null && Kn(e.ref, null, a, e, !0);
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
	}, ee = ({ el: e, anchor: t }, n, r) => {
		let i;
		for (; e && e !== t;) i = h(e), o(e, n, r), e = i;
		o(t, n, r);
	}, S = ({ el: e, anchor: t }) => {
		let n;
		for (; e && e !== t;) n = h(e), s(e), e = n;
		s(t);
	}, C = (e, t, n, r, i, a, o, s, c) => {
		if (t.type === "svg" ? o = "svg" : t.type === "math" && (o = "mathml"), e == null) ne(t, n, r, i, a, o, s, c);
		else {
			let n = e.el && e.el._isVueCE ? e.el : null;
			try {
				n && n._beginPatch(), T(e, t, i, a, o, s, c);
			} finally {
				n && n._endPatch();
			}
		}
	}, ne = (e, t, n, r, i, a, s, u) => {
		let d, f, { props: m, shapeFlag: h, transition: g, dirs: _ } = e;
		if (d = e.el = l(e.type, a, m && m.is, m), h & 8 ? p(d, e.children) : h & 16 && w(e.children, d, null, r, i, Br(e, a), s, u), _ && On(e, null, r, "created"), re(d, e, e.scopeId, s, r), m) {
			for (let e in m) e !== "value" && !te(e) && c(d, e, null, m[e], a, r);
			"value" in m && c(d, "value", null, m.value, a), (f = m.onVnodeBeforeMount) && _i(f, r, e);
		}
		_ && On(e, null, r, "beforeMount");
		let v = Hr(i, g);
		v && g.beforeEnter(d), o(d, t, n), ((f = m && m.onVnodeMounted) || v || _) && H(() => {
			try {
				f && _i(f, r, e), v && g.enter(d), _ && On(e, null, r, "mounted");
			} finally {}
		}, i);
	}, re = (e, t, n, r, i) => {
		if (n && g(e, n), r) for (let t = 0; t < r.length; t++) g(e, r[t]);
		if (i) {
			let n = i.subTree;
			if (t === n || Jr(n.type) && (n.ssContent === t || n.ssFallback === t)) {
				let t = i.vnode;
				re(e, t, t.scopeId, t.slotScopeIds, i.parent);
			}
		}
	}, w = (e, t, n, r, i, a, o, s, c = 0) => {
		for (let l = c; l < e.length; l++) {
			let c = e[l] = s ? mi(e[l]) : pi(e[l]);
			v(null, c, t, n, r, i, a, o, s);
		}
	}, T = (e, n, r, i, a, o, s) => {
		let l = n.el = e.el, { patchFlag: u, dynamicChildren: d, dirs: f } = n;
		u |= e.patchFlag & 16;
		let m = e.props || t, h = n.props || t, g;
		if (r && Vr(r, !1), (g = h.onVnodeBeforeUpdate) && _i(g, r, n, e), f && On(n, e, r, "beforeUpdate"), r && Vr(r, !0), d && (!e.dynamicChildren || e.dynamicChildren.length !== d.length) && (u = 0, s = !1, d = null), (m.innerHTML && h.innerHTML == null || m.textContent && h.textContent == null) && p(l, ""), d ? E(e.dynamicChildren, d, l, r, i, Br(n, a), o) : s || ue(e, n, l, null, r, i, Br(n, a), o, !1), u > 0) {
			if (u & 16) D(l, m, h, r, a);
			else if (u & 2 && m.class !== h.class && c(l, "class", null, h.class, a), u & 4 && c(l, "style", m.style, h.style, a), u & 8) {
				let e = n.dynamicProps;
				for (let t = 0; t < e.length; t++) {
					let n = e[t], i = m[n], o = h[n];
					(o !== i || n === "value") && c(l, n, i, o, a, r);
				}
			}
			u & 1 && e.children !== n.children && p(l, n.children);
		} else !s && d == null && D(l, m, h, r, a);
		((g = h.onVnodeUpdated) || f) && H(() => {
			g && _i(g, r, n, e), f && On(n, e, r, "updated");
		}, i);
	}, E = (e, t, n, r, i, a, o) => {
		for (let s = 0; s < t.length; s++) {
			let c = e[s], l = t[s], u = c.el && (c.type === U || !ai(c, l) || c.shapeFlag & 198) ? m(c.el) : n;
			v(c, l, u, null, r, i, a, o, !0);
		}
	}, D = (e, n, r, i, a) => {
		if (n !== r) {
			if (n !== t) for (let t in n) !te(t) && !(t in r) && c(e, t, n[t], null, a, i);
			for (let t in r) {
				if (te(t)) continue;
				let o = r[t], s = n[t];
				o !== s && t !== "value" && c(e, t, s, o, a, i);
			}
			"value" in r && c(e, "value", n.value, r.value, a);
		}
	}, ie = (e, t, n, r, i, a, s, c, l) => {
		let d = t.el = e ? e.el : u(""), f = t.anchor = e ? e.anchor : u(""), { patchFlag: p, dynamicChildren: m, slotScopeIds: h } = t;
		h && (c = c ? c.concat(h) : h), e == null ? (o(d, n, r), o(f, n, r), w(t.children || [], n, f, i, a, s, c, l)) : p > 0 && p & 64 && m && e.dynamicChildren && e.dynamicChildren.length === m.length ? (E(e.dynamicChildren, m, n, i, a, s, c), (t.key != null || i && t === i.subTree) && Ur(e, t, !0)) : ue(e, t, n, f, i, a, s, c, l);
	}, O = (e, t, n, r, i, a, o, s, c) => {
		t.slotScopeIds = s, e == null ? t.shapeFlag & 512 ? i.ctx.activate(t, n, r, o, c) : oe(t, n, r, i, a, o, c) : se(e, t, c);
	}, oe = (e, t, n, r, i, a, o) => {
		let s = e.component = bi(e, r, i);
		if (Yn(e) && (s.ctx.renderer = xe), Oi(s, !1, o), s.asyncDep) {
			if (i && i.registerDep(s, ce, o), !e.el) {
				let r = s.subTree = Y(Zr);
				b(null, r, t, n), e.placeholder = r.el;
			}
		} else ce(s, e, t, n, i, a, o);
	}, se = (e, t, n) => {
		let r = t.component = e.component;
		if (_r(e, t, n)) {
			if (r.asyncDep && !r.asyncResolved) {
				k(r, t, n);
				return;
			}
			r.next = t, r.update();
		} else t.el = e.el, r.vnode = t;
	}, ce = (e, t, n, r, i, a, o) => {
		let s = () => {
			if (e.isMounted) {
				let { next: t, bu: n, u: r, parent: s, vnode: c } = e;
				{
					let n = Gr(e);
					if (n) {
						t && (t.el = c.el, k(e, t, o)), n.asyncDep.then(() => {
							H(() => {
								e.isUnmounted || l();
							}, i);
						});
						return;
					}
				}
				let u = t, d;
				Vr(e, !1), t ? (t.el = c.el, k(e, t, o)) : t = c, n && ae(n), (d = t.props && t.props.onVnodeBeforeUpdate) && _i(d, s, t, c), Vr(e, !0);
				let f = mr(e), p = e.subTree;
				e.subTree = f, v(p, f, m(p.el), ye(p), e, i, a), t.el = f.el, u === null && br(e, f.el), r && H(r, i), (d = t.props && t.props.onVnodeUpdated) && H(() => _i(d, s, t, c), i);
			} else {
				let o, { el: s, props: c } = t, { bm: l, m: u, parent: d, root: f, type: p } = e, m = Jn(t);
				if (Vr(e, !1), l && ae(l), !m && (o = c && c.onVnodeBeforeMount) && _i(o, d, t), Vr(e, !0), s && j) {
					let t = () => {
						e.subTree = mr(e), j(s, e.subTree, e, i, null);
					};
					m && p.__asyncHydrate ? p.__asyncHydrate(s, e, t) : t();
				} else {
					f.ce && f.ce._hasShadowRoot() && f.ce._injectChildStyle(p, e.parent ? e.parent.type : void 0);
					let o = e.subTree = mr(e);
					v(null, o, n, r, e, i, a), t.el = o.el;
				}
				if (u && H(u, i), !m && (o = c && c.onVnodeMounted)) {
					let e = t;
					H(() => _i(o, d, e), i);
				}
				(t.shapeFlag & 256 || d && Jn(d.vnode) && d.vnode.shapeFlag & 256) && e.a && H(e.a, i), e.isMounted = !0, t = n = r = null;
			}
		};
		e.scope.on();
		let c = e.effect = new ke(s);
		e.scope.off();
		let l = e.update = c.run.bind(c), u = e.job = c.runIfDirty.bind(c);
		u.i = e, u.id = e.uid, c.scheduler = () => _n(u), Vr(e, !0), l();
	}, k = (e, t, n) => {
		t.component = e;
		let r = e.vnode.props;
		e.vnode = t, e.next = null, Tr(e, t.props, r, n), Lr(e, t.children, n), We(), bn(e), Ge();
	}, ue = (e, t, n, r, i, a, o, s, c = !1) => {
		let l = e && e.children, u = e ? e.shapeFlag : 0, d = t.children, { patchFlag: f, shapeFlag: m } = t;
		if (f > 0) {
			if (f & 128) {
				fe(l, d, n, r, i, a, o, s, c);
				return;
			}
			if (f & 256) {
				de(l, d, n, r, i, a, o, s, c);
				return;
			}
		}
		m & 8 ? (u & 16 && ve(l, i, a), d !== l && p(n, d)) : u & 16 ? m & 16 ? fe(l, d, n, r, i, a, o, s, c) : ve(l, i, a, !0) : (u & 8 && p(n, ""), m & 16 && w(d, n, r, i, a, o, s, c));
	}, de = (e, t, r, i, a, o, s, c, l) => {
		e ||= n, t ||= n;
		let u = e.length, d = t.length, f = Math.min(u, d), p = 0;
		for (; p < f; p++) {
			let n = t[p] = l ? mi(t[p]) : pi(t[p]);
			v(e[p], n, r, null, a, o, s, c, l);
		}
		u > d ? ve(e, a, o, !0, !1, f) : w(t, r, i, a, o, s, c, l, f);
	}, fe = (e, t, r, i, a, o, s, c, l) => {
		let u = 0, d = t.length, f = e.length - 1, p = d - 1;
		for (; u <= f && u <= p;) {
			let n = e[u], i = t[u] = l ? mi(t[u]) : pi(t[u]);
			if (ai(n, i)) v(n, i, r, null, a, o, s, c, l);
			else break;
			u++;
		}
		for (; u <= f && u <= p;) {
			let n = e[f], i = t[p] = l ? mi(t[p]) : pi(t[p]);
			if (ai(n, i)) v(n, i, r, null, a, o, s, c, l);
			else break;
			f--, p--;
		}
		if (u > f) {
			if (u <= p) {
				let e = p + 1, n = e < d ? t[e].el : i;
				for (; u <= p;) v(null, t[u] = l ? mi(t[u]) : pi(t[u]), r, n, a, o, s, c, l), u++;
			}
		} else if (u > p) for (; u <= f;) me(e[u], a, o, !0), u++;
		else {
			let m = u, h = u, g = /* @__PURE__ */ new Map();
			for (u = h; u <= p; u++) {
				let e = t[u] = l ? mi(t[u]) : pi(t[u]);
				e.key != null && g.set(e.key, u);
			}
			let _, y = 0, b = p - h + 1, x = !1, ee = 0, S = Array(b);
			for (u = 0; u < b; u++) S[u] = 0;
			for (u = m; u <= f; u++) {
				let n = e[u];
				if (y >= b) {
					me(n, a, o, !0);
					continue;
				}
				let i;
				if (n.key != null) i = g.get(n.key);
				else for (_ = h; _ <= p; _++) if (S[_ - h] === 0 && ai(n, t[_])) {
					i = _;
					break;
				}
				i === void 0 ? me(n, a, o, !0) : (S[i - h] = u + 1, i >= ee ? ee = i : x = !0, v(n, t[i], r, null, a, o, s, c, l), y++);
			}
			let C = x ? Wr(S) : n;
			for (_ = C.length - 1, u = b - 1; u >= 0; u--) {
				let e = h + u, n = t[e], f = t[e + 1], p = e + 1 < d ? f.el || qr(f) : i;
				S[u] === 0 ? v(null, n, r, p, a, o, s, c, l) : x && (_ < 0 || u !== C[_] ? pe(n, r, p, 2) : _--);
			}
		}
	}, pe = (e, t, n, r, i = null) => {
		let { el: a, type: c, transition: l, children: u, shapeFlag: d } = e;
		if (d & 6) {
			pe(e.component.subTree, t, n, r);
			return;
		}
		if (d & 128) {
			e.suspense.move(t, n, r);
			return;
		}
		if (d & 64) {
			c.move(e, t, n, xe);
			return;
		}
		if (c === U) {
			o(a, t, n);
			for (let e = 0; e < u.length; e++) pe(u[e], t, n, r);
			o(e.anchor, t, n);
			return;
		}
		if (c === Qr) {
			ee(e, t, n);
			return;
		}
		if (r !== 2 && d & 1 && l) {
			if (r === 0) l.persisted && !a[Ln] ? o(a, t, n) : (l.beforeEnter(a), o(a, t, n), H(() => l.enter(a), i));
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
	}, me = (e, t, n, r = !1, i = !1) => {
		let { type: a, props: o, ref: s, children: c, dynamicChildren: l, shapeFlag: u, patchFlag: d, dirs: f, cacheIndex: p, memo: m } = e;
		if (d === -2 && (i = !1), s != null && (We(), Kn(s, null, n, e, !0), Ge()), p != null && (t.renderCache[p] = void 0), u & 256) {
			t.ctx.deactivate(e);
			return;
		}
		let h = u & 1 && f, g = !Jn(e), _;
		if (g && (_ = o && o.onVnodeBeforeUnmount) && _i(_, t, e), u & 6) _e(e.component, n, r);
		else {
			if (u & 128) {
				e.suspense.unmount(n, r);
				return;
			}
			h && On(e, null, t, "beforeUnmount"), u & 64 ? e.type.remove(e, t, n, xe, r) : l && !l.hasOnce && (a !== U || d > 0 && d & 64) ? ve(l, t, n, !1, !0) : (a === U && d & 384 || !i && u & 16) && ve(c, t, n), r && he(e);
		}
		let v = m != null && p == null;
		(g && (_ = o && o.onVnodeUnmounted) || h || v) && H(() => {
			_ && _i(_, t, e), h && On(e, null, t, "unmounted"), v && (e.el = null);
		}, n);
	}, he = (e) => {
		let { type: t, el: n, anchor: r, transition: i } = e;
		if (t === U) {
			ge(n, r);
			return;
		}
		if (t === Qr) {
			S(e);
			return;
		}
		let a = () => {
			s(n), i && !i.persisted && i.afterLeave && i.afterLeave();
		};
		if (e.shapeFlag & 1 && i && !i.persisted) {
			let { leave: t, delayLeave: r } = i, o = () => t(n, a);
			r ? r(e.el, a, o) : o();
		} else a();
	}, ge = (e, t) => {
		let n;
		for (; e !== t;) n = h(e), s(e), e = n;
		s(t);
	}, _e = (e, t, n) => {
		let { bum: r, scope: i, job: a, subTree: o, um: s, m: c, a: l } = e;
		Kr(c), Kr(l), r && ae(r), i.stop(), a && (a.flags |= 8, me(o, e, t, n)), s && H(s, t), H(() => {
			e.isUnmounted = !0;
		}, t);
	}, ve = (e, t, n, r = !1, i = !1, a = 0) => {
		for (let o = a; o < e.length; o++) me(e[o], t, n, r, i);
	}, ye = (e) => {
		if (e.shapeFlag & 6) return ye(e.component.subTree);
		if (e.shapeFlag & 128) return e.suspense.next();
		let t = h(e.anchor || e.el), n = t && t[Fn];
		return n ? h(n) : t;
	}, be = !1, A = (e, t, n) => {
		let r;
		e == null ? t._vnode && (me(t._vnode, null, null, !0), r = t._vnode.component) : v(t._vnode || null, e, t, null, null, null, n), t._vnode = e, be ||= (be = !0, bn(r), xn(), !1);
	}, xe = {
		p: v,
		um: me,
		m: pe,
		r: he,
		mt: oe,
		mc: w,
		pc: ue,
		pbc: E,
		n: ye,
		o: e
	}, Se, j;
	return i && ([Se, j] = i(xe)), {
		render: A,
		hydrate: Se,
		createApp: cr(A, Se)
	};
}
function Br({ type: e, props: t }, n) {
	return n === "svg" && e === "foreignObject" || n === "mathml" && e === "annotation-xml" && t && t.encoding && t.encoding.includes("html") ? void 0 : n;
}
function Vr({ effect: e, job: t }, n) {
	n ? (e.flags |= 32, t.flags |= 4) : (e.flags &= -33, t.flags &= -5);
}
function Hr(e, t) {
	return (!e || e && !e.pendingBranch) && t && !t.persisted;
}
function Ur(e, t, n = !1) {
	let r = e.children, i = t.children;
	if (d(r) && d(i)) for (let e = 0; e < r.length; e++) {
		let t = r[e], a = i[e];
		a.shapeFlag & 1 && !a.dynamicChildren && ((a.patchFlag <= 0 || a.patchFlag === 32) && (a = i[e] = mi(i[e]), a.el = t.el), !n && a.patchFlag !== -2 && Ur(t, a)), a.type === Xr && (a.patchFlag === -1 && (a = i[e] = mi(a)), a.el = t.el), a.type === Zr && !a.el && (a.el = t.el);
	}
}
function Wr(e) {
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
function Gr(e) {
	let t = e.subTree.component;
	if (t) return t.asyncDep && !t.asyncResolved ? t : Gr(t);
}
function Kr(e) {
	if (e) for (let t = 0; t < e.length; t++) e[t].flags |= 8;
}
function qr(e) {
	if (e.placeholder) return e.placeholder;
	let t = e.component;
	return t ? qr(t.subTree) : null;
}
var Jr = (e) => e.__isSuspense;
function Yr(e, t) {
	t && t.pendingBranch ? d(e) ? t.effects.push(...e) : t.effects.push(e) : yn(e);
}
var U = /* @__PURE__ */ Symbol.for("v-fgt"), Xr = /* @__PURE__ */ Symbol.for("v-txt"), Zr = /* @__PURE__ */ Symbol.for("v-cmt"), Qr = /* @__PURE__ */ Symbol.for("v-stc"), $r = [], W = null;
function G(e = !1) {
	$r.push(W = e ? null : []);
}
function ei() {
	$r.pop(), W = $r[$r.length - 1] || null;
}
var ti = 1;
function ni(e, t = !1) {
	ti += e, e < 0 && W && t && (W.hasOnce = !0);
}
function ri(e) {
	return e.dynamicChildren = ti > 0 ? W || n : null, ei(), ti > 0 && W && W.push(e), e;
}
function K(e, t, n, r, i, a) {
	return ri(J(e, t, n, r, i, a, !0));
}
function q(e, t, n, r, i) {
	return ri(Y(e, t, n, r, i, !0));
}
function ii(e) {
	return e ? e.__v_isVNode === !0 : !1;
}
function ai(e, t) {
	return e.type === t.type && e.key === t.key;
}
var oi = ({ key: e }) => e ?? null, si = ({ ref: e, ref_key: t, ref_for: n }) => (typeof e == "number" && (e = "" + e), e == null ? null : g(e) || /* @__PURE__ */ L(e) || h(e) ? {
	i: V,
	r: e,
	k: t,
	f: !!n
} : e);
function J(e, t = null, n = null, r = 0, i = null, a = e === U ? 0 : 1, o = !1, s = !1) {
	let c = {
		__v_isVNode: !0,
		__v_skip: !0,
		type: e,
		props: t,
		key: t && oi(t),
		ref: t && si(t),
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
		ctx: V
	};
	return s ? (hi(c, n), a & 128 && e.normalize(c)) : n && (c.shapeFlag |= g(n) ? 8 : 16), ti > 0 && !o && W && (c.patchFlag > 0 || a & 6) && c.patchFlag !== 32 && W.push(c), c;
}
var Y = ci;
function ci(e, t = null, n = null, r = 0, i = null, a = !1) {
	if ((!e || e === er) && (e = Zr), ii(e)) {
		let r = ui(e, t, !0);
		return n && hi(r, n), ti > 0 && !a && W && (r.shapeFlag & 6 ? W[W.indexOf(e)] = r : W.push(r)), r.patchFlag = -2, r;
	}
	if (Fi(e) && (e = e.__vccOpts), t) {
		t = li(t);
		let { class: e, style: n } = t;
		e && !g(e) && (t.class = he(e)), v(n) && (/* @__PURE__ */ Vt(n) && !d(n) && (n = s({}, n)), t.style = ue(n));
	}
	let o = g(e) ? 1 : Jr(e) ? 128 : In(e) ? 64 : v(e) ? 4 : h(e) ? 2 : 0;
	return J(e, t, n, r, i, o, a, !0);
}
function li(e) {
	return e ? /* @__PURE__ */ Vt(e) || Cr(e) ? s({}, e) : e : null;
}
function ui(e, t, n = !1, r = !1) {
	let { props: i, ref: a, patchFlag: o, children: s, transition: c } = e, l = t ? gi(i || {}, t) : i, u = {
		__v_isVNode: !0,
		__v_skip: !0,
		type: e.type,
		props: l,
		key: l && oi(l),
		ref: t && t.ref ? n && a ? d(a) ? a.concat(si(t)) : [a, si(t)] : si(t) : a,
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
		ssContent: e.ssContent && ui(e.ssContent),
		ssFallback: e.ssFallback && ui(e.ssFallback),
		placeholder: e.placeholder,
		el: e.el,
		anchor: e.anchor,
		ctx: e.ctx,
		ce: e.ce
	};
	return c && r && Bn(u, c.clone(u)), u;
}
function di(e = " ", t = 0) {
	return Y(Xr, null, e, t);
}
function fi(e, t) {
	let n = Y(Qr, null, e);
	return n.staticCount = t, n;
}
function X(e = "", t = !1) {
	return t ? (G(), q(Zr, null, e)) : Y(Zr, null, e);
}
function pi(e) {
	return e == null || typeof e == "boolean" ? Y(Zr) : d(e) ? Y(U, null, e.slice()) : ii(e) ? mi(e) : Y(Xr, null, String(e));
}
function mi(e) {
	return e.el === null && e.patchFlag !== -1 || e.memo ? e : ui(e);
}
function hi(e, t) {
	let n = 0, { shapeFlag: r } = e;
	if (t == null) t = null;
	else if (d(t)) n = 16;
	else if (typeof t == "object") {
		if (r & 65) {
			let n = t.default;
			n && (n._c && (n._d = !1), hi(e, n()), n._c && (n._d = !0));
			return;
		}
		{
			n = 32;
			let r = t._;
			!r && !Cr(t) ? t._ctx = V : r === 3 && V && (V.slots._ === 1 ? t._ = 1 : (t._ = 2, e.patchFlag |= 1024));
		}
	} else if (h(t)) {
		if (r & 65) {
			hi(e, { default: t });
			return;
		}
		t = {
			default: t,
			_ctx: V
		}, n = 32;
	} else t = String(t), r & 64 ? (n = 16, t = [di(t)]) : n = 8;
	e.children = t, e.shapeFlag |= n;
}
function gi(...e) {
	let t = {};
	for (let n = 0; n < e.length; n++) {
		let r = e[n];
		for (let e in r) if (e === "class") t.class !== r.class && (t.class = he([t.class, r.class]));
		else if (e === "style") t.style = ue([t.style, r.style]);
		else if (a(e)) {
			let n = t[e], i = r[e];
			i && n !== i && !(d(n) && n.includes(i)) ? t[e] = n ? [].concat(n, i) : i : i == null && n == null && !o(e) && (t[e] = i);
		} else e !== "" && (t[e] = r[e]);
	}
	return t;
}
function _i(e, t, n, r = null) {
	on(e, t, 7, [n, r]);
}
var vi = or(), yi = 0;
function bi(e, n, r) {
	let i = e.type, a = (n ? n.appContext : e.appContext) || vi, o = {
		uid: yi++,
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
		scope: new Te(!0),
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
var Z = null, xi = () => Z || V, Si, Ci;
{
	let e = le(), t = (t, n) => {
		let r;
		return (r = e[t]) || (r = e[t] = []), r.push(n), (e) => {
			r.length > 1 ? r.forEach((t) => t(e)) : r[0](e);
		};
	};
	Si = t("__VUE_INSTANCE_SETTERS__", (e) => Z = e), Ci = t("__VUE_SSR_SETTERS__", (e) => Di = e);
}
var wi = (e) => {
	let t = Z;
	return Si(e), e.scope.on(), () => {
		e.scope.off(), Si(t);
	};
}, Ti = () => {
	Z && Z.scope.off(), Si(null);
};
function Ei(e) {
	return e.vnode.shapeFlag & 4;
}
var Di = !1;
function Oi(e, t = !1, n = !1) {
	t && Ci(t);
	let { props: r, children: i } = e.vnode, a = Ei(e);
	wr(e, r, a, t), Ir(e, i, n || t);
	let o = a ? ki(e, t) : void 0;
	return t && Ci(!1), o;
}
function ki(e, t) {
	let n = e.type;
	e.accessCache = /* @__PURE__ */ Object.create(null), e.proxy = new Proxy(e.ctx, ar);
	let { setup: r } = n;
	if (r) {
		We();
		let n = e.setupContext = r.length > 1 ? Ni(e) : null, i = wi(e), a = an(r, e, 0, [e.props, n]), o = y(a);
		if (Ge(), i(), (o || e.sp) && !Jn(e) && Un(e), o) {
			if (a.then(Ti, Ti), t) return a.then((n) => {
				Ci(!0);
				try {
					Ai(e, n, t);
				} finally {
					Ci(!1);
				}
			}).catch((t) => {
				sn(t, e, 0);
			});
			e.asyncDep = a;
		} else Ai(e, a, t);
	} else ji(e, t);
}
function Ai(e, t, n) {
	h(t) ? e.type.__ssrInlineRender ? e.ssrRender = t : e.render = t : v(t) && (e.setupState = Yt(t)), ji(e, n);
}
function ji(e, t, n) {
	let i = e.type;
	e.render ||= i.render || r;
}
var Mi = { get(e, t) {
	return P(e, "get", ""), e[t];
} };
function Ni(e) {
	return {
		attrs: new Proxy(e.attrs, Mi),
		slots: e.slots,
		emit: e.emit,
		expose: (t) => {
			e.exposed = t || {};
		}
	};
}
function Pi(e) {
	return e.exposed ? e.exposeProxy ||= new Proxy(Yt(Ht(e.exposed)), {
		get(t, n) {
			if (n in t) return t[n];
			if (n in rr) return rr[n](e);
		},
		has(e, t) {
			return t in e || t in rr;
		}
	}) : e.proxy;
}
function Fi(e) {
	return h(e) && "__vccOpts" in e;
}
var Q = (e, t) => /* @__PURE__ */ Zt(e, t, Di), Ii = "3.5.42", Li = void 0, Ri = typeof window < "u" && window.trustedTypes;
if (Ri) try {
	Li = /* @__PURE__ */ Ri.createPolicy("vue", { createHTML: (e) => e });
} catch {}
var zi = Li ? (e) => Li.createHTML(e) : (e) => e, Bi = "http://www.w3.org/2000/svg", Vi = "http://www.w3.org/1998/Math/MathML", Hi = typeof document < "u" ? document : null, Ui = Hi && /* @__PURE__ */ Hi.createElement("template"), Wi = {
	insert: (e, t, n) => {
		t.insertBefore(e, n || null);
	},
	remove: (e) => {
		let t = e.parentNode;
		t && t.removeChild(e);
	},
	createElement: (e, t, n, r) => {
		let i = t === "svg" ? Hi.createElementNS(Bi, e) : t === "mathml" ? Hi.createElementNS(Vi, e) : n ? Hi.createElement(e, { is: n }) : Hi.createElement(e);
		return e === "select" && r && r.multiple != null && i.setAttribute("multiple", r.multiple), i;
	},
	createText: (e) => Hi.createTextNode(e),
	createComment: (e) => Hi.createComment(e),
	setText: (e, t) => {
		e.nodeValue = t;
	},
	setElementText: (e, t) => {
		e.textContent = t;
	},
	parentNode: (e) => e.parentNode,
	nextSibling: (e) => e.nextSibling,
	querySelector: (e) => Hi.querySelector(e),
	setScopeId(e, t) {
		e.setAttribute(t, "");
	},
	insertStaticContent(e, t, n, r, i, a) {
		let o = n ? n.previousSibling : t.lastChild;
		if (i && (i === a || i.nextSibling)) for (; t.insertBefore(i.cloneNode(!0), n), i !== a && (i = i.nextSibling););
		else {
			Ui.innerHTML = zi(r === "svg" ? `<svg>${e}</svg>` : r === "mathml" ? `<math>${e}</math>` : e);
			let i = Ui.content;
			if (r === "svg" || r === "mathml") {
				let e = i.firstChild;
				for (; e.firstChild;) i.appendChild(e.firstChild);
				i.removeChild(e);
			}
			t.insertBefore(i, n);
		}
		return [o ? o.nextSibling : t.firstChild, n ? n.previousSibling : t.lastChild];
	}
}, Gi = /* @__PURE__ */ Symbol("_vtc");
function Ki(e, t, n) {
	let r = e[Gi];
	r && (t = (t ? [t, ...r] : [...r]).join(" ")), t == null ? e.removeAttribute("class") : n ? e.setAttribute("class", t) : e.className = t;
}
var qi = /* @__PURE__ */ Symbol("_vod"), Ji = /* @__PURE__ */ Symbol("_vsh"), Yi = /* @__PURE__ */ Symbol(""), Xi = /(?:^|;)\s*display\s*:/;
function Zi(e, t, n) {
	let r = e.style, i = g(n), a = !1;
	if (n && !i) {
		if (t) {
			if (g(t)) for (let e of t.split(";")) {
				let t = e.slice(0, e.indexOf(":")).trim();
				n[t] ?? $i(r, t, "");
			}
			else for (let e in t) n[e] ?? $i(r, e, "");
		}
		for (let i in n) {
			i === "display" && (a = !0);
			let o = n[i];
			o == null ? $i(r, i, "") : ra(e, i, !g(t) && t ? t[i] : void 0, o) || $i(r, i, o);
		}
	} else if (i) {
		if (t !== n) {
			let e = r[Yi];
			e && (n += ";" + e), r.cssText = n, a = Xi.test(n);
		}
	} else t && e.removeAttribute("style");
	qi in e && (e[qi] = a ? r.display : "", e[Ji] && (r.display = "none"));
}
var Qi = /\s*!important$/;
function $i(e, t, n) {
	if (d(n)) n.forEach((n) => $i(e, t, n));
	else if (n ??= "", t.startsWith("--")) Qi.test(n) ? e.setProperty(t, n.replace(Qi, ""), "important") : e.setProperty(t, n);
	else {
		let r = na(e, t);
		Qi.test(n) ? e.setProperty(E(r), n.replace(Qi, ""), "important") : e[r] = n;
	}
}
var ea = [
	"Webkit",
	"Moz",
	"ms"
], ta = {};
function na(e, t) {
	let n = ta[t];
	if (n) return n;
	let r = w(t);
	if (r !== "filter" && r in e) return ta[t] = r;
	r = D(r);
	for (let n = 0; n < ea.length; n++) {
		let i = ea[n] + r;
		if (i in e) return ta[t] = i;
	}
	return t;
}
function ra(e, t, n, r) {
	return e.tagName === "TEXTAREA" && (t === "width" || t === "height") && g(r) && n === r;
}
var ia = "http://www.w3.org/1999/xlink";
function aa(e, t, n, r, i, a = _e(t)) {
	r && t.startsWith("xlink:") ? n == null ? e.removeAttributeNS(ia, t.slice(6, t.length)) : e.setAttributeNS(ia, t, n) : n == null || a && !ve(n) ? e.removeAttribute(t) : e.setAttribute(t, a ? "" : _(n) ? String(n) : n);
}
function oa(e, t, n, r, i) {
	if (t === "innerHTML" || t === "textContent") {
		n != null && (e[t] = t === "innerHTML" ? zi(n) : n);
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
		r === "boolean" ? n = ve(n) : n == null && r === "string" ? (n = "", o = !0) : r === "number" && (n = 0, o = !0);
	}
	try {
		e[t] = n;
	} catch {}
	o && e.removeAttribute(i || t);
}
function sa(e, t, n, r) {
	e.addEventListener(t, n, r);
}
function ca(e, t, n, r) {
	e.removeEventListener(t, n, r);
}
var la = /* @__PURE__ */ Symbol("_vei");
function ua(e, t, n, r, i = null) {
	let a = e[la] || (e[la] = {}), o = a[t];
	if (r && o) o.value = r;
	else {
		let [n, s] = pa(t);
		r ? sa(e, n, a[t] = _a(r, i), s) : o && (ca(e, n, o, s), a[t] = void 0);
	}
}
var da = /(Once|Passive|Capture)$/, fa = /^on:?(?:Once|Passive|Capture)$/;
function pa(e) {
	let t, n;
	for (; (n = e.match(da)) && !fa.test(e);) t ||= {}, e = e.slice(0, e.length - n[1].length), t[n[1].toLowerCase()] = !0;
	return [e[2] === ":" ? e.slice(3) : E(e.slice(2)), t];
}
var ma = 0, ha = /* @__PURE__ */ Promise.resolve(), ga = () => ma ||= (ha.then(() => ma = 0), Date.now());
function _a(e, t) {
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
				e && on(e, t, 5, a);
			}
		} else on(r, t, 5, [e]);
	};
	return n.value = e, n.attached = ga(), n;
}
var va = (e) => e.charCodeAt(0) === 111 && e.charCodeAt(1) === 110 && e.charCodeAt(2) > 96 && e.charCodeAt(2) < 123, ya = (e, t, n, r, i, s) => {
	let c = i === "svg";
	t === "class" ? Ki(e, r, c) : t === "style" ? Zi(e, n, r) : a(t) ? o(t) || ua(e, t, n, r, s) : (t[0] === "." ? (t = t.slice(1), 1) : t[0] === "^" ? (t = t.slice(1), 0) : ba(e, t, r, c)) ? (oa(e, t, r), !e.tagName.includes("-") && (t === "value" || t === "checked" || t === "selected") && aa(e, t, r, c, s, t !== "value")) : e._isVueCE && (xa(e, t) || e._def.__asyncLoader && (/[A-Z]/.test(t) || !g(r))) ? oa(e, w(t), r, s, t) : (t === "true-value" ? e._trueValue = r : t === "false-value" && (e._falseValue = r), aa(e, t, r, c));
};
function ba(e, t, n, r) {
	if (r) return !!(t === "innerHTML" || t === "textContent" || t in e && va(t) && h(n));
	if (t === "spellcheck" || t === "draggable" || t === "translate" || t === "autocorrect" || t === "sandbox" && e.tagName === "IFRAME" || t === "form" || t === "list" && e.tagName === "INPUT" || t === "type" && e.tagName === "TEXTAREA") return !1;
	if (t === "width" || t === "height") {
		let t = e.tagName;
		if (t === "IMG" || t === "VIDEO" || t === "CANVAS" || t === "SOURCE") return !1;
	}
	return va(t) && g(n) ? !1 : t in e;
}
function xa(e, t) {
	let n = e._def.props;
	if (!n) return !1;
	let r = w(t);
	return Array.isArray(n) ? n.some((e) => w(e) === r) : Object.keys(n).some((e) => w(e) === r);
}
var Sa = {};
// @__NO_SIDE_EFFECTS__
function Ca(e, t, n) {
	let r = /* @__PURE__ */ Vn(e, t);
	S(r) && (r = s({}, r, t));
	class i extends Ta {
		constructor(e) {
			super(r, e, n);
		}
	}
	return i.def = r, i;
}
var wa = typeof HTMLElement < "u" ? HTMLElement : class {}, Ta = class e extends wa {
	constructor(e, t = {}, n = Za) {
		super(), this._def = e, this._props = t, this._createApp = n, this._isVueCE = !0, this._instance = null, this._app = null, this._nonce = this._def.nonce, this._connected = !1, this._resolved = !1, this._patching = !1, this._dirty = !1, this._numberProps = null, this._styleChildren = /* @__PURE__ */ new WeakSet(), this._styleAnchors = /* @__PURE__ */ new WeakMap(), this._ob = null, this.shadowRoot && n !== Za ? this._root = this.shadowRoot : e.shadowRoot === !1 ? this._root = this : (this.attachShadow(s({}, e.shadowRootOptions, { mode: "open" })), this._root = this.shadowRoot);
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
		this._connected = !1, hn(() => {
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
				(t === Number || t && t.type === Number) && (e in this._props && (this._props[e] = ce(this._props[e])), (i ||= /* @__PURE__ */ Object.create(null))[w(e)] = !0);
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
		for (let e of n.map(w)) Object.defineProperty(this, e, {
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
		let t = this.hasAttribute(e), n = t ? this.getAttribute(e) : Sa, r = w(e);
		t && this._numberProps && this._numberProps[r] && (n = ce(n)), this._setProp(r, n, !1, !0);
	}
	_getProp(e) {
		return this._props[e];
	}
	_setProp(e, t, n = !0, r = !1) {
		if (t !== this._props[e] && (this._dirty = !0, t === Sa ? delete this._props[e] : (this._props[e] = t, e === "key" && this._app && (this._app._ceVNode.key = t)), r && this._instance && this._update(), n)) {
			let n = this._ob;
			n && (this._processMutations(n.takeRecords()), n.disconnect()), t === !0 ? this.setAttribute(E(e), "") : typeof t == "string" || typeof t == "number" ? this.setAttribute(E(e), t + "") : t || this.removeAttribute(E(e)), n && n.observe(this, { attributes: !0 });
		}
	}
	_update() {
		let e = this._createVNode();
		this._app && (e.appContext = this._app._context), Xa(e, this._root);
	}
	_createVNode() {
		let e = {};
		this.shadowRoot || (e.onVnodeMounted = e.onVnodeUpdated = this._renderSlots.bind(this));
		let t = Y(this._def, s(e, this._props));
		return this._instance || (t.ce = (e) => {
			this._instance = e, e.ce = this, e.isCE = !0;
			let t = (e, t) => {
				this.dispatchEvent(new CustomEvent(e, S(t[0]) ? s({ detail: t }, t[0]) : { detail: t }));
			};
			e.emit = (e, ...n) => {
				t(e, n), E(e) !== e && t(E(e), n);
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
function Ea(e) {
	let t = xi();
	return t && t.ce || null;
}
var Da = (e) => {
	let t = e.props["onUpdate:modelValue"] || !1;
	return d(t) ? (e) => ae(t, e) : t;
};
function Oa(e) {
	e.target.composing = !0;
}
function ka(e) {
	let t = e.target;
	t.composing && (t.composing = !1, t.dispatchEvent(new Event("input")));
}
var $ = /* @__PURE__ */ Symbol("_assign"), Aa = /* @__PURE__ */ Symbol("_initialValue");
function ja(e, t, n) {
	return t && (e = e.trim()), n && (e = se(e)), e;
}
var Ma = {
	created(e, { modifiers: { lazy: t, trim: n, number: r } }, i) {
		e.parentNode && (e.type === "text" ? e[Aa] = e.defaultValue.replace(/[\r\n]/g, "") : e.type === "textarea" && (e[Aa] = e.defaultValue.replace(/\r\n?/g, "\n"))), e[$] = Da(i);
		let a = r || i.props && i.props.type === "number";
		sa(e, t ? "change" : "input", (t) => {
			t.target.composing || e[$](ja(e.value, n, a));
		}), (n || a) && sa(e, "change", () => {
			e.value = ja(e.value, n, a);
		}), t || (sa(e, "compositionstart", Oa), sa(e, "compositionend", ka), sa(e, "change", ka));
	},
	mounted(e, { value: t, modifiers: { trim: n, number: r } }) {
		let i = t ?? "", a = e[Aa];
		delete e[Aa], a !== void 0 && (e.type === "text" || e.type === "textarea") && e.value !== a ? e[$](ja(e.value, n, r)) : e.value = i;
	},
	beforeUpdate(e, { value: t, oldValue: n, modifiers: { lazy: r, trim: i, number: a } }, o) {
		if (e[$] = Da(o), e.composing) return;
		let s = (a || e.type === "number") && !/^0\d/.test(e.value) ? se(e.value) : e.value, c = t ?? "";
		if (s === c) return;
		let l = e.getRootNode();
		(l instanceof Document || l instanceof ShadowRoot) && l.activeElement === e && e.type !== "range" && (r && t === n || i && e.value.trim() === c) || (e.value = c);
	}
}, Na = {
	deep: !0,
	created(e, t, n) {
		e[$] = Da(n), sa(e, "change", () => {
			let t = e._modelValue, n = za(e), r = e.checked, i = e[$];
			if (d(t)) {
				let e = xe(t, n), a = e !== -1;
				if (r && !a) i(t.concat(n));
				else if (!r && a) {
					let n = [...t];
					n.splice(e, 1), i(n);
				}
			} else if (p(t)) {
				let e = new Set(t);
				r ? e.add(n) : e.delete(n), i(e);
			} else i(Ba(e, r));
		});
	},
	mounted: Pa,
	beforeUpdate(e, t, n) {
		e[$] = Da(n), Pa(e, t, n);
	}
};
function Pa(e, { value: t, oldValue: n }, r) {
	e._modelValue = t;
	let i;
	if (d(t)) i = xe(t, r.props.value) > -1;
	else if (p(t)) i = t.has(r.props.value);
	else {
		if (t === n) return;
		i = A(t, Ba(e, !0));
	}
	e.checked !== i && (e.checked = i);
}
var Fa = {
	created(e, { value: t }, n) {
		e.checked = A(t, n.props.value), e[$] = Da(n), sa(e, "change", () => {
			e[$](za(e));
		});
	},
	beforeUpdate(e, { value: t, oldValue: n }, r) {
		e[$] = Da(r), t !== n && (e.checked = A(t, r.props.value));
	}
}, Ia = {
	deep: !0,
	created(e, { value: t, modifiers: { number: n } }, r) {
		e._modelValue = t, sa(e, "change", () => {
			let t = Array.prototype.filter.call(e.options, (e) => e.selected).map((e) => n ? se(za(e)) : za(e)), r = e.multiple, i = r ? p(e._modelValue) ? new Set(t) : t : t[0], a = e._pendingValue = [r, r ? d(i) ? t.slice() : t : i];
			try {
				e[$](i);
			} finally {
				hn(() => {
					e._pendingValue === a && (e._pendingValue = void 0);
				});
			}
		}), e[$] = Da(r);
	},
	mounted(e, { value: t }) {
		Ra(e, t);
	},
	beforeUpdate(e, { value: t }, n) {
		e._modelValue = t, e[$] = Da(n);
	},
	updated(e, { value: t }) {
		let n = e._pendingValue;
		e._pendingValue = void 0, (!n || n[0] !== e.multiple || !La(t, n[1], n[0])) && Ra(e, t);
	}
};
function La(e, t, n) {
	if (!n || d(e)) return A(e, t);
	if (p(e)) {
		if (e.size !== t.length) return !1;
		for (let n of t) if (!e.has(n)) return !1;
		return !0;
	}
	return !1;
}
function Ra(e, t) {
	let n = e.multiple, r = d(t);
	if (!n || r || p(t)) {
		for (let i = 0, a = e.options.length; i < a; i++) {
			let a = e.options[i], o = za(a);
			if (n) {
				if (r) {
					let e = typeof o;
					a.selected = e === "string" || e === "number" ? t.some((e) => String(e) === String(o)) : xe(t, o) > -1;
				} else a.selected = t.has(o);
			} else if (A(za(a), t)) {
				e.selectedIndex !== i && (e.selectedIndex = i);
				return;
			}
		}
		!n && e.selectedIndex !== -1 && (e.selectedIndex = -1);
	}
}
function za(e) {
	return "_value" in e ? e._value : e.value;
}
function Ba(e, t) {
	let n = t ? "_trueValue" : "_falseValue";
	return n in e ? e[n] : t;
}
var Va = {
	created(e, t, n) {
		Ua(e, t, n, null, "created");
	},
	mounted(e, t, n) {
		Ua(e, t, n, null, "mounted");
	},
	beforeUpdate(e, t, n, r) {
		Ua(e, t, n, r, "beforeUpdate");
	},
	updated(e, t, n, r) {
		Ua(e, t, n, r, "updated");
	}
};
function Ha(e, t) {
	switch (e) {
		case "SELECT": return Ia;
		case "TEXTAREA": return Ma;
		default: switch (t) {
			case "checkbox": return Na;
			case "radio": return Fa;
			default: return Ma;
		}
	}
}
function Ua(e, t, n, r, i) {
	let a = Ha(e.tagName, n.props && n.props.type)[i];
	a && a(e, t, n, r);
}
var Wa = [
	"ctrl",
	"shift",
	"alt",
	"meta"
], Ga = {
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
	exact: (e, t) => Wa.some((n) => e[`${n}Key`] && !t.includes(n))
}, Ka = (e, t) => {
	if (!e) return e;
	let n = e._withMods ||= {}, r = t.join(".");
	return n[r] || (n[r] = ((n, ...r) => {
		for (let e = 0; e < t.length; e++) {
			let r = Ga[t[e]];
			if (r && r(n, t)) return;
		}
		return e(n, ...r);
	}));
}, qa = /* @__PURE__ */ s({ patchProp: ya }, Wi), Ja;
function Ya() {
	return Ja ||= Rr(qa);
}
var Xa = ((...e) => {
	Ya().render(...e);
}), Za = ((...e) => {
	let t = Ya().createApp(...e), { mount: n } = t;
	return t.mount = (e) => {
		let r = $a(e);
		if (!r) return;
		let i = t._component;
		!h(i) && !i.render && !i.template && (i.template = r.innerHTML), r.nodeType === 1 && (r.textContent = "");
		let a = n(r, !1, Qa(r));
		return r instanceof Element && (r.removeAttribute("v-cloak"), r.setAttribute("data-v-app", "")), a;
	}, t;
});
function Qa(e) {
	if (e instanceof SVGElement) return "svg";
	if (typeof MathMLElement == "function" && e instanceof MathMLElement) return "mathml";
}
function $a(e) {
	return g(e) ? document.querySelector(e) : e;
}
//#endregion
//#region src/tabs.ts
var eo = [
	{
		path: "allgemein",
		de: "Allgemeine Informationen",
		en: "General information"
	},
	{
		path: "ladeautomatik",
		de: "Ladeautomatik",
		en: "Scheduled charging"
	},
	{
		path: "netzdienliches-laden",
		de: "Netzdienliches Laden",
		en: "Grid-serving charging"
	},
	{
		path: "dynamisches-laden",
		de: "Dynamisches Laden",
		en: "Dynamic charging"
	},
	{
		path: "ersparnis",
		de: "Ersparnis",
		en: "Savings"
	}
];
function to(e, t) {
	let n = e.split(/[?#]/, 1)[0].replace(/\/+$/, "");
	return (n.startsWith(`${t}/`) ? n.slice(t.length) : n === t ? "" : n).replace(/^\//, "") || eo[0].path;
}
var no = {
	de: {
		navigation: "Dashboard-Bereiche",
		menu: "Seitenleiste öffnen",
		preview: "Vorschau",
		introduction: "Dieses Dashboard zeigt dieselben Gerätewerte und Einstellungen wie Ihre bisherige Ansicht.",
		introductionStandalone: "Gerätewerte, Ladeeinstellungen und Ersparnis Ihres SAX-Power-Speichers.",
		existing: "Bestehendes Dashboard öffnen",
		loading: "Home Assistant wird geladen …",
		missingEntry: "Diesem Dashboard ist noch kein SAX-Power-Gerät zugeordnet. Bitte laden Sie die Integration neu.",
		notFound: "Bereich nicht gefunden",
		notFoundDescription: "Dieser Dashboard-Bereich ist nicht verfügbar. Wählen Sie einen der oben angezeigten Bereiche.",
		returnToOverview: "Zur Übersicht"
	},
	en: {
		navigation: "Dashboard sections",
		menu: "Open sidebar",
		preview: "Preview",
		introduction: "This dashboard shows the same device values and settings as your existing dashboard.",
		introductionStandalone: "Device values, charging settings and savings for your SAX Power battery.",
		existing: "Open existing dashboard",
		loading: "Loading Home Assistant …",
		missingEntry: "No SAX Power device is assigned to this dashboard yet. Please reload the integration.",
		notFound: "Section not found",
		notFoundDescription: "This dashboard section is unavailable. Choose one of the sections above.",
		returnToOverview: "Back to overview"
	}
}, ro = {
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
}, io = Symbol("sax-dashboard");
function ao(e, t, n, r, i) {
	let a = ro[r];
	if (!i || !n || n.state === "unavailable") return a.unavailable;
	if (n.state === "unknown") return a.unknown;
	if (e?.formatEntityState) return e.formatEntityState(n);
	if (t.states[n.state]) return t.states[n.state];
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
function oo(e, t) {
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
		case "time": return typeof t != "string" || !/^([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(t) ? null : {
			service: "set_value",
			data: { time: t.length === 5 ? `${t}:00` : t }
		};
		case "select": return typeof t == "string" && Array.isArray(n.options) && n.options.includes(t) ? {
			service: "select_option",
			data: { option: t }
		} : null;
		default: return null;
	}
}
function so(e, t) {
	let n = Q(() => e()?.language.toLowerCase().startsWith("de") ? "de" : "en"), r = /* @__PURE__ */ R(!1), i = /* @__PURE__ */ R(!1), a = /* @__PURE__ */ R(null), o = Q(() => a.value ? ro[n.value][a.value] : null), s = /* @__PURE__ */ Gt([]), c = /* @__PURE__ */ Ft(/* @__PURE__ */ new Map()), l = /* @__PURE__ */ Ft(/* @__PURE__ */ new Map()), u = (e, n) => JSON.stringify([
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
	De(() => {
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
			displayValue: ao(o, a, d, n.value, i.value),
			canControl: f && a.can_control && !!o?.callService,
			pending: p?.pending ?? !1,
			error: p?.error ? ro[n.value][p.error] : null
		};
	}
	async function h(t, n, i) {
		let a = m(t, n);
		if (!a || a.pending) return !1;
		let o = /* @__PURE__ */ Ft({
			pending: !1,
			error: null
		});
		c.set(a.metadata.entity_id, o);
		let s = e();
		if (!a.canControl || !s?.callService || !r.value) return o.error = "forbidden", !1;
		let f = oo(a, i);
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
	return {
		language: n,
		ready: /* @__PURE__ */ Lt(r),
		connected: /* @__PURE__ */ Lt(i),
		error: o,
		entity: m,
		perform: h
	};
}
//#endregion
//#region src/components/EntityControl.vue?vue&type=script&setup=true&lang.ts
var co = ["aria-busy"], lo = { class: "entity-control__description" }, uo = { class: "entity-control__input" }, fo = [
	"checked",
	"disabled",
	"aria-describedby"
], po = [
	"value",
	"disabled",
	"aria-describedby"
], mo = {
	key: 0,
	value: "",
	disabled: ""
}, ho = ["value"], go = [
	"type",
	"min",
	"max",
	"step",
	"disabled",
	"aria-describedby"
], _o = ["disabled"], vo = {
	key: 0,
	class: "entity-control__error",
	role: "alert"
}, yo = {
	key: 1,
	role: "status"
}, bo = /*@__PURE__*/ Vn({
	__name: "EntityControl",
	props: {
		domain: { type: String },
		entityKey: { type: String }
	},
	setup(e) {
		let t = e, n = An(io), r = Q(() => n?.entity(t.domain, t.entityKey)), i = Hn(), a = `sax-control-${i}`, o = `sax-status-${i}`, s = `sax-value-${i}`, c = /* @__PURE__ */ R(""), l = Q(() => r.value?.state?.state ?? ""), u = Q(() => r.value?.state?.attributes ?? {}), d = Q(() => {
			let e = u.value.options;
			return Array.isArray(e) ? e.filter((e) => typeof e == "string") : [];
		}), f = Q(() => n?.language.value ?? "en"), p = Q(() => f.value === "de" ? {
			apply: "Übernehmen",
			confirmed: "Bestätigter Wert",
			disconnected: "Keine Verbindung zu Home Assistant",
			unavailable: "Nicht verfügbar",
			readOnly: "Keine Berechtigung zum Ändern",
			pending: "Änderung wird an Home Assistant gesendet …"
		} : {
			apply: "Apply",
			confirmed: "Confirmed value",
			disconnected: "Disconnected from Home Assistant",
			unavailable: "Unavailable",
			readOnly: "You do not have permission to change this setting",
			pending: "Sending change to Home Assistant …"
		}), m = Q(() => !r.value?.canControl || r.value.pending), h = Q(() => n?.connected.value ? r.value?.available ? r.value.metadata.can_control ? r.value.pending ? p.value.pending : "" : p.value.readOnly : p.value.unavailable : p.value.disconnected);
		function g(e) {
			return r.value?.available ? e : "";
		}
		Nn([() => r.value?.metadata.entity_id, () => l.value], ([, e]) => {
			c.value = g(e);
		}, { immediate: !0 });
		function _(e) {
			let t = u.value[e];
			return typeof t == "number" && Number.isFinite(t) ? t : void 0;
		}
		function v(e) {
			return r.value?.metadata.states[e] ?? e;
		}
		async function y() {
			!m.value && n && await n.perform(t.domain, t.entityKey, c.value);
		}
		async function b(e) {
			let r = e.target, i = r.checked;
			r.checked = l.value === "on", !m.value && n && await n.perform(t.domain, t.entityKey, i);
		}
		async function x(e) {
			let r = e.target, i = r.value;
			r.value = l.value, !m.value && n && await n.perform(t.domain, t.entityKey, i);
		}
		return (t, n) => r.value ? (G(), K("form", {
			key: 0,
			class: "entity-control",
			"aria-busy": r.value.pending,
			onSubmit: Ka(y, ["prevent"])
		}, [
			J("div", lo, [J("label", {
				for: a,
				class: "entity-control__name"
			}, j(r.value.name), 1), J("p", {
				id: s,
				class: "entity-control__value"
			}, [J("span", null, j(p.value.confirmed) + ":", 1), di(" " + j(r.value.displayValue), 1)])]),
			J("div", uo, [e.domain === "switch" ? (G(), K("input", {
				key: 0,
				id: a,
				type: "checkbox",
				role: "switch",
				checked: l.value === "on",
				disabled: m.value,
				"aria-describedby": `${s} ${o}`,
				onChange: b
			}, null, 40, fo)) : e.domain === "select" ? (G(), K("select", {
				key: 1,
				id: a,
				value: r.value.available ? l.value : "",
				disabled: m.value,
				"aria-describedby": `${s} ${o}`,
				onChange: x
			}, [r.value.available ? X("", !0) : (G(), K("option", mo, j(p.value.unavailable), 1)), (G(!0), K(U, null, tr(d.value, (e) => (G(), K("option", {
				key: e,
				value: e
			}, j(v(e)), 9, ho))), 128))], 40, po)) : (G(), K(U, { key: 2 }, [Dn(J("input", {
				id: a,
				"onUpdate:modelValue": n[0] ||= (e) => c.value = e,
				type: e.domain === "number" ? "number" : "time",
				min: e.domain === "number" ? _("min") : void 0,
				max: e.domain === "number" ? _("max") : void 0,
				step: e.domain === "number" ? _("step") : 1,
				disabled: m.value,
				"aria-describedby": `${s} ${o}`,
				required: ""
			}, null, 8, go), [[Va, c.value]]), J("button", {
				type: "submit",
				disabled: m.value || c.value === ""
			}, j(p.value.apply), 9, _o)], 64))]),
			J("div", {
				id: o,
				class: "entity-control__feedback"
			}, [r.value.error ? (G(), K("p", vo, j(r.value.error), 1)) : h.value ? (G(), K("p", yo, j(h.value), 1)) : X("", !0)])
		], 40, co)) : X("", !0);
	}
}), xo = ".entity-control{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));color:var(--primary-text-color,#212121);box-shadow:var(--ha-card-box-shadow,none);flex-wrap:wrap;align-items:center;gap:12px 24px;padding:20px;display:flex}.entity-control__description{overflow-wrap:anywhere;flex:200px;min-width:0}.entity-control__name{font-weight:500;line-height:1.5;display:block}.entity-control__value{color:var(--secondary-text-color,#666);margin:4px 0 0;font-size:.9em;line-height:1.5}.entity-control__input{flex-wrap:wrap;align-items:center;gap:8px;max-width:100%;display:flex}.entity-control input,.entity-control select,.entity-control button{border:1px solid var(--divider-color,#767676);max-width:100%;min-height:44px;color:inherit;background:var(--card-background-color,#fff);font:inherit;border-radius:6px;padding:8px 12px}.entity-control input[type=number]{width:120px}.entity-control input[type=checkbox]{width:28px;accent-color:var(--primary-color,#03a9f4);cursor:pointer;margin:0 8px}.entity-control button{border-color:var(--primary-color,#03a9f4);color:var(--primary-text-color,#212121);cursor:pointer}.entity-control :disabled{cursor:not-allowed;opacity:.6}.entity-control input:focus-visible,.entity-control select:focus-visible,.entity-control button:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.entity-control__feedback{color:var(--secondary-text-color,#666);flex-basis:100%;line-height:1.5}.entity-control__feedback:empty{display:none}.entity-control__feedback p{margin:0}.entity-control__error{color:var(--error-color,#b71c1c)}", So = (e, t) => {
	let n = e.__vccOpts || e;
	for (let [e, r] of t) n[e] = r;
	return n;
}, Co = /*#__PURE__*/ So(bo, [["styles", [xo]]]), wo = [
	"role",
	"aria-labelledby",
	"aria-valuemin",
	"aria-valuemax",
	"aria-valuenow",
	"aria-valuetext"
], To = {
	viewBox: "0 0 240 124",
	"aria-hidden": "true"
}, Eo = ["stroke-dasharray", "stroke-dashoffset"], Do = ["transform"], Oo = {
	class: "entity-gauge__scale",
	"aria-hidden": "true"
}, ko = { class: "entity-gauge__value" }, Ao = {
	key: 0,
	class: "entity-gauge__range"
}, jo = /*#__PURE__*/ So(/* @__PURE__ */ Vn({
	__name: "EntityGauge",
	props: {
		entityKey: { type: String },
		maximum: { type: Number },
		segments: { type: Array }
	},
	setup(e) {
		let t = e, n = An(io), r = Q(() => n?.entity("sensor", t.entityKey)), i = `sax-gauge-${Hn()}`, a = Q(() => {
			let e = r.value?.state?.state.trim();
			if (!r.value?.available || !e) return null;
			let t = Number(e);
			return Number.isFinite(t) ? t : null;
		}), o = Q(() => a.value === null ? null : Math.max(0, Math.min(t.maximum, a.value))), s = Q(() => a.value === null ? null : [...t.segments].reverse().find((e) => a.value >= e.from)?.label ?? t.segments[0]?.label), c = Q(() => r.value?.available && a.value === null ? n?.language.value === "de" ? "Unbekannt" : "Unknown" : r.value?.displayValue), l = Q(() => t.segments.map((e, n) => ({
			...e,
			offset: -(e.from / t.maximum) * 100,
			length: ((t.segments[n + 1]?.from ?? t.maximum) - e.from) / t.maximum * 100
		})));
		return (t, n) => r.value ? (G(), K("section", {
			key: 0,
			class: "entity-gauge",
			"aria-labelledby": i
		}, [J("h2", { id: i }, j(r.value.name), 1), J("div", {
			class: "entity-gauge__meter",
			role: o.value === null ? void 0 : "meter",
			"aria-labelledby": o.value === null ? void 0 : i,
			"aria-valuemin": o.value === null ? void 0 : 0,
			"aria-valuemax": o.value === null ? void 0 : e.maximum,
			"aria-valuenow": o.value ?? void 0,
			"aria-valuetext": o.value === null ? void 0 : `${c.value} · ${s.value}`
		}, [
			(G(), K("svg", To, [n[1] ||= J("path", {
				class: "entity-gauge__track",
				d: "M20 110 A100 100 0 0 1 220 110"
			}, null, -1), o.value === null ? X("", !0) : (G(), K(U, { key: 0 }, [
				(G(!0), K(U, null, tr(l.value, (e) => (G(), K("path", {
					key: e.from,
					class: he(["entity-gauge__segment", `entity-gauge__segment--${e.color}`]),
					d: "M20 110 A100 100 0 0 1 220 110",
					pathLength: "100",
					"stroke-dasharray": `${e.length} 100`,
					"stroke-dashoffset": e.offset
				}, null, 10, Eo))), 128)),
				J("line", {
					class: "entity-gauge__needle",
					x1: "120",
					y1: "110",
					x2: "120",
					y2: "33",
					transform: `rotate(${o.value / e.maximum * 180 - 90} 120 110)`
				}, null, 8, Do),
				n[0] ||= J("circle", {
					class: "entity-gauge__pivot",
					cx: "120",
					cy: "110",
					r: "5"
				}, null, -1)
			], 64))])),
			J("div", Oo, [n[2] ||= J("span", null, "0", -1), J("span", null, j(e.maximum), 1)]),
			J("p", ko, j(c.value), 1),
			s.value ? (G(), K("p", Ao, j(s.value), 1)) : X("", !0)
		], 8, wo)])) : X("", !0);
	}
}), [["styles", [".entity-gauge{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);text-align:center;padding:24px}.entity-gauge h2{overflow-wrap:anywhere;margin:0 0 20px;font-size:16px;font-weight:500;line-height:1.5}.entity-gauge__meter{max-width:260px;margin:0 auto}.entity-gauge svg{fill:none;width:100%;display:block}.entity-gauge__track,.entity-gauge__segment{stroke-width:15px;stroke-linecap:butt}.entity-gauge__track{stroke:var(--divider-color,#e0e0e0)}.entity-gauge__segment--red{stroke:var(--error-color,#db4437)}.entity-gauge__segment--yellow{stroke:var(--warning-color,#f4b400)}.entity-gauge__segment--green{stroke:var(--success-color,#0f9d58)}.entity-gauge__needle{stroke:var(--primary-text-color,#212121);stroke-width:3px;stroke-linecap:round}.entity-gauge__pivot{stroke:none;fill:var(--primary-text-color,#212121)}.entity-gauge__scale{color:var(--secondary-text-color,#666);justify-content:space-between;padding:2px 7px;font-size:12px;display:flex}.entity-gauge__value{overflow-wrap:anywhere;margin:10px 0 0;font-size:28px;font-weight:500;line-height:1.4}.entity-gauge__range{color:var(--secondary-text-color,#666);margin:4px 0 0;font-size:14px;line-height:1.5}"]]]), Mo = {
	key: 0,
	class: "entity-value"
}, No = { class: "entity-value__name" }, Po = { class: "entity-value__state" }, Fo = /*#__PURE__*/ So(/* @__PURE__ */ Vn({
	__name: "EntityValue",
	props: {
		domain: { type: null },
		entityKey: { type: String }
	},
	setup(e) {
		let t = e, n = An(io), r = Q(() => n?.entity(t.domain, t.entityKey));
		return (e, t) => r.value ? (G(), K("div", Mo, [J("span", No, j(r.value.name), 1), J("span", Po, j(r.value.displayValue), 1)])) : X("", !0);
	}
}), [["styles", [".entity-value{color:var(--primary-text-color,#212121);overflow-wrap:anywhere;flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:8px 20px;line-height:1.5;display:flex}.entity-value__name{color:var(--secondary-text-color,#666)}.entity-value__state{font-weight:500}"]]]), Io = { class: "general-view" }, Lo = {
	key: 0,
	class: "general-view__status",
	role: "status"
}, Ro = {
	key: 1,
	class: "general-view__status",
	role: "status"
}, zo = {
	key: 2,
	class: "general-view__gauges"
}, Bo = ["aria-labelledby"], Vo = ["id"], Ho = { class: "general-view__rows" }, Uo = /*#__PURE__*/ So(/* @__PURE__ */ Vn({
	__name: "GeneralView",
	setup(e) {
		let t = An(io), n = Hn(), r = Q(() => t?.language.value === "de" ? {
			power: "Leistung",
			energy: "Energie",
			device: "Gerät",
			low: "Niedrig",
			medium: "Mittel",
			high: "Hoch",
			inRange: "Im Bereich",
			loading: "Die Entitäten werden geladen …",
			empty: "Für diese Ansicht sind keine Entitäten verfügbar."
		} : {
			power: "Power",
			energy: "Energy",
			device: "Device",
			low: "Low",
			medium: "Medium",
			high: "High",
			inRange: "In range",
			loading: "Loading entities …",
			empty: "No entities are available for this view."
		}), i = [
			{
				title: "power",
				entities: [
					["number", "max_soc"],
					["sensor", "charge_power"],
					["sensor", "discharge_power"],
					["sensor", "smartmeter_power"]
				]
			},
			{
				title: "energy",
				entities: [["sensor", "energy_charged"], ["sensor", "energy_discharged"]]
			},
			{
				title: "device",
				entities: [
					["sensor", "sun_version_master"],
					["sensor", "sun_version_gateway"],
					["sensor", "sun_serial_number"],
					["sensor", "storage_event_text"],
					["sensor", "ic_control_mode_text"],
					["binary_sensor", "cell_calibration_active"],
					["sensor", "next_cell_calibration"]
				]
			}
		], a = Q(() => i.map((e) => ({
			...e,
			entities: e.entities.filter(([e, n]) => t?.entity(e, n))
		})).filter((e) => e.entities.length)), o = Q(() => !!(t?.entity("sensor", "soc") || t?.entity("sensor", "storage_max_cell_temp"))), s = Q(() => !!t?.entity("switch", "storage_switch")), c = Q(() => o.value || s.value || a.value.length > 0);
		return (e, i) => (G(), K("div", Io, [
			!z(t)?.ready.value && !z(t)?.error.value ? (G(), K("p", Lo, j(r.value.loading), 1)) : z(t)?.ready.value && !c.value ? (G(), K("p", Ro, j(r.value.empty), 1)) : X("", !0),
			o.value ? (G(), K("div", zo, [Y(jo, {
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
			}, null, 8, ["segments"]), Y(jo, {
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
			s.value ? (G(), q(Co, {
				key: 3,
				domain: "switch",
				"entity-key": "storage_switch"
			})) : X("", !0),
			(G(!0), K(U, null, tr(a.value, (e) => (G(), K("section", {
				key: e.title,
				class: "general-view__card",
				"aria-labelledby": `${z(n)}-${e.title}`
			}, [J("h2", { id: `${z(n)}-${e.title}` }, j(r.value[e.title]), 9, Vo), J("div", Ho, [(G(!0), K(U, null, tr(e.entities, ([e, t]) => (G(), K(U, { key: `${e}.${t}` }, [e === "number" ? (G(), q(Co, {
				key: 0,
				domain: e,
				"entity-key": t
			}, null, 8, ["domain", "entity-key"])) : (G(), q(Fo, {
				key: 1,
				domain: e,
				"entity-key": t
			}, null, 8, ["domain", "entity-key"]))], 64))), 128))])], 8, Bo))), 128))
		]));
	}
}), [["styles", [".general-view{gap:20px;min-width:0;margin-top:24px;display:grid}.general-view__gauges{grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr));gap:20px;display:grid}.general-view__card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.general-view__card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.general-view__rows{gap:16px;display:grid}.general-view__rows .entity-control{border:0;border-bottom:1px solid var(--divider-color,#e0e0e0);box-shadow:none;border-radius:0;padding:0 0 16px}.general-view__rows .entity-control:only-child{border-bottom:0;padding-bottom:0}.general-view__status{color:var(--secondary-text-color,#666);margin:0;line-height:1.6}@media (max-width:600px){.general-view,.general-view__gauges{gap:16px}.general-view__card{padding:20px}}"]]]), Wo = { class: "charging-view" }, Go = {
	key: 0,
	class: "charging-view__status",
	role: "status"
}, Ko = {
	key: 1,
	class: "charging-view__status",
	role: "status"
}, qo = ["aria-labelledby"], Jo = ["id"], Yo = { class: "charging-view__rows" }, Xo = /*#__PURE__*/ So(/* @__PURE__ */ Vn({
	__name: "ChargingLayout",
	props: {
		switchKey: { type: String },
		cards: { type: Array }
	},
	setup(e) {
		let t = e, n = An(io), r = Hn(), i = Q(() => n?.language.value ?? "en"), a = Q(() => t.cards.map((e) => ({
			...e,
			entities: e.entities.filter(([e, t]) => n?.entity(e, t))
		})).filter((e) => e.entities.length)), o = Q(() => !!n?.entity("switch", t.switchKey)), s = Q(() => i.value === "de" ? {
			loading: "Die Entitäten werden geladen …",
			empty: "Für diese Ansicht sind keine Entitäten verfügbar."
		} : {
			loading: "Loading entities …",
			empty: "No entities are available for this view."
		});
		return (t, c) => (G(), K("div", Wo, [
			!z(n)?.ready.value && !z(n)?.error.value ? (G(), K("p", Go, j(s.value.loading), 1)) : z(n)?.ready.value && !o.value && !a.value.length ? (G(), K("p", Ko, j(s.value.empty), 1)) : X("", !0),
			o.value ? (G(), q(Co, {
				key: 2,
				domain: "switch",
				"entity-key": e.switchKey
			}, null, 8, ["entity-key"])) : X("", !0),
			(G(!0), K(U, null, tr(a.value, (e) => (G(), K("section", {
				key: e.key,
				class: "charging-view__card",
				"aria-labelledby": `${z(r)}-${e.key}`
			}, [J("h2", { id: `${z(r)}-${e.key}` }, j(e.title[i.value]), 9, Jo), J("div", Yo, [(G(!0), K(U, null, tr(e.entities, ([e, t]) => (G(), K(U, { key: `${e}.${t}` }, [e === "switch" || e === "number" || e === "time" || e === "select" ? (G(), q(Co, {
				key: 0,
				domain: e,
				"entity-key": t
			}, null, 8, ["domain", "entity-key"])) : (G(), q(Fo, {
				key: 1,
				domain: e,
				"entity-key": t
			}, null, 8, ["domain", "entity-key"]))], 64))), 128))])], 8, qo))), 128))
		]));
	}
}), [["styles", [".charging-view{gap:20px;min-width:0;margin-top:24px;display:grid}.charging-view__card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.charging-view__card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.charging-view__rows{gap:16px;display:grid}.charging-view__rows .entity-control{border:0;border-bottom:1px solid var(--divider-color,#e0e0e0);box-shadow:none;border-radius:0;padding:0 0 16px}.charging-view__rows .entity-control:last-child{border-bottom:0;padding-bottom:0}.charging-view__status{color:var(--secondary-text-color,#666);margin:0;line-height:1.6}@media (max-width:600px){.charging-view{gap:16px}.charging-view__card{padding:20px}}"]]]), Zo = /* @__PURE__ */ Vn({
	__name: "TimedChargingView",
	setup(e) {
		let t = [
			{
				key: "window",
				title: {
					de: "Zeitfenster",
					en: "Time window"
				},
				entities: [["time", "timed_charge_start"], ["time", "timed_charge_end"]]
			},
			{
				key: "discharge",
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
				title: {
					de: "Aktive Monate",
					en: "Active months"
				},
				entities: Array.from({ length: 12 }, (e, t) => ["switch", `timed_charge_month_${t + 1}`])
			}
		];
		return (e, n) => (G(), q(Xo, {
			"switch-key": "timed_charge_enabled",
			cards: t
		}));
	}
}), Qo = /* @__PURE__ */ Vn({
	__name: "GridServingView",
	setup(e) {
		let t = [{
			key: "pause",
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
			title: {
				de: "Aktive Monate",
				en: "Active months"
			},
			entities: Array.from({ length: 12 }, (e, t) => ["switch", `grid_serving_month_${t + 1}`])
		}];
		return (e, n) => (G(), q(Xo, {
			"switch-key": "grid_serving_enabled",
			cards: t
		}));
	}
}), $o = /* @__PURE__ */ Vn({
	__name: "DynamicChargingView",
	setup(e) {
		let t = [{
			key: "price",
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
		return (e, n) => (G(), q(Xo, {
			"switch-key": "price_charge_enabled",
			cards: t
		}));
	}
});
//#endregion
//#region src/savings.ts
function es(e) {
	if (typeof e != "number" && typeof e != "string" || typeof e == "string" && !e.trim()) return null;
	let t = Number(e);
	return Number.isFinite(t) ? t : null;
}
function ts(e) {
	return {
		comma_decimal: "en-US",
		decimal_comma: "de-DE",
		space_comma: "fr-FR"
	}[e?.locale?.number_format ?? ""] ?? e?.locale?.language ?? e?.language ?? "en";
}
function ns(e, t, n = 2) {
	let r = es(e);
	return r === null ? null : new Intl.NumberFormat(ts(t), {
		minimumFractionDigits: n,
		maximumFractionDigits: n,
		useGrouping: t?.locale?.number_format !== "none"
	}).format(r);
}
function rs(e, t, n = {
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
function is(e, t) {
	let n = (e) => /^\d{4}-\d{2}-\d{2}$/.test(e) && Number(e.slice(0, 4)) > 0 && Number.isFinite(Date.parse(`${e}T00:00:00Z`)) && (/* @__PURE__ */ new Date(`${e}T00:00:00Z`)).toISOString().slice(0, 10) === e;
	return n(e) && n(t) && e <= t;
}
function as(e) {
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
function os(e, t, n) {
	let r = /* @__PURE__ */ Gt(null), i = /* @__PURE__ */ R(!1), a = /* @__PURE__ */ R(null), o, s = 0, c = !1;
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
					first_weekday: as(u),
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
		if (!is(e, t)) {
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
		() => as(e()),
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
	}, { immediate: !0 }), De(() => {
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
//#region src/views/SavingsView.vue?vue&type=script&setup=true&lang.ts
var ss = { class: "savings-view" }, cs = ["aria-labelledby"], ls = ["id"], us = ["aria-labelledby"], ds = ["id"], fs = {
	key: 0,
	class: "savings-progress"
}, ps = ["id"], ms = { class: "savings-large" }, hs = [
	"role",
	"aria-labelledby",
	"aria-valuemin",
	"aria-valuemax",
	"aria-valuenow"
], gs = {
	key: 1,
	class: "savings-rows"
}, _s = { key: 0 }, vs = { key: 1 }, ys = { key: 2 }, bs = { key: 3 }, xs = ["aria-label"], Ss = { class: "savings-large" }, Cs = ["aria-labelledby"], ws = ["id"], Ts = { class: "savings-table-scroll" }, Es = { class: "savings-table" }, Ds = { colspan: "2" }, Os = { key: 0 }, ks = { key: 0 }, As = { key: 1 }, js = ["aria-labelledby"], Ms = ["id"], Ns = ["for"], Ps = ["id", "max"], Fs = ["for"], Is = ["id", "min"], Ls = { type: "submit" }, Rs = ["disabled"], zs = {
	key: 0,
	role: "status"
}, Bs = {
	key: 1,
	role: "alert"
}, Vs = { class: "savings-selected-dates" }, Hs = { class: "savings-large" }, Us = ["id"], Ws = { class: "savings-chart-hint" }, Gs = [
	"viewBox",
	"aria-labelledby",
	"aria-describedby"
], Ks = ["id"], qs = [
	"x1",
	"x2",
	"y1",
	"y2"
], Js = ["x"], Ys = ["x"], Xs = ["x"], Zs = ["x"], Qs = [
	"x",
	"y",
	"width",
	"height"
], $s = { class: "savings-chart-table" }, ec = { class: "savings-table-scroll" }, tc = { class: "savings-table" }, nc = {
	key: 1,
	class: "savings-empty"
}, rc = { class: "savings-card savings-explanation" }, ic = {
	key: 5,
	class: "savings-card savings-status",
	role: "status"
}, ac = /*#__PURE__*/ So(/* @__PURE__ */ Vn({
	__name: "SavingsView",
	props: {
		hass: { type: Object },
		entryId: { type: String }
	},
	setup(e) {
		let t = e, n = An(io), r = Hn(), i = Q(() => n?.language.value === "de"), a = Q(() => i.value ? {
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
			tariff: "Tarifplan (tageszeitabhängig)",
			from: "Von",
			to: "Bis",
			price: "Arbeitspreis",
			now: "jetzt",
			base: "Grundpreis",
			feed: "Einspeisevergütung",
			next: "Nächster Preiswechsel",
			noPrice: "Derzeit gilt kein Preis. Bitte die Tarifkonfiguration prüfen.",
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
			tariff: "Tariff schedule (time of use)",
			from: "From",
			to: "To",
			price: "Import price",
			now: "now",
			base: "Base price",
			feed: "Feed-in remuneration",
			next: "Next price change",
			noPrice: "No price currently applies. Please check the tariff configuration.",
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
		}), o = Q(() => n?.entity("binary_sensor", "economics_investment_configured")), s = Q(() => n?.entity("sensor", "economics_amortization_progress")), c = Q(() => n?.entity("sensor", "economics_remaining_to_payback")), l = Q(() => n?.entity("sensor", "economics_roi")), u = Q(() => n?.entity("sensor", "economics_net_savings")), d = Q(() => n?.entity("sensor", "economics_status")), f = Q(() => n?.entity("sensor", "economics_current_import_price")), p = Q(() => s.value?.available ? es(s.value.state?.state) : null), m = Q(() => p.value === null ? null : Math.max(0, Math.min(100, p.value))), h = (e) => {
			let n = ns(e, t.hass);
			return n === null ? a.value.unavailable : `${n} €`;
		}, g = (e) => {
			let n = ns(e, t.hass, 4);
			return n === null ? a.value.unavailable : `${n} EUR/kWh`;
		}, _ = (e) => rs(e, t.hass) ?? a.value.unavailable, v = (e) => rs(`${e}T12:00:00Z`, t.hass, {
			dateStyle: "medium",
			timeZone: "UTC"
		}) ?? e, y = Q(() => {
			let e = d.value?.available ? d.value.state?.state : void 0;
			return e === "active" ? null : e === "disabled" || e === "price_unavailable" || e === "origin_unavailable" || e === "partial_price_coverage" || e === "storage_error" ? a.value[e] : a.value.missing;
		}), b = Q(() => f.value?.state?.attributes ?? {}), x = Q(() => b.value.tariff_type === "time_of_use"), ee = Q(() => Array.isArray(b.value.windows) ? b.value.windows.filter((e) => !!e && typeof e == "object" && typeof e.start == "string" && typeof e.end == "string") : []), S = Q(() => b.value.unavailable_reason), C = Q(() => f.value?.available && es(f.value.state?.state) !== null && S.value == null), te = Q(() => {
			let e = b.value.active_window;
			return e && typeof e == "object" ? e : null;
		}), ne = (e) => C.value && es(e.price_eur_kwh) !== null && te.value?.start === e.start && te.value?.end === e.end, re = Q(() => C.value && te.value === null && es(b.value.base_price_eur_kwh) !== null), w = (e) => rs(`2000-01-01T${e.length === 5 ? `${e}:00` : e}Z`, t.hass, {
			timeStyle: "short",
			timeZone: "UTC"
		}) ?? e.slice(0, 5), T = os(() => t.hass, () => t.entryId, () => u.value?.metadata.entity_id), E = /* @__PURE__ */ R(""), D = /* @__PURE__ */ R(""), ie = null;
		Nn(T.data, (e) => {
			e && ((!E.value && !D.value || E.value === ie?.start && D.value === ie?.end) && (E.value = e.selected.start_date, D.value = e.selected.end_date), ie = {
				start: e.selected.start_date,
				end: e.selected.end_date
			});
		}), Nn(() => t.entryId, () => {
			E.value = "", D.value = "", ie = null;
		});
		let O = Q(() => T.error.value === "invalid" ? a.value.invalid : T.error.value === "failed" ? a.value.failed : T.error.value === "unavailable" || T.data.value?.status === "recorder_unavailable" ? a.value.noRecorder : null), ae = [
			"day",
			"week",
			"month",
			"year"
		], oe = Q(() => T.data.value?.selected.buckets ?? []), se = /* @__PURE__ */ R(null), ce = /* @__PURE__ */ R(720);
		Nn(se, (e, t, n) => {
			if (!e) return;
			let r = (e) => {
				Number.isFinite(e) && e > 0 && (ce.value = e);
			};
			if (r(e.getBoundingClientRect().width), typeof ResizeObserver > "u") return;
			let i = new ResizeObserver((e) => {
				for (let t of e) r(t.contentRect.width);
			});
			i.observe(e), n(() => i.disconnect());
		});
		let k = Q(() => {
			let e = oe.value.map((e) => es(e.change)), n = Math.max(0, ...e.map((e) => e ?? 0)), r = Math.min(0, ...e.map((e) => e ?? 0)), i = n - r || 1, a = (e) => 20 + (n - e) / i * 180, o = T.data.value?.selected, s = Date.parse(o?.start ?? ""), c = Date.parse(o?.end ?? ""), l = c - s, u = ns(n, t.hass) ?? "", d = ns(r, t.hass) ?? "", f = Math.max(56, Math.max(u.length, d.length) * 7.1 + 12), p = ce.value - 24, m = Math.max(1, p - f), h = (e) => f + Math.max(0, Math.min(1, (Date.parse(e) - s) / l)) * m;
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
				bars: oe.value.map((t, n) => {
					let r = h(t.end) - h(t.start);
					return {
						...t,
						value: e[n],
						x: h(t.start) + Math.min(2, r / 8),
						y: e[n] === null ? a(0) : a(Math.max(0, e[n])),
						height: e[n] === null ? 0 : Math.abs(a(e[n]) - a(0)),
						width: Math.max(0, r - Math.min(4, r / 4)),
						label: _(t.start)
					};
				})
			};
		}), le = Q(() => oe.value.some((e) => es(e.change) !== null)), de = (e) => rs(e, t.hass, T.data.value?.selected.period === "hour" ? { timeStyle: "short" } : T.data.value?.selected.period === "month" ? {
			month: "short",
			year: "numeric"
		} : {
			day: "2-digit",
			month: "short"
		}) ?? e;
		return (t, i) => (G(), K("div", ss, [
			o.value?.available && o.value.state?.state === "off" ? (G(), K("section", {
				key: 0,
				class: "savings-card",
				"aria-labelledby": `${z(r)}-investment`
			}, [J("h2", { id: `${z(r)}-investment` }, j(a.value.payback), 9, ls), J("p", null, j(a.value.investment), 1)], 8, cs)) : o.value?.available && o.value.state?.state === "on" && (s.value || c.value || l.value || u.value || d.value) ? (G(), K("section", {
				key: 1,
				class: "savings-card",
				"aria-labelledby": `${z(r)}-payback`
			}, [
				J("h2", { id: `${z(r)}-payback` }, j(a.value.payback), 9, ds),
				s.value ? (G(), K("div", fs, [
					J("h3", { id: `${z(r)}-progress` }, j(s.value.name), 9, ps),
					J("p", ms, j(p.value === null ? a.value.unavailable : `${z(ns)(p.value, e.hass)} %`), 1),
					J("div", {
						class: "savings-progress__track",
						role: m.value === null ? void 0 : "meter",
						"aria-labelledby": `${z(r)}-progress`,
						"aria-valuemin": m.value === null ? void 0 : 0,
						"aria-valuemax": m.value === null ? void 0 : 100,
						"aria-valuenow": m.value ?? void 0
					}, [m.value === null ? X("", !0) : (G(), K("span", {
						key: 0,
						style: ue({ width: `${m.value}%` })
					}, null, 4))], 8, hs)
				])) : X("", !0),
				c.value || l.value || u.value || d.value ? (G(), K("dl", gs, [
					c.value ? (G(), K("div", _s, [J("dt", null, j(c.value.name), 1), J("dd", null, j(h(c.value.available ? c.value.state?.state : null)), 1)])) : X("", !0),
					l.value ? (G(), K("div", vs, [J("dt", null, j(a.value.prior), 1), J("dd", null, j(h(l.value.available ? l.value.state?.attributes.prior_result_eur ?? l.value.state?.attributes.prior_result_eur_formatted : null)), 1)])) : X("", !0),
					u.value ? (G(), K("div", ys, [J("dt", null, j(a.value.net), 1), J("dd", null, j(h(u.value.available ? u.value.state?.state : null)), 1)])) : X("", !0),
					d.value ? (G(), K("div", bs, [J("dt", null, j(a.value.started), 1), J("dd", null, j(_(d.value.available ? d.value.state?.attributes.economics_started_at : null)), 1)])) : X("", !0)
				])) : X("", !0)
			], 8, us)) : X("", !0),
			u.value ? (G(), K("section", {
				key: 2,
				class: "savings-periods",
				"aria-label": a.value.periods
			}, [(G(), K(U, null, tr(ae, (e) => J("article", {
				key: e,
				class: "savings-card"
			}, [J("h2", null, j(a.value[e]), 1), J("p", Ss, j(z(T).loading.value ? "…" : h(z(T).data.value?.periods[e].change)), 1)])), 64))], 8, xs)) : X("", !0),
			x.value ? (G(), K("section", {
				key: 3,
				class: "savings-card",
				"aria-labelledby": `${z(r)}-tariff`
			}, [
				J("h2", { id: `${z(r)}-tariff` }, j(a.value.tariff), 9, ws),
				J("div", Ts, [J("table", Es, [J("thead", null, [J("tr", null, [
					i[4] ||= J("th", { "aria-label": "Status" }, null, -1),
					J("th", null, j(a.value.from), 1),
					J("th", null, j(a.value.to), 1),
					J("th", null, j(a.value.price), 1)
				])]), J("tbody", null, [(G(!0), K(U, null, tr(ee.value, (e, t) => (G(), K("tr", {
					key: t,
					class: he({ "savings-current": ne(e) })
				}, [
					J("td", null, j(ne(e) ? a.value.now : ""), 1),
					J("td", null, j(w(e.start)), 1),
					J("td", null, j(w(e.end)), 1),
					J("td", null, j(g(e.price_eur_kwh)), 1)
				], 2))), 128)), J("tr", { class: he({ "savings-current": re.value }) }, [
					J("td", null, j(re.value ? a.value.now : ""), 1),
					J("td", Ds, j(a.value.base), 1),
					J("td", null, j(g(b.value.base_price_eur_kwh)), 1)
				], 2)])])]),
				J("p", null, [J("strong", null, j(a.value.feed) + ":", 1), di(" " + j(g(b.value.feed_in_price_eur_kwh)), 1)]),
				C.value ? b.value.next_price_change_at ? (G(), K("p", As, [J("strong", null, j(a.value.next) + ":", 1), di(" " + j(_(b.value.next_price_change_at)), 1)])) : X("", !0) : (G(), K("p", Os, [di(j(a.value.noPrice), 1), typeof S.value == "string" && S.value ? (G(), K("span", ks, " (" + j(S.value) + ")", 1)) : X("", !0)]))
			], 8, Cs)) : X("", !0),
			u.value ? (G(), K("section", {
				key: 4,
				class: "savings-card",
				"aria-labelledby": `${z(r)}-range`
			}, [
				J("h2", { id: `${z(r)}-range` }, j(a.value.range), 9, Ms),
				J("form", {
					class: "savings-dates",
					onSubmit: i[3] ||= Ka((e) => z(T).select(E.value, D.value), ["prevent"])
				}, [
					J("label", { for: `${z(r)}-from` }, [di(j(a.value.from), 1), Dn(J("input", {
						id: `${z(r)}-from`,
						"onUpdate:modelValue": i[0] ||= (e) => E.value = e,
						type: "date",
						required: "",
						max: D.value || void 0
					}, null, 8, Ps), [[Ma, E.value]])], 8, Ns),
					J("label", { for: `${z(r)}-to` }, [di(j(a.value.to), 1), Dn(J("input", {
						id: `${z(r)}-to`,
						"onUpdate:modelValue": i[1] ||= (e) => D.value = e,
						type: "date",
						required: "",
						min: E.value || void 0
					}, null, 8, Is), [[Ma, D.value]])], 8, Fs),
					J("button", Ls, j(a.value.apply), 1),
					J("button", {
						type: "button",
						disabled: z(T).loading.value,
						onClick: i[2] ||= (...e) => z(T).refresh && z(T).refresh(...e)
					}, j(a.value.refresh), 9, Rs)
				], 32),
				z(T).loading.value ? (G(), K("p", zs, j(a.value.loading), 1)) : O.value ? (G(), K("p", Bs, j(O.value), 1)) : z(T).data.value ? (G(), K(U, { key: 2 }, [
					J("p", Vs, j(v(z(T).data.value.selected.start_date)) + " – " + j(v(z(T).data.value.selected.end_date)), 1),
					J("h3", null, j(a.value.selected), 1),
					J("p", Hs, j(h(z(T).data.value.selected.change)), 1),
					J("h3", { id: `${z(r)}-chart` }, j(a.value.chart), 9, Us),
					J("p", Ws, j(a.value.chartHint), 1),
					le.value ? (G(), K(U, { key: 0 }, [(G(), K("svg", {
						ref_key: "chartElement",
						ref: se,
						class: "savings-chart",
						viewBox: `0 0 ${ce.value} 240`,
						role: "img",
						"aria-labelledby": `${z(r)}-chart`,
						"aria-describedby": `${z(r)}-chart-description`
					}, [
						J("desc", { id: `${z(r)}-chart-description` }, j(a.value.net) + ": " + j(h(z(T).data.value.selected.change)) + ". " + j(a.value.table) + ". ", 9, Ks),
						J("line", {
							x1: k.value.left - 2,
							x2: k.value.right + 2,
							y1: k.value.zero,
							y2: k.value.zero,
							class: "savings-chart__axis"
						}, null, 8, qs),
						J("text", {
							x: k.value.left - 8,
							y: "24",
							"text-anchor": "end"
						}, j(k.value.highLabel), 9, Js),
						J("text", {
							x: k.value.left - 8,
							y: "204",
							"text-anchor": "end"
						}, j(k.value.lowLabel), 9, Ys),
						i[5] ||= J("text", {
							x: "10",
							y: "226"
						}, "EUR", -1),
						oe.value.length ? (G(), K("text", {
							key: 0,
							x: k.value.left,
							y: "226"
						}, j(de(k.value.start)), 9, Xs)) : X("", !0),
						oe.value.length > 1 ? (G(), K("text", {
							key: 1,
							x: k.value.right,
							y: "226",
							"text-anchor": "end"
						}, j(de(k.value.end)), 9, Zs)) : X("", !0),
						(G(!0), K(U, null, tr(k.value.bars, (e, t) => (G(), K("rect", {
							key: t,
							x: e.x,
							y: e.y,
							width: e.width,
							height: e.height,
							class: he(["savings-chart__bar", { "savings-chart__bar--negative": (e.value ?? 0) < 0 }])
						}, [J("title", null, j(e.label) + ": " + j(h(e.value)), 1)], 10, Qs))), 128))
					], 8, Gs)), J("details", $s, [J("summary", null, j(a.value.table), 1), J("div", ec, [J("table", tc, [J("thead", null, [J("tr", null, [
						J("th", null, j(a.value.from), 1),
						J("th", null, j(a.value.to), 1),
						J("th", null, j(a.value.net), 1)
					])]), J("tbody", null, [(G(!0), K(U, null, tr(k.value.bars, (e, t) => (G(), K("tr", { key: t }, [
						J("td", null, j(e.label), 1),
						J("td", null, j(_(e.end)), 1),
						J("td", null, j(h(e.value)), 1)
					]))), 128))])])])])], 64)) : X("", !0),
					!le.value || z(T).data.value.selected.change === null ? (G(), K("p", nc, j(z(T).data.value.selected.change === null ? a.value.noData : a.value.noChartData), 1)) : X("", !0)
				], 64)) : X("", !0)
			], 8, js)) : X("", !0),
			J("details", rc, [
				J("summary", null, j(a.value.explain), 1),
				J("p", null, j(a.value.netHint), 1),
				J("p", null, j(a.value.calendarHint), 1),
				J("p", null, j(a.value.rangeHint), 1)
			]),
			y.value && z(n)?.ready.value ? (G(), K("p", ic, j(y.value), 1)) : X("", !0)
		]));
	}
}), [["styles", [".savings-view{gap:20px;min-width:0;margin-top:24px;display:grid}.savings-card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.savings-card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.savings-card h3{margin:20px 0 8px;font-size:16px;font-weight:500}.savings-card p{overflow-wrap:anywhere;line-height:1.6}.savings-card p:last-child{margin-bottom:0}.savings-large{font-variant-numeric:tabular-nums;margin:0 0 12px;font-size:28px;font-weight:500}.savings-progress__track{background:var(--divider-color,#e0e0e0);border-radius:8px;height:16px;overflow:hidden}.savings-progress__track span{background:var(--info-color,#039be5);height:100%;display:block}.savings-rows{margin:20px 0 0}.savings-rows>div{border-bottom:1px solid var(--divider-color,#e0e0e0);justify-content:space-between;gap:16px;padding:12px 0;line-height:1.5;display:flex}.savings-rows>div:last-child{border-bottom:0;padding-bottom:0}.savings-rows dd{text-align:right;font-variant-numeric:tabular-nums;margin:0}.savings-periods{grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:16px;display:grid}.savings-periods h2{font-size:16px}.savings-table-scroll{overflow-x:auto}.savings-table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%;line-height:1.5}.savings-table th,.savings-table td{text-align:left;border-bottom:1px solid var(--divider-color,#e0e0e0);padding:10px 8px}.savings-table th:last-child,.savings-table td:last-child{text-align:right}.savings-current{background:var(--secondary-background-color,color-mix(in srgb, currentColor 8%, transparent));font-weight:600}.savings-dates{flex-wrap:wrap;align-items:end;gap:16px;display:flex}.savings-dates label{flex:180px;gap:8px;min-width:0;display:grid}.savings-dates input,.savings-dates button{box-sizing:border-box;font:inherit;border:1px solid var(--divider-color,#bdbdbd);background:var(--ha-card-background,var(--card-background-color,#fff));min-height:44px;color:var(--primary-text-color,#212121);border-radius:6px;padding:10px 12px}.savings-dates input{--lightningcss-light:initial;--lightningcss-dark: ;color-scheme:light dark;width:100%}@media (prefers-color-scheme:dark){.savings-dates input{--lightningcss-light: ;--lightningcss-dark:initial}}.savings-dates button{cursor:pointer;color:var(--primary-color,#0288d1)}.savings-dates button:disabled{opacity:.6;cursor:default}.savings-dates :focus-visible,.savings-card summary:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:3px}.savings-selected-dates,.savings-empty{color:var(--secondary-text-color,#666)}.savings-chart{width:100%;height:auto;display:block;overflow:visible}.savings-chart text{fill:var(--secondary-text-color,#666);font-size:12px}.savings-chart__axis{stroke:var(--primary-text-color,#212121);stroke-width:1px}.savings-chart__bar{fill:var(--info-color,#039be5)}.savings-chart__bar--negative{fill:var(--error-color,#db4437)}.savings-card summary{cursor:pointer;min-height:24px;font-weight:500;line-height:1.6}.savings-chart-table{margin-top:16px}.savings-status{margin:0;line-height:1.6}@media (max-width:600px){.savings-view{gap:16px}.savings-card{padding:20px}.savings-rows>div{flex-wrap:wrap;gap:4px 16px}.savings-rows dd{margin-left:auto}}"]]]), oc = ["lang"], sc = { class: "header" }, cc = ["aria-label"], lc = { class: "preview" }, uc = ["aria-label"], dc = [
	"href",
	"aria-current",
	"onClick"
], fc = {
	key: 0,
	class: "status",
	role: "alert"
}, pc = { class: "introduction" }, mc = {
	key: 0,
	class: "existing-link",
	href: "/sax-power"
}, hc = {
	class: "section",
	"aria-labelledby": "section-heading"
}, gc = {
	key: 0,
	class: "status",
	role: "status"
}, _c = {
	key: 1,
	class: "status",
	role: "status"
}, vc = {
	key: 7,
	class: "status"
}, yc = ["href"], bc = /* @__PURE__ */ Ca(/* @__PURE__ */ So(/* @__PURE__ */ Vn({
	__name: "Panel.ce",
	props: {
		hass: { type: Object },
		narrow: { type: Boolean },
		panel: { type: Object },
		route: { type: Object }
	},
	setup(e) {
		let t = e, n = Ea(), r = so(() => t.hass, () => t.panel?.config?.entry_id);
		kn(io, r);
		let i = Q(() => t.hass?.language.toLowerCase().startsWith("de") ? "de" : "en"), a = Q(() => no[i.value]), o = Q(() => !!t.hass?.panels?.["sax-power"]), s = Q(() => !t.hass?.kioskMode && (t.narrow || t.hass?.dockedSidebar === "always_hidden")), c = Q(() => `/${t.panel?.url_path || "sax-power-vue"}`), l = /* @__PURE__ */ R(t.route?.path ?? window.location.pathname), u = Q(() => to(l.value, c.value)), d = Q(() => eo.find((e) => e.path === u.value)), f = /* @__PURE__ */ R();
		Nn(() => t.route?.path, (e) => {
			e !== void 0 && (l.value = e);
		});
		function p() {
			l.value = window.location.pathname;
		}
		Qn(() => {
			window.addEventListener("popstate", p), window.addEventListener("location-changed", p);
		}), $n(() => {
			window.removeEventListener("popstate", p), window.removeEventListener("location-changed", p);
		});
		function m(e, t) {
			e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || (e.preventDefault(), window.location.pathname !== t && (window.history.pushState(null, "", t), window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: !1 } }))), p(), hn(() => f.value?.focus()));
		}
		function h() {
			n?.dispatchEvent(new CustomEvent("hass-toggle-menu", {
				bubbles: !0,
				composed: !0
			}));
		}
		return (t, n) => (G(), K("div", {
			class: he(["dashboard", { narrow: e.narrow }]),
			lang: i.value
		}, [
			J("header", sc, [
				s.value ? (G(), K("button", {
					key: 0,
					class: "menu-button",
					type: "button",
					"aria-label": a.value.menu,
					onClick: h
				}, [...n[1] ||= [J("svg", {
					viewBox: "0 0 24 24",
					"aria-hidden": "true"
				}, [J("path", { d: "M4 6h16M4 12h16M4 18h16" })], -1)]], 8, cc)) : X("", !0),
				n[2] ||= fi("<div class=\"brand\"><svg class=\"brand-icon\" viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path d=\"M9 3h6M8 5h8a1 1 0 0 1 1 1v14H7V6a1 1 0 0 1 1-1Z\"></path><path d=\"m13 8-3 5h4l-3 5\"></path></svg><span>SAX Power <span class=\"variant\">(Vue)</span></span></div>", 1),
				J("span", lc, j(a.value.preview), 1)
			]),
			J("nav", {
				class: "navigation",
				"aria-label": a.value.navigation
			}, [(G(!0), K(U, null, tr(z(eo), (e) => (G(), K("a", {
				key: e.path,
				href: `${c.value}/${e.path}`,
				"aria-current": u.value === e.path ? "page" : void 0,
				onClick: (t) => m(t, `${c.value}/${e.path}`)
			}, j(e[i.value]), 9, dc))), 128))], 8, uc),
			J("main", null, [
				z(r).error.value ? (G(), K("p", fc, j(z(r).error.value), 1)) : X("", !0),
				J("div", pc, [J("p", null, j(o.value ? a.value.introduction : a.value.introductionStandalone), 1), o.value ? (G(), K("a", mc, j(a.value.existing), 1)) : X("", !0)]),
				J("section", hc, [J("h1", {
					id: "section-heading",
					ref_key: "heading",
					ref: f,
					tabindex: "-1"
				}, j(d.value?.[i.value] ?? a.value.notFound), 513), e.hass ? e.panel?.config?.entry_id ? u.value === "allgemein" ? (G(), q(Uo, { key: 2 })) : u.value === "ladeautomatik" ? (G(), q(Zo, { key: 3 })) : u.value === "netzdienliches-laden" ? (G(), q(Qo, { key: 4 })) : u.value === "dynamisches-laden" ? (G(), q($o, { key: 5 })) : u.value === "ersparnis" ? (G(), q(ac, {
					key: 6,
					hass: e.hass,
					"entry-id": e.panel?.config?.entry_id
				}, null, 8, ["hass", "entry-id"])) : (G(), K("div", vc, [J("p", null, j(a.value.notFoundDescription), 1), J("a", {
					href: `${c.value}/allgemein`,
					onClick: n[0] ||= (e) => m(e, `${c.value}/allgemein`)
				}, j(a.value.returnToOverview), 9, yc)])) : (G(), K("p", _c, j(a.value.missingEntry), 1)) : (G(), K("p", gc, j(a.value.loading), 1))])
			])
		], 10, oc));
	}
}), [["styles", [":host{height:100%;color:var(--primary-text-color,#212121);background:var(--primary-background-color,#fafafa);font-family:var(--paper-font-body1_-_font-family,Roboto, sans-serif);font-size:14px;display:block}*{box-sizing:border-box}.dashboard{min-height:100%}.header{background:var(--app-header-background-color,var(--primary-color,#03a9f4));min-height:64px;color:var(--app-header-text-color,#fff);align-items:center;gap:14px;padding:8px 24px;display:flex}.brand{align-items:center;gap:10px;font-size:20px;font-weight:500;display:flex}.variant{font-size:16px;font-weight:400}.header svg{fill:none;stroke:currentColor;stroke-width:1.7px;stroke-linecap:round;stroke-linejoin:round}.brand-icon{width:30px;height:30px}.preview{border:1px solid;border-radius:12px;margin-left:auto;padding:3px 10px;font-size:12px}.menu-button{width:44px;height:44px;color:inherit;cursor:pointer;background:0 0;border:0;border-radius:50%;place-items:center;margin-left:-10px;display:grid}.menu-button svg{width:24px;height:24px}.navigation{border-bottom:1px solid var(--divider-color,#e0e0e0);background:var(--card-background-color,#fff);padding:0 16px;display:flex;overflow-x:auto}.navigation a{min-height:56px;color:var(--secondary-text-color,#666);white-space:nowrap;border-bottom:3px solid #0000;align-items:center;padding:12px 16px;text-decoration:none;display:flex}.navigation a[aria-current=page]{border-color:var(--primary-color,#03a9f4);color:var(--primary-text-color,#212121);font-weight:600}a{color:var(--primary-text-color,#212121);text-underline-offset:3px}a:focus-visible,button:focus-visible{outline-offset:-4px;outline:2px solid}main{max-width:1120px;margin:0 auto;padding:28px 24px 48px}.introduction{flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:8px 24px;margin-bottom:24px;line-height:1.6;display:flex}.introduction p{color:var(--secondary-text-color,#666);margin:0}.existing-link{align-items:center;min-height:44px;display:inline-flex}.section{overflow-wrap:anywhere;border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));box-shadow:var(--ha-card-box-shadow,none);padding:28px}h1{margin:0;font-size:24px;font-weight:500;line-height:1.35}h1:focus{outline:none}h2{margin:0 0 12px;font-size:18px;font-weight:500;line-height:1.5}.status{margin-top:24px;line-height:1.7}.narrow .header{padding-left:16px;padding-right:16px}.narrow main{padding:16px 12px 32px}@media (max-width:600px){.header{gap:8px;padding:8px 16px}.brand{gap:6px;font-size:18px}.brand-icon{display:none}.navigation{padding:0 4px}main{padding:16px 12px 32px}.introduction{gap:0;margin-bottom:16px}.section{padding:20px}h1{font-size:22px}}"]]]));
customElements.get("sax-power-vue-panel") || customElements.define("sax-power-vue-panel", bc);
//#endregion
export { bc as SaxPowerVuePanel };
