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
}, E = /-\w/g, D = T((e) => e.replace(E, (e) => e.slice(1).toUpperCase())), O = /\B([A-Z])/g, k = T((e) => e.replace(O, "-$1").toLowerCase()), te = T((e) => e.charAt(0).toUpperCase() + e.slice(1)), ne = T((e) => e ? `on${te(e)}` : ""), re = (e, t) => !Object.is(e, t), ie = (e, ...t) => {
	for (let n = 0; n < e.length; n++) e[n](...t);
}, ae = (e, t, n, r = !1) => {
	Object.defineProperty(e, t, {
		configurable: !0,
		enumerable: !1,
		writable: r,
		value: n
	});
}, oe = (e) => {
	let t = parseFloat(e);
	return isNaN(t) ? e : t;
}, se = (e) => {
	let t = g(e) ? Number(e) : NaN;
	return isNaN(t) ? e : t;
}, ce, le = () => ce ||= typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : typeof global < "u" ? global : {};
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
function A(e) {
	let t = "";
	if (g(e)) t = e;
	else if (d(e)) for (let n = 0; n < e.length; n++) {
		let r = A(e[n]);
		r && (t += r + " ");
	}
	else if (v(e)) for (let n in e) e[n] && (t += n + " ");
	return t.trim();
}
var he = "itemscope,allowfullscreen,formnovalidate,ismap,nomodule,novalidate,readonly", ge = /* @__PURE__ */ e(he);
he + "";
function _e(e) {
	return !!e || e === "";
}
function ve(e, t) {
	if (e.length !== t.length) return !1;
	let n = !0;
	for (let r = 0; n && r < e.length; r++) n = be(e[r], t[r]);
	return n;
}
function ye(e, t) {
	if (e.size !== t.size) return !1;
	let n = Array.from(t), r = new Uint8Array(n.length);
	for (let t of e) {
		let e = -1;
		for (let i = 0; i < n.length; i++) if (!r[i] && be(t, n[i])) {
			e = i;
			break;
		}
		if (e < 0) return !1;
		r[e] = 1;
	}
	return !0;
}
function be(e, t) {
	if (e === t) return !0;
	let n = m(e), r = m(t);
	if (n || r) return n && r ? e.getTime() === t.getTime() : !1;
	if (n = _(e), r = _(t), n || r) return e === t;
	if (n = d(e), r = d(t), n || r) return n && r ? ve(e, t) : !1;
	if (n = v(e), r = v(t), n || r) {
		if (!n || !r) return !1;
		if (n = f(e), r = f(t), n || r || (n = p(e), r = p(t), n || r)) return n && r ? ye(e, t) : !1;
		if (Object.keys(e).length !== Object.keys(t).length) return !1;
		for (let n in e) {
			let r = e.hasOwnProperty(n), i = t.hasOwnProperty(n);
			if (r && !i || !r && i || !be(e[n], t[n])) return !1;
		}
	}
	return String(e) === String(t);
}
var xe = (e) => !!(e && e.__v_isRef === !0), j = (e) => g(e) ? e : e == null ? "" : d(e) || v(e) && (e.toString === b || !h(e.toString)) ? xe(e) ? j(e.value) : JSON.stringify(e, Se, 2) : String(e), Se = (e, t) => xe(t) ? Se(e, t.value) : f(t) ? { [`Map(${t.size})`]: [...t.entries()].reduce((e, [t, n], r) => (e[Ce(t, r) + " =>"] = n, e), {}) } : p(t) ? { [`Set(${t.size})`]: [...t.values()].map((e) => Ce(e)) } : _(t) ? Ce(t) : v(t) && !d(t) && !C(t) ? String(t) : t, Ce = (e, t = "") => _(e) ? `Symbol(${e.description ?? t})` : e, M, we = class {
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
function Te() {
	return M;
}
function Ee(e, t = !1) {
	M && M.cleanups.push(e);
}
var N, De = /* @__PURE__ */ new WeakSet(), Oe = class {
	constructor(e) {
		this.fn = e, this.deps = void 0, this.depsTail = void 0, this.flags = 5, this.next = void 0, this.cleanup = void 0, this.scheduler = void 0, M && (M.active ? M.effects.push(this) : this.flags &= -2);
	}
	pause() {
		this.flags |= 64;
	}
	resume() {
		this.flags & 64 && (this.flags &= -65, De.has(this) && (De.delete(this), this.trigger()));
	}
	notify() {
		this.flags & 2 && !(this.flags & 32) || this.flags & 8 || Me(this);
	}
	run() {
		if (!(this.flags & 1)) return this.fn();
		this.flags |= 2, Ge(this), Fe(this);
		let e = N, t = Ve;
		N = this, Ve = !0;
		try {
			return this.fn();
		} finally {
			Ie(this), N = e, Ve = t, this.flags &= -3;
		}
	}
	stop() {
		if (this.flags & 1) {
			for (let e = this.deps; e; e = e.nextDep) ze(e);
			this.deps = this.depsTail = void 0, Ge(this), this.onStop && this.onStop(), this.flags &= -2;
		}
	}
	trigger() {
		this.flags & 64 ? De.add(this) : this.scheduler ? this.scheduler() : this.runIfDirty();
	}
	runIfDirty() {
		Le(this) && this.run();
	}
	get dirty() {
		return Le(this);
	}
}, ke = 0, Ae, je;
function Me(e, t = !1) {
	if (e.flags |= 8, t) {
		e.next = je, je = e;
		return;
	}
	e.next = Ae, Ae = e;
}
function Ne() {
	ke++;
}
function Pe() {
	if (--ke > 0) return;
	if (je) {
		let e = je;
		for (je = void 0; e;) {
			let t = e.next;
			e.next = void 0, e.flags &= -9, e = t;
		}
	}
	let e;
	for (; Ae;) {
		let t = Ae;
		for (Ae = void 0; t;) {
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
function Fe(e) {
	for (let t = e.deps; t; t = t.nextDep) t.version = -1, t.prevActiveLink = t.dep.activeLink, t.dep.activeLink = t;
}
function Ie(e) {
	let t, n = e.depsTail, r = n;
	for (; r;) {
		let e = r.prevDep;
		r.version === -1 ? (r === n && (n = e), ze(r), Be(r)) : t = r, r.dep.activeLink = r.prevActiveLink, r.prevActiveLink = void 0, r = e;
	}
	e.deps = t, e.depsTail = n;
}
function Le(e) {
	for (let t = e.deps; t; t = t.nextDep) if (t.dep.version !== t.version || t.dep.computed && (Re(t.dep.computed) || t.dep.version !== t.version)) return !0;
	return !!e._dirty;
}
function Re(e) {
	if (e.flags & 4 && !(e.flags & 16) || (e.flags &= -17, e.globalVersion === Ke) || (e.globalVersion = Ke, !e.isSSR && e.flags & 128 && (!e.deps && !e._dirty || !Le(e)))) return;
	e.flags |= 2;
	let t = e.dep, n = N, r = Ve;
	N = e, Ve = !0;
	try {
		Fe(e);
		let n = e.fn(e._value);
		(t.version === 0 || re(n, e._value)) && (e.flags |= 128, e._value = n, t.version++);
	} catch (e) {
		throw t.version++, e;
	} finally {
		N = n, Ve = r, Ie(e), e.flags &= -3;
	}
}
function ze(e, t = !1) {
	let { dep: n, prevSub: r, nextSub: i } = e;
	if (r && (r.nextSub = i, e.prevSub = void 0), i && (i.prevSub = r, e.nextSub = void 0), n.subs === e && (n.subs = r, !r && n.computed)) {
		n.computed.flags &= -5;
		for (let e = n.computed.deps; e; e = e.nextDep) ze(e, !0);
	}
	!t && !--n.sc && n.map && n.map.delete(n.key);
}
function Be(e) {
	let { prevDep: t, nextDep: n } = e;
	t && (t.nextDep = n, e.prevDep = void 0), n && (n.prevDep = t, e.nextDep = void 0);
}
var Ve = !0, He = [];
function Ue() {
	He.push(Ve), Ve = !1;
}
function We() {
	let e = He.pop();
	Ve = e === void 0 || e;
}
function Ge(e) {
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
var Ke = 0, qe = class {
	constructor(e, t) {
		this.sub = e, this.dep = t, this.version = t.version, this.nextDep = this.prevDep = this.nextSub = this.prevSub = this.prevActiveLink = void 0;
	}
}, Je = class {
	constructor(e) {
		this.computed = e, this.version = 0, this.activeLink = void 0, this.subs = void 0, this.map = void 0, this.key = void 0, this.sc = 0, this.__v_skip = !0;
	}
	track(e) {
		if (!N || !Ve || N === this.computed) return;
		let t = this.activeLink;
		if (t === void 0 || t.sub !== N) t = this.activeLink = new qe(N, this), N.deps ? (t.prevDep = N.depsTail, N.depsTail.nextDep = t, N.depsTail = t) : N.deps = N.depsTail = t, Ye(t);
		else if (t.version === -1 && (t.version = this.version, t.nextDep)) {
			let e = t.nextDep;
			e.prevDep = t.prevDep, t.prevDep && (t.prevDep.nextDep = e), t.prevDep = N.depsTail, t.nextDep = void 0, N.depsTail.nextDep = t, N.depsTail = t, N.deps === t && (N.deps = e);
		}
		return t;
	}
	trigger(e) {
		this.version++, Ke++, this.notify(e);
	}
	notify(e) {
		Ne();
		try {
			for (let e = this.subs; e; e = e.prevSub) e.sub.notify() && e.sub.dep.notify();
		} finally {
			Pe();
		}
	}
};
function Ye(e) {
	if (e.dep.sc++, e.sub.flags & 4) {
		let t = e.dep.computed;
		if (t && !e.dep.subs) {
			t.flags |= 20;
			for (let e = t.deps; e; e = e.nextDep) Ye(e);
		}
		let n = e.dep.subs;
		n !== e && (e.prevSub = n, n && (n.nextSub = e)), e.dep.subs = e;
	}
}
var Xe = /* @__PURE__ */ new WeakMap(), Ze = /* @__PURE__ */ Symbol(""), Qe = /* @__PURE__ */ Symbol(""), $e = /* @__PURE__ */ Symbol("");
function P(e, t, n) {
	if (Ve && N) {
		let t = Xe.get(e);
		t || Xe.set(e, t = /* @__PURE__ */ new Map());
		let r = t.get(n);
		r || (t.set(n, r = new Je()), r.map = t, r.key = n), r.track();
	}
}
function et(e, t, n, r, i, a) {
	let o = Xe.get(e);
	if (!o) {
		Ke++;
		return;
	}
	let s = (e) => {
		e && e.trigger();
	};
	if (Ne(), t === "clear") o.forEach(s);
	else {
		let i = d(e), a = i && w(n);
		if (i && n === "length") {
			let e = Number(r);
			o.forEach((t, n) => {
				(n === "length" || n === $e || !_(n) && n >= e) && s(t);
			});
		} else switch ((n !== void 0 || o.has(void 0)) && s(o.get(n)), a && s(o.get($e)), t) {
			case "add":
				i ? a && s(o.get("length")) : (s(o.get(Ze)), f(e) && s(o.get(Qe)));
				break;
			case "delete":
				i || (s(o.get(Ze)), f(e) && s(o.get(Qe)));
				break;
			case "set": f(e) && s(o.get(Ze));
		}
	}
	Pe();
}
function tt(e) {
	let t = /* @__PURE__ */ F(e);
	return t === e ? t : (P(t, "iterate", $e), /* @__PURE__ */ Bt(e) ? t : t.map(Ut));
}
function nt(e) {
	return P(e = /* @__PURE__ */ F(e), "iterate", $e), e;
}
function rt(e, t) {
	return /* @__PURE__ */ zt(e) ? Wt(/* @__PURE__ */ Rt(e) ? Ut(t) : t) : Ut(t);
}
var it = {
	__proto__: null,
	[Symbol.iterator]() {
		return at(this, Symbol.iterator, (e) => rt(this, e));
	},
	concat(...e) {
		return tt(this).concat(...e.map((e) => d(e) ? tt(e) : e));
	},
	entries() {
		return at(this, "entries", (e) => (e[1] = rt(this, e[1]), e));
	},
	every(e, t) {
		return st(this, "every", e, t, void 0, arguments);
	},
	filter(e, t) {
		return st(this, "filter", e, t, (e) => e.map((e) => rt(this, e)), arguments);
	},
	find(e, t) {
		return st(this, "find", e, t, (e) => rt(this, e), arguments);
	},
	findIndex(e, t) {
		return st(this, "findIndex", e, t, void 0, arguments);
	},
	findLast(e, t) {
		return st(this, "findLast", e, t, (e) => rt(this, e), arguments);
	},
	findLastIndex(e, t) {
		return st(this, "findLastIndex", e, t, void 0, arguments);
	},
	forEach(e, t) {
		return st(this, "forEach", e, t, void 0, arguments);
	},
	includes(...e) {
		return lt(this, "includes", e);
	},
	indexOf(...e) {
		return lt(this, "indexOf", e);
	},
	join(e) {
		return tt(this).join(e);
	},
	lastIndexOf(...e) {
		return lt(this, "lastIndexOf", e);
	},
	map(e, t) {
		return st(this, "map", e, t, void 0, arguments);
	},
	pop() {
		return ut(this, "pop");
	},
	push(...e) {
		return ut(this, "push", e);
	},
	reduce(e, ...t) {
		return ct(this, "reduce", e, t);
	},
	reduceRight(e, ...t) {
		return ct(this, "reduceRight", e, t);
	},
	shift() {
		return ut(this, "shift");
	},
	some(e, t) {
		return st(this, "some", e, t, void 0, arguments);
	},
	splice(...e) {
		return ut(this, "splice", e);
	},
	toReversed() {
		return tt(this).toReversed();
	},
	toSorted(e) {
		return tt(this).toSorted(e);
	},
	toSpliced(...e) {
		return tt(this).toSpliced(...e);
	},
	unshift(...e) {
		return ut(this, "unshift", e);
	},
	values() {
		return at(this, "values", (e) => rt(this, e));
	}
};
function at(e, t, n) {
	let r = nt(e), i = r[t]();
	return r !== e && !/* @__PURE__ */ Bt(e) && (i._next = i.next, i.next = () => {
		let e = i._next();
		return e.done || (e.value = n(e.value)), e;
	}), i;
}
var ot = Array.prototype;
function st(e, t, n, r, i, a) {
	let o = nt(e), s = o !== e && !/* @__PURE__ */ Bt(e), c = o[t];
	if (c !== ot[t]) {
		let t = c.apply(e, a);
		return s ? Ut(t) : t;
	}
	let l = n;
	o !== e && (s ? l = function(t, r) {
		return n.call(this, rt(e, t), r, e);
	} : n.length > 2 && (l = function(t, r) {
		return n.call(this, t, r, e);
	}));
	let u = c.call(o, l, r);
	return s && i ? i(u) : u;
}
function ct(e, t, n, r) {
	let i = nt(e), a = i !== e && !/* @__PURE__ */ Bt(e), o = n, s = !1;
	i !== e && (a ? (s = r.length === 0, o = function(t, r, i) {
		return s && (s = !1, t = rt(e, t)), n.call(this, t, rt(e, r), i, e);
	}) : n.length > 3 && (o = function(t, r, i) {
		return n.call(this, t, r, i, e);
	}));
	let c = i[t](o, ...r);
	return s ? rt(e, c) : c;
}
function lt(e, t, n) {
	let r = /* @__PURE__ */ F(e);
	P(r, "iterate", $e);
	let i = r[t](...n);
	return (i === -1 || i === !1) && /* @__PURE__ */ Vt(n[0]) ? (n[0] = /* @__PURE__ */ F(n[0]), r[t](...n)) : i;
}
function ut(e, t, n = []) {
	Ue(), Ne();
	let r = (/* @__PURE__ */ F(e))[t].apply(e, n);
	return Pe(), We(), r;
}
var dt = /* @__PURE__ */ e("__proto__,__v_isRef,__isVue"), ft = new Set(/* @__PURE__ */ Object.getOwnPropertyNames(Symbol).filter((e) => e !== "arguments" && e !== "caller").map((e) => Symbol[e]).filter(_));
function pt(e) {
	_(e) || (e = String(e));
	let t = /* @__PURE__ */ F(this);
	return P(t, "has", e), t.hasOwnProperty(e);
}
var mt = class {
	constructor(e = !1, t = !1) {
		this._isReadonly = e, this._isShallow = t;
	}
	get(e, t, n) {
		if (t === "__v_skip") return e.__v_skip;
		let r = this._isReadonly, i = this._isShallow;
		if (t === "__v_isReactive") return !r;
		if (t === "__v_isReadonly") return r;
		if (t === "__v_isShallow") return i;
		if (t === "__v_raw") return n === (r ? i ? Mt : jt : i ? At : kt).get(e) || Object.getPrototypeOf(e) === Object.getPrototypeOf(n) ? e : void 0;
		let a = d(e);
		if (!r) {
			let e;
			if (a && (e = it[t])) return e;
			if (t === "hasOwnProperty") return pt;
		}
		let o = Reflect.get(e, t, /* @__PURE__ */ I(e) ? e : n);
		if ((_(t) ? ft.has(t) : dt(t)) || (r || P(e, "get", t), i)) return o;
		if (/* @__PURE__ */ I(o)) {
			let e = a && w(t) ? o : o.value;
			return r && v(e) ? /* @__PURE__ */ It(e) : e;
		}
		return v(o) ? r ? /* @__PURE__ */ It(o) : /* @__PURE__ */ Pt(o) : o;
	}
}, ht = class extends mt {
	constructor(e = !1) {
		super(!1, e);
	}
	set(e, t, n, r) {
		let i = e[t], a = d(e) && w(t);
		if (!this._isShallow) {
			let e = /* @__PURE__ */ zt(i);
			if (!/* @__PURE__ */ Bt(n) && !/* @__PURE__ */ zt(n) && (i = /* @__PURE__ */ F(i), n = /* @__PURE__ */ F(n)), !a && /* @__PURE__ */ I(i) && !/* @__PURE__ */ I(n)) return e || (i.value = n), !0;
		}
		let o = a ? Number(t) < e.length : u(e, t), s = Reflect.set(e, t, n, /* @__PURE__ */ I(e) ? e : r);
		return e === /* @__PURE__ */ F(r) && s && (o ? re(n, i) && et(e, "set", t, n, i) : et(e, "add", t, n)), s;
	}
	deleteProperty(e, t) {
		let n = u(e, t), r = e[t], i = Reflect.deleteProperty(e, t);
		return i && n && et(e, "delete", t, void 0, r), i;
	}
	has(e, t) {
		let n = Reflect.has(e, t);
		return (!_(t) || !ft.has(t)) && P(e, "has", t), n;
	}
	ownKeys(e) {
		return P(e, "iterate", d(e) ? "length" : Ze), Reflect.ownKeys(e);
	}
}, gt = class extends mt {
	constructor(e = !1) {
		super(!0, e);
	}
	set(e, t) {
		return !0;
	}
	deleteProperty(e, t) {
		return !0;
	}
}, _t = /* @__PURE__ */ new ht(), vt = /* @__PURE__ */ new gt(), yt = /* @__PURE__ */ new ht(!0), bt = (e) => e, xt = (e) => Reflect.getPrototypeOf(e);
function St(e, t, n) {
	return function(...r) {
		let i = this.__v_raw, a = /* @__PURE__ */ F(i), o = f(a), c = e === "entries" || e === Symbol.iterator && o, l = e === "keys" && o, u = i[e](...r), d = n ? bt : t ? Wt : Ut;
		return !t && P(a, "iterate", l ? Qe : Ze), s(Object.create(u), { next() {
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
function Ct(e) {
	return function(...t) {
		return e === "delete" ? !1 : e === "clear" ? void 0 : this;
	};
}
function wt(e, t) {
	let n = {
		get(n) {
			let r = this.__v_raw, i = /* @__PURE__ */ F(r), a = /* @__PURE__ */ F(n);
			e || (re(n, a) && P(i, "get", n), P(i, "get", a));
			let { has: o } = xt(i), s = t ? bt : e ? Wt : Ut;
			if (o.call(i, n)) return s(r.get(n));
			if (o.call(i, a)) return s(r.get(a));
			r !== i && r.get(n);
		},
		get size() {
			let t = this.__v_raw;
			return !e && P(/* @__PURE__ */ F(t), "iterate", Ze), t.size;
		},
		has(t) {
			let n = this.__v_raw, r = /* @__PURE__ */ F(n), i = /* @__PURE__ */ F(t);
			return e || (re(t, i) && P(r, "has", t), P(r, "has", i)), t === i ? n.has(t) : n.has(t) || n.has(i);
		},
		forEach(n, r) {
			let i = this, a = i.__v_raw, o = /* @__PURE__ */ F(a), s = t ? bt : e ? Wt : Ut;
			return !e && P(o, "iterate", Ze), a.forEach((e, t) => n.call(r, s(e), s(t), i));
		}
	};
	return s(n, e ? {
		add: Ct("add"),
		set: Ct("set"),
		delete: Ct("delete"),
		clear: Ct("clear")
	} : {
		add(e) {
			let n = /* @__PURE__ */ F(this), r = xt(n), i = /* @__PURE__ */ F(e), a = !t && !/* @__PURE__ */ Bt(e) && !/* @__PURE__ */ zt(e) ? i : e;
			return r.has.call(n, a) || re(e, a) && r.has.call(n, e) || re(i, a) && r.has.call(n, i) || (n.add(a), et(n, "add", a, a)), this;
		},
		set(e, n) {
			!t && !/* @__PURE__ */ Bt(n) && !/* @__PURE__ */ zt(n) && (n = /* @__PURE__ */ F(n));
			let r = /* @__PURE__ */ F(this), { has: i, get: a } = xt(r), o = i.call(r, e);
			o ||= (e = /* @__PURE__ */ F(e), i.call(r, e));
			let s = a.call(r, e);
			return r.set(e, n), o ? re(n, s) && et(r, "set", e, n, s) : et(r, "add", e, n), this;
		},
		delete(e) {
			let t = /* @__PURE__ */ F(this), { has: n, get: r } = xt(t), i = n.call(t, e);
			i ||= (e = /* @__PURE__ */ F(e), n.call(t, e));
			let a = r ? r.call(t, e) : void 0, o = t.delete(e);
			return i && et(t, "delete", e, void 0, a), o;
		},
		clear() {
			let e = /* @__PURE__ */ F(this), t = e.size !== 0, n = e.clear();
			return t && et(e, "clear", void 0, void 0, void 0), n;
		}
	}), [
		"keys",
		"values",
		"entries",
		Symbol.iterator
	].forEach((r) => {
		n[r] = St(r, e, t);
	}), n;
}
function Tt(e, t) {
	let n = wt(e, t);
	return (t, r, i) => r === "__v_isReactive" ? !e : r === "__v_isReadonly" ? e : r === "__v_raw" ? t : Reflect.get(u(n, r) && r in t ? n : t, r, i);
}
var Et = { get: /* @__PURE__ */ Tt(!1, !1) }, Dt = { get: /* @__PURE__ */ Tt(!1, !0) }, Ot = { get: /* @__PURE__ */ Tt(!0, !1) }, kt = /* @__PURE__ */ new WeakMap(), At = /* @__PURE__ */ new WeakMap(), jt = /* @__PURE__ */ new WeakMap(), Mt = /* @__PURE__ */ new WeakMap();
function Nt(e) {
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
function Pt(e) {
	return /* @__PURE__ */ zt(e) ? e : Lt(e, !1, _t, Et, kt);
}
// @__NO_SIDE_EFFECTS__
function Ft(e) {
	return Lt(e, !1, yt, Dt, At);
}
// @__NO_SIDE_EFFECTS__
function It(e) {
	return Lt(e, !0, vt, Ot, jt);
}
function Lt(e, t, n, r, i) {
	if (!v(e) || e.__v_raw && !(t && e.__v_isReactive) || e.__v_skip || !Object.isExtensible(e)) return e;
	let a = i.get(e);
	if (a) return a;
	let o = Nt(S(e));
	if (o === 0) return e;
	let s = new Proxy(e, o === 2 ? r : n);
	return i.set(e, s), s;
}
// @__NO_SIDE_EFFECTS__
function Rt(e) {
	return /* @__PURE__ */ zt(e) ? /* @__PURE__ */ Rt(e.__v_raw) : !!(e && e.__v_isReactive);
}
// @__NO_SIDE_EFFECTS__
function zt(e) {
	return !!(e && e.__v_isReadonly);
}
// @__NO_SIDE_EFFECTS__
function Bt(e) {
	return !!(e && e.__v_isShallow);
}
// @__NO_SIDE_EFFECTS__
function Vt(e) {
	return e ? !!e.__v_raw : !1;
}
// @__NO_SIDE_EFFECTS__
function F(e) {
	let t = e && e.__v_raw;
	return t ? /* @__PURE__ */ F(t) : e;
}
function Ht(e) {
	return !u(e, "__v_skip") && Object.isExtensible(e) && ae(e, "__v_skip", !0), e;
}
var Ut = (e) => v(e) ? /* @__PURE__ */ Pt(e) : e, Wt = (e) => v(e) ? /* @__PURE__ */ It(e) : e;
// @__NO_SIDE_EFFECTS__
function I(e) {
	return e ? e.__v_isRef === !0 : !1;
}
// @__NO_SIDE_EFFECTS__
function L(e) {
	return Kt(e, !1);
}
// @__NO_SIDE_EFFECTS__
function Gt(e) {
	return Kt(e, !0);
}
function Kt(e, t) {
	return /* @__PURE__ */ I(e) ? e : new qt(e, t);
}
var qt = class {
	constructor(e, t) {
		this.dep = new Je(), this.__v_isRef = !0, this.__v_isShallow = !1, this._rawValue = t ? e : /* @__PURE__ */ F(e), this._value = t ? e : Ut(e), this.__v_isShallow = t;
	}
	get value() {
		return this.dep.track(), this._value;
	}
	set value(e) {
		let t = this._rawValue, n = this.__v_isShallow || /* @__PURE__ */ Bt(e) || /* @__PURE__ */ zt(e);
		e = n ? e : /* @__PURE__ */ F(e), re(e, t) && (this._rawValue = e, this._value = n ? e : Ut(e), this.dep.trigger());
	}
};
function R(e) {
	return /* @__PURE__ */ I(e) ? e.value : e;
}
var Jt = {
	get: (e, t, n) => t === "__v_raw" ? e : R(Reflect.get(e, t, n)),
	set: (e, t, n, r) => {
		let i = e[t];
		return /* @__PURE__ */ I(i) && !/* @__PURE__ */ I(n) ? (i.value = n, !0) : Reflect.set(e, t, n, r);
	}
};
function Yt(e) {
	return /* @__PURE__ */ Rt(e) ? e : new Proxy(e, Jt);
}
var Xt = class {
	constructor(e, t, n) {
		this.fn = e, this.setter = t, this._value = void 0, this.dep = new Je(this), this.__v_isRef = !0, this.deps = void 0, this.depsTail = void 0, this.flags = 16, this.globalVersion = Ke - 1, this.next = void 0, this.effect = this, this.__v_isReadonly = !t, this.isSSR = n;
	}
	notify() {
		if (this.flags |= 16, !(this.flags & 8) && N !== this) return Me(this, !0), !0;
	}
	get value() {
		let e = this.dep.track();
		return Re(this), e && (e.version = this.dep.version), this._value;
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
	let { immediate: a, deep: o, once: s, scheduler: l, augmentJob: u, call: f } = i, p = (e) => o ? e : /* @__PURE__ */ Bt(e) || o === !1 || o === 0 ? rn(e, 1) : rn(e), m, g, _, v, y = !1, b = !1;
	if (/* @__PURE__ */ I(e) ? (g = () => e.value, y = /* @__PURE__ */ Bt(e)) : /* @__PURE__ */ Rt(e) ? (g = () => p(e), y = !0) : d(e) ? (b = !0, y = e.some((e) => /* @__PURE__ */ Rt(e) || /* @__PURE__ */ Bt(e)), g = () => e.map((e) => {
		if (/* @__PURE__ */ I(e)) return e.value;
		if (/* @__PURE__ */ Rt(e)) return p(e);
		if (h(e)) return f ? f(e, 2) : e();
	})) : g = h(e) ? n ? f ? () => f(e, 2) : e : () => {
		if (_) {
			Ue();
			try {
				_();
			} finally {
				We();
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
	let x = Te(), S = () => {
		m.stop(), x && x.active && c(x.effects, m);
	};
	if (s && n) {
		let e = n;
		n = (...t) => {
			let n = e(...t);
			return S(), n;
		};
	}
	let C = b ? Array(e.length).fill(Qt) : Qt, w = (e) => {
		if (m.flags & 1 && (m.dirty || e)) {
			if (n) {
				let t = m.run();
				if (e || o || y || (b ? t.some((e, t) => re(e, C[t])) : re(t, C))) {
					_ && _();
					let e = en;
					en = m;
					try {
						let e = [
							t,
							C === Qt ? void 0 : b && C[0] === Qt ? [] : C,
							v
						];
						C = t, f ? f(n, 3, e) : n(...e);
					} finally {
						en = e;
					}
				}
			} else m.run();
		}
	};
	return u && u(w), m = new Oe(g), m.scheduler = l ? () => l(w, !1) : w, v = (e) => tn(e, !1, m), _ = m.onStop = () => {
		let e = $t.get(m);
		if (e) {
			if (f) f(e, 4);
			else for (let t of e) t();
			$t.delete(m);
		}
	}, n ? a ? w(!0) : C = m.run() : l ? l(w.bind(null, !0), !0) : m.run(), S.pause = m.pause.bind(m), S.resume = m.resume.bind(m), S.stop = S, S;
}
function rn(e, t = Infinity, n) {
	if (t <= 0 || !v(e) || e.__v_skip || (n ||= /* @__PURE__ */ new Map(), (n.get(e) || 0) >= t)) return e;
	if (n.set(e, t), t--, /* @__PURE__ */ I(e)) rn(e.value, t, n);
	else if (d(e)) for (let r = 0; r < e.length; r++) rn(e[r], t, n);
	else if (p(e) || f(e)) e.forEach((e) => {
		rn(e, t, n);
	});
	else if (C(e)) {
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
			Ue(), an(o, null, 10, [
				e,
				i,
				a
			]), We();
			return;
		}
	}
	cn(e, r, a, i, s);
}
function cn(e, t, n, r = !0, i = !1) {
	if (i) throw e;
	console.error(e);
}
var z = [], ln = -1, un = [], dn = null, fn = 0, pn = /* @__PURE__ */ Promise.resolve(), mn = null;
function hn(e) {
	let t = mn || pn;
	return e ? t.then(this ? e.bind(this) : e) : t;
}
function gn(e) {
	let t = ln + 1, n = z.length;
	for (; t < n;) {
		let r = t + n >>> 1, i = z[r], a = Sn(i);
		a < e || a === e && i.flags & 2 ? t = r + 1 : n = r;
	}
	return t;
}
function _n(e) {
	if (!(e.flags & 1)) {
		let t = Sn(e), n = z[z.length - 1];
		!n || !(e.flags & 2) && t >= Sn(n) ? z.push(e) : z.splice(gn(t), 0, e), e.flags |= 1, vn();
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
	for (; n < z.length; n++) {
		let t = z[n];
		if (t && t.flags & 2) {
			if (e && t.id !== e.uid) continue;
			z.splice(n, 1), n--, t.flags & 4 && (t.flags &= -2), t(), t.flags & 4 || (t.flags &= -2);
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
		for (ln = 0; ln < z.length; ln++) {
			let e = z[ln];
			e && !(e.flags & 8) && (e.flags & 4 && (e.flags &= -2), an(e, e.i, e.i ? 15 : 14), e.flags & 4 || (e.flags &= -2));
		}
	} finally {
		for (; ln < z.length; ln++) {
			let e = z[ln];
			e && (e.flags &= -2);
		}
		ln = -1, z.length = 0, xn(e), mn = null, (z.length || un.length) && Cn(e);
	}
}
var wn = null, Tn = null;
function En(e) {
	let t = wn;
	return wn = e, Tn = e && e.type.__scopeId || null, t;
}
function Dn(e, t = wn, n) {
	if (!t || e._n) return e;
	let r = (...n) => {
		r._d && ti(-1);
		let i = En(t), a = Qr.length, o;
		try {
			o = e(...n);
		} finally {
			for (let e = Qr.length; e > a; e--) $r();
			En(i), r._d && ti(1);
		}
		return o;
	};
	return r._n = !0, r._c = !0, r._d = !0, r;
}
function On(e, n) {
	if (wn === null) return e;
	let r = ji(wn), i = e.dirs ||= [];
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
function kn(e, t, n, r) {
	let i = e.dirs, a = t && t.dirs;
	for (let o = 0; o < i.length; o++) {
		let s = i[o];
		a && (s.oldValue = a[o].value);
		let c = s.dir[r];
		c && (Ue(), on(c, n, 8, [
			e.el,
			s,
			e,
			t
		]), We());
	}
}
function An(e, t) {
	if (Q) {
		let n = Q.provides, r = Q.parent && Q.parent.provides;
		r === n && (n = Q.provides = Object.create(r)), n[e] = t;
	}
}
function jn(e, t, n = !1) {
	let r = vi();
	if (r || cr) {
		let i = cr ? cr._context.provides : r ? r.parent == null || r.ce ? r.vnode.appContext && r.vnode.appContext.provides : r.parent.provides : void 0;
		if (i && e in i) return i[e];
		if (arguments.length > 1) return n && h(t) ? t.call(r && r.proxy) : t;
	}
}
var Mn = /* @__PURE__ */ Symbol.for("v-scx"), Nn = () => jn(Mn);
function Pn(e, t, n) {
	return Fn(e, t, n);
}
function Fn(e, n, i = t) {
	let { immediate: a, deep: o, flush: c, once: l } = i, u = s({}, i), d = n && a || !n && c !== "post", f;
	if (wi) {
		if (c === "sync") {
			let e = Nn();
			f = e.__watcherHandles ||= [];
		} else if (!d) {
			let e = () => {};
			return e.stop = r, e.resume = r, e.pause = r, e;
		}
	}
	let p = Q;
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
	return wi && (f ? f.push(h) : d && h()), h;
}
var In = /* @__PURE__ */ Symbol("_vte"), Ln = (e) => e.__isTeleport, Rn = /* @__PURE__ */ Symbol("_leaveCb");
function zn(e) {
	let t = e[0];
	if (e.length > 1) {
		for (let n of e) if (n.type !== Xr) {
			t = n;
			break;
		}
	}
	return t;
}
function Bn(e) {
	if (!Yn(e)) return Ln(e.type) && e.children ? zn(e.children) : e;
	if (e.component) return e.component.subTree;
	let { shapeFlag: t, children: n } = e;
	if (n) {
		if (t & 16) return n[0];
		if (t & 32 && h(n.default)) return n.default();
	}
}
function Vn(e, t) {
	if (e.shapeFlag & 6 && e.component) {
		e.transition = t;
		let n = e.component.subTree;
		Vn(Ln(n.type) && Bn(n) || n, t);
	} else e.shapeFlag & 128 ? (e.ssContent.transition = t.clone(e.ssContent), e.ssFallback.transition = t.clone(e.ssFallback)) : e.transition = t;
}
// @__NO_SIDE_EFFECTS__
function B(e, t) {
	return h(e) ? /* @__PURE__ */ s({ name: e.name }, t, { setup: e }) : e;
}
function Hn() {
	let e = vi();
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
	let s = a.shapeFlag & 4 ? ji(a.component) : a.el, l = o ? null : s, { i: f, r: p } = e, m = n && n.r, _ = f.refs === t ? f.refs = {} : f.refs, v = f.setupState, y = /* @__PURE__ */ F(v), b = v === t ? i : (e) => !Wn(_, e) && u(y, e), x = (e, t) => !(t && Wn(_, t));
	if (m != null && m !== p) {
		if (qn(n), g(m)) _[m] = null, b(m) && (v[m] = null);
		else if (/* @__PURE__ */ I(m)) {
			let e = n;
			x(m, e.k) && (m.value = null), e.k && (_[e.k] = null);
		}
	}
	if (h(p)) an(p, f, 12, [l, _]);
	else {
		let t = g(p), n = /* @__PURE__ */ I(p);
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
function Xn(e, t, n = Q, r = !1) {
	if (n) {
		let i = n[e] || (n[e] = []), a = t.__weh ||= (...r) => {
			Ue();
			let i = xi(n), a = on(t, n, e, r);
			return i(), We(), a;
		};
		return r ? i.unshift(a) : i.push(a), a;
	}
}
var Zn = (e) => (t, n = Q) => {
	(!wi || e === "sp") && Xn(e, (...e) => t(...e), n);
}, Qn = Zn("m"), $n = Zn("bum"), er = /* @__PURE__ */ Symbol.for("v-ndc");
function V(e, t, n, r) {
	let i, a = n && n[r], o = d(e);
	if (o || g(e)) {
		let n = o && /* @__PURE__ */ Rt(e), r = !1, s = !1;
		n && (r = !/* @__PURE__ */ Bt(e), s = /* @__PURE__ */ zt(e), e = nt(e)), i = Array(e.length);
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
var tr = (e) => e ? Ci(e) ? ji(e) : tr(e.parent) : null, nr = /* @__PURE__ */ s(/* @__PURE__ */ Object.create(null), {
	$: (e) => e,
	$el: (e) => e.vnode.el,
	$data: (e) => e.data,
	$props: (e) => e.props,
	$attrs: (e) => e.attrs,
	$slots: (e) => e.slots,
	$refs: (e) => e.refs,
	$parent: (e) => tr(e.parent),
	$root: (e) => tr(e.root),
	$host: (e) => e.ce,
	$emit: (e) => e.emit,
	$options: (e) => e.type,
	$forceUpdate: (e) => e.f ||= () => {
		_n(e.update);
	},
	$nextTick: (e) => e.n ||= hn.bind(e.proxy),
	$watch: (e) => r
}), rr = (e, n) => e !== t && !e.__isScriptSetup && u(e, n), ir = {
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
			else if (rr(i, n)) return s[n] = 1, i[n];
			else if (u(o, n)) return s[n] = 3, o[n];
			else if (r !== t && u(r, n)) return s[n] = 4, r[n];
			else s[n] = 0;
		}
		let d = nr[n], f, p;
		if (d) return n === "$attrs" && P(e.attrs, "get", ""), d(e);
		if ((f = c.__cssModules) && (f = f[n])) return f;
		if (r !== t && u(r, n)) return s[n] = 4, r[n];
		if (p = l.config.globalProperties, u(p, n)) return p[n];
	},
	set({ _: e }, t, n) {
		let { data: r, setupState: i, ctx: a } = e;
		return rr(i, t) ? (i[t] = n, !0) : u(e.props, t) || t[0] === "$" && t.slice(1) in e ? !1 : (a[t] = n, !0);
	},
	has({ _: { data: e, setupState: t, accessCache: n, ctx: r, appContext: i, props: a, type: o } }, s) {
		let c;
		return !!(n[s] || rr(t, s) || u(a, s) || u(r, s) || u(nr, s) || u(i.config.globalProperties, s) || (c = o.__cssModules) && c[s]);
	},
	defineProperty(e, t, n) {
		return n.get == null ? u(n, "value") && this.set(e, t, n.value, null) : e._.accessCache[t] = 0, Reflect.defineProperty(e, t, n);
	}
};
function ar() {
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
var or = 0;
function sr(e, t) {
	return function(n, r = null) {
		h(n) || (n = s({}, n)), r != null && !v(r) && (r = null);
		let i = ar(), a = /* @__PURE__ */ new WeakSet(), o = [], c = !1, l = i.app = {
			_uid: or++,
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
					let u = l._ceVNode || Y(n, r);
					return u.appContext = i, s === !0 ? s = "svg" : s === !1 && (s = void 0), o && t ? t(u, a) : e(u, a, s), c = !0, l._container = a, a.__vue_app__ = l, ji(u.component);
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
				let t = cr;
				cr = l;
				try {
					return e();
				} finally {
					cr = t;
				}
			}
		};
		return l;
	};
}
var cr = null, lr = (e, t) => t === "modelValue" || t === "model-value" ? e.modelModifiers : e[`${t}Modifiers`] || e[`${D(t)}Modifiers`] || e[`${k(t)}Modifiers`];
function ur(e, n, ...r) {
	if (e.isUnmounted) return;
	let i = e.vnode.props || t, a = r, o = n.startsWith("update:"), s = o && lr(i, n.slice(7));
	s && (s.trim && (a = r.map((e) => g(e) ? e.trim() : e)), s.number && (a = a.map(oe)));
	let c, l = i[c = ne(n)] || i[c = ne(D(n))];
	!l && o && (l = i[c = ne(k(n))]), l && on(l, e, 6, a);
	let u = i[c + "Once"];
	if (u) {
		if (!e.emitted) e.emitted = {};
		else if (e.emitted[c]) return;
		e.emitted[c] = !0, on(u, e, 6, a);
	}
}
function dr(e, t, n = !1) {
	let r = t.emitsCache, i = r.get(e);
	if (i !== void 0) return i;
	let a = e.emits, o = {};
	return a ? (d(a) ? a.forEach((e) => o[e] = null) : s(o, a), v(e) && r.set(e, o), o) : (v(e) && r.set(e, null), null);
}
function fr(e, t) {
	return !e || !a(t) ? !1 : (t = t.slice(2), t = t === "Once" ? t : t.replace(/Once$/, ""), u(e, t[0].toLowerCase() + t.slice(1)) || u(e, k(t)) || u(e, t));
}
function pr(e) {
	let { type: t, vnode: n, proxy: r, withProxy: i, propsOptions: [a], slots: s, attrs: c, emit: l, render: u, renderCache: d, props: f, data: p, setupState: m, ctx: h, inheritAttrs: g } = e, _ = En(e), v, y;
	try {
		if (n.shapeFlag & 4) {
			let e = i || r, t = e;
			v = ui(u.call(t, e, d, f, m, p, h)), y = c;
		} else {
			let e = t;
			v = ui(e.length > 1 ? e(f, {
				attrs: c,
				slots: s,
				emit: l
			}) : e(f, null)), y = t.props ? c : mr(c);
		}
	} catch (t) {
		Qr.length = 0, sn(t, e, 1), v = Y(Xr);
	}
	let b = v;
	if (y && g !== !1) {
		let e = Object.keys(y), { shapeFlag: t } = b;
		e.length && t & 7 && (a && e.some(o) && (y = hr(y, a)), b = li(b, y, !1, !0));
	}
	return n.dirs && (b = li(b, null, !1, !0), b.dirs = b.dirs ? b.dirs.concat(n.dirs) : n.dirs), n.transition && Vn(Ln(b.type) && Bn(b) || b, n.transition), v = b, En(_), v;
}
var mr = (e) => {
	let t;
	for (let n in e) (n === "class" || n === "style" || a(n)) && ((t ||= {})[n] = e[n]);
	return t;
}, hr = (e, t) => {
	let n = {};
	for (let r in e) (!o(r) || !(r.slice(9) in t)) && (n[r] = e[r]);
	return n;
};
function gr(e, t, n) {
	let { props: r, children: i, component: a } = e, { props: o, children: s, patchFlag: c } = t, l = a.emitsOptions;
	if (t.dirs || t.transition) return !0;
	if (n && c >= 0) {
		if (c & 1024) return !0;
		if (c & 16) return r ? _r(r, o, l) : !!o;
		if (c & 8) {
			let e = t.dynamicProps;
			for (let t = 0; t < e.length; t++) {
				let n = e[t];
				if (vr(o, r, n) && !fr(l, n)) return !0;
			}
		}
	} else return (i || s) && (!s || !s.$stable) ? !0 : r === o ? !1 : r ? !o || _r(r, o, l) : !!o;
	return !1;
}
function _r(e, t, n) {
	let r = Object.keys(t);
	if (r.length !== Object.keys(e).length) return !0;
	for (let i = 0; i < r.length; i++) {
		let a = r[i];
		if (vr(t, e, a) && !fr(n, a)) return !0;
	}
	return !1;
}
function vr(e, t, n) {
	let r = e[n], i = t[n];
	return n === "style" && v(r) && v(i) ? !be(r, i) : r !== i;
}
function yr({ vnode: e, parent: t, suspense: n }, r) {
	for (; t;) {
		let n = t.subTree;
		if (n.suspense && n.suspense.activeBranch === e && (n.suspense.vnode.el = n.el = r, e = n), n === e) (e = t.vnode).el = r, t = t.parent;
		else break;
	}
	n && n.activeBranch === e && (n.vnode.el = r);
}
var br = {}, xr = () => Object.create(br), Sr = (e) => Object.getPrototypeOf(e) === br;
function Cr(e, t, n, r = !1) {
	let i = {}, a = xr();
	e.propsDefaults = /* @__PURE__ */ Object.create(null), Tr(e, t, i, a);
	for (let t in e.propsOptions[0]) t in i || (i[t] = void 0);
	e.props = n ? r ? i : /* @__PURE__ */ Ft(i) : e.type.props ? i : a, e.attrs = a;
}
function wr(e, t, n, r) {
	let { props: i, attrs: a, vnode: { patchFlag: o } } = e, s = /* @__PURE__ */ F(i), [c] = e.propsOptions, l = !1;
	if ((r || o > 0) && !(o & 16)) {
		if (o & 8) {
			let n = e.vnode.dynamicProps;
			for (let r = 0; r < n.length; r++) {
				let o = n[r];
				if (fr(e.emitsOptions, o)) continue;
				let d = t[o];
				if (c) {
					if (u(a, o)) d !== a[o] && (a[o] = d, l = !0);
					else {
						let t = D(o);
						i[t] = Er(c, s, t, d, e, !1);
					}
				} else d !== a[o] && (a[o] = d, l = !0);
			}
		}
	} else {
		Tr(e, t, i, a) && (l = !0);
		let r;
		for (let a in s) (!t || !u(t, a) && ((r = k(a)) === a || !u(t, r))) && (c ? n && (n[a] !== void 0 || n[r] !== void 0) && (i[a] = Er(c, s, a, void 0, e, !0)) : delete i[a]);
		if (a !== s) for (let e in a) (!t || !u(t, e)) && (delete a[e], l = !0);
	}
	l && et(e.attrs, "set", "");
}
function Tr(e, n, r, i) {
	let [a, o] = e.propsOptions, s = !1, c;
	if (n) for (let t in n) {
		if (ee(t)) continue;
		let l = n[t], d;
		a && u(a, d = D(t)) ? !o || !o.includes(d) ? r[d] = l : (c ||= {})[d] = l : fr(e.emitsOptions, t) || (!(t in i) || l !== i[t]) && (i[t] = l, s = !0);
	}
	if (o) {
		let n = /* @__PURE__ */ F(r), i = c || t;
		for (let t = 0; t < o.length; t++) {
			let s = o[t];
			r[s] = Er(a, n, s, i[s], e, !u(i, s));
		}
	}
	return s;
}
function Er(e, t, n, r, i, a) {
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
function Dr(e, r, i = !1) {
	let a = r.propsCache, o = a.get(e);
	if (o) return o;
	let c = e.props, l = {}, f = [];
	if (!c) return v(e) && a.set(e, n), n;
	if (d(c)) for (let e = 0; e < c.length; e++) {
		let n = D(c[e]);
		Or(n) && (l[n] = t);
	}
	else if (c) for (let e in c) {
		let t = D(e);
		if (Or(t)) {
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
function Or(e) {
	return e[0] !== "$" && !ee(e);
}
var kr = (e) => e === "_" || e === "_ctx" || e === "$stable", Ar = (e) => d(e) ? e.map(ui) : [ui(e)], jr = (e, t, n) => {
	if (t._n) return t;
	let r = Dn((...e) => Ar(t(...e)), n);
	return r._c = !1, r;
}, Mr = (e, t, n) => {
	let r = e._ctx;
	for (let n in e) {
		if (kr(n)) continue;
		let i = e[n];
		if (h(i)) t[n] = jr(n, i, r);
		else if (i != null) {
			let e = Ar(i);
			t[n] = () => e;
		}
	}
}, Nr = (e, t) => {
	let n = Ar(t);
	e.slots.default = () => n;
}, Pr = (e, t, n) => {
	for (let r in t) (n || !kr(r)) && (e[r] = t[r]);
}, Fr = (e, t, n) => {
	let r = e.slots = xr();
	if (e.vnode.shapeFlag & 32) {
		let e = t._;
		e ? (Pr(r, t, n), n && ae(r, "_", e, !0)) : Mr(t, r);
	} else t && Nr(e, t);
}, Ir = (e, n, r) => {
	let { vnode: i, slots: a } = e, o = !0, s = t;
	if (i.shapeFlag & 32) {
		let e = n._;
		e ? r && e === 1 ? o = !1 : Pr(a, n, r) : (o = !n.$stable, Mr(n, a)), s = n;
	} else n && (Nr(e, n), s = { default: 1 });
	if (o) for (let e in a) !kr(e) && s[e] == null && delete a[e];
}, H = Jr;
function Lr(e) {
	return Rr(e);
}
function Rr(e, i) {
	let a = le();
	a.__VUE__ = !0;
	let { insert: o, remove: s, patchProp: c, createElement: l, createText: u, createComment: d, setText: f, setElementText: p, parentNode: m, nextSibling: h, setScopeId: g = r, insertStaticContent: _ } = e, v = (e, t, n, r = null, i = null, a = null, o = void 0, s = null, c = !!t.dynamicChildren) => {
		if (e === t) return;
		e && !ii(e, t) && (r = ve(e), me(e, i, a, !0), e = null), t.patchFlag === -2 && (c = !1, t.dynamicChildren = null);
		let { type: l, ref: u, shapeFlag: d } = t;
		switch (l) {
			case Yr:
				y(e, t, n, r);
				break;
			case Xr:
				b(e, t, n, r);
				break;
			case Zr:
				e ?? x(t, n, r, o);
				break;
			case U:
				ne(e, t, n, r, i, a, o, s, c);
				break;
			default: d & 1 ? w(e, t, n, r, i, a, o, s, c) : d & 6 ? re(e, t, n, r, i, a, o, s, c) : (d & 64 || d & 128) && l.process(e, t, n, r, i, a, o, s, c, xe);
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
		if (d = e.el = l(e.type, a, m && m.is, m), h & 8 ? p(d, e.children) : h & 16 && D(e.children, d, null, r, i, zr(e, a), s, u), _ && kn(e, null, r, "created"), E(d, e, e.scopeId, s, r), m) {
			for (let e in m) e !== "value" && !ee(e) && c(d, e, null, m[e], a, r);
			"value" in m && c(d, "value", null, m.value, a), (f = m.onVnodeBeforeMount) && mi(f, r, e);
		}
		_ && kn(e, null, r, "beforeMount");
		let v = Vr(i, g);
		v && g.beforeEnter(d), o(d, t, n), ((f = m && m.onVnodeMounted) || v || _) && H(() => {
			try {
				f && mi(f, r, e), v && g.enter(d), _ && kn(e, null, r, "mounted");
			} finally {}
		}, i);
	}, E = (e, t, n, r, i) => {
		if (n && g(e, n), r) for (let t = 0; t < r.length; t++) g(e, r[t]);
		if (i) {
			let n = i.subTree;
			if (t === n || qr(n.type) && (n.ssContent === t || n.ssFallback === t)) {
				let t = i.vnode;
				E(e, t, t.scopeId, t.slotScopeIds, i.parent);
			}
		}
	}, D = (e, t, n, r, i, a, o, s, c = 0) => {
		for (let l = c; l < e.length; l++) {
			let c = e[l] = s ? di(e[l]) : ui(e[l]);
			v(null, c, t, n, r, i, a, o, s);
		}
	}, O = (e, n, r, i, a, o, s) => {
		let l = n.el = e.el, { patchFlag: u, dynamicChildren: d, dirs: f } = n;
		u |= e.patchFlag & 16;
		let m = e.props || t, h = n.props || t, g;
		if (r && Br(r, !1), (g = h.onVnodeBeforeUpdate) && mi(g, r, n, e), f && kn(n, e, r, "beforeUpdate"), r && Br(r, !0), d && (!e.dynamicChildren || e.dynamicChildren.length !== d.length) && (u = 0, s = !1, d = null), (m.innerHTML && h.innerHTML == null || m.textContent && h.textContent == null) && p(l, ""), d ? k(e.dynamicChildren, d, l, r, i, zr(n, a), o) : s || ue(e, n, l, null, r, i, zr(n, a), o, !1), u > 0) {
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
		((g = h.onVnodeUpdated) || f) && H(() => {
			g && mi(g, r, n, e), f && kn(n, e, r, "updated");
		}, i);
	}, k = (e, t, n, r, i, a, o) => {
		for (let s = 0; s < t.length; s++) {
			let c = e[s], l = t[s], u = c.el && (c.type === U || !ii(c, l) || c.shapeFlag & 198) ? m(c.el) : n;
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
		h && (c = c ? c.concat(h) : h), e == null ? (o(d, n, r), o(f, n, r), D(t.children || [], n, f, i, a, s, c, l)) : p > 0 && p & 64 && m && e.dynamicChildren && e.dynamicChildren.length === m.length ? (k(e.dynamicChildren, m, n, i, a, s, c), (t.key != null || i && t === i.subTree) && Hr(e, t, !0)) : ue(e, t, n, f, i, a, s, c, l);
	}, re = (e, t, n, r, i, a, o, s, c) => {
		t.slotScopeIds = s, e == null ? t.shapeFlag & 512 ? i.ctx.activate(t, n, r, o, c) : ae(t, n, r, i, a, o, c) : oe(e, t, c);
	}, ae = (e, t, n, r, i, a, o) => {
		let s = e.component = _i(e, r, i);
		if (Yn(e) && (s.ctx.renderer = xe), Ti(s, !1, o), s.asyncDep) {
			if (i && i.registerDep(s, se, o), !e.el) {
				let r = s.subTree = Y(Xr);
				b(null, r, t, n), e.placeholder = r.el;
			}
		} else se(s, e, t, n, i, a, o);
	}, oe = (e, t, n) => {
		let r = t.component = e.component;
		if (gr(e, t, n)) {
			if (r.asyncDep && !r.asyncResolved) {
				ce(r, t, n);
				return;
			}
			r.next = t, r.update();
		} else t.el = e.el, r.vnode = t;
	}, se = (e, t, n, r, i, a, o) => {
		let s = () => {
			if (e.isMounted) {
				let { next: t, bu: n, u: r, parent: s, vnode: c } = e;
				{
					let n = Wr(e);
					if (n) {
						t && (t.el = c.el, ce(e, t, o)), n.asyncDep.then(() => {
							H(() => {
								e.isUnmounted || l();
							}, i);
						});
						return;
					}
				}
				let u = t, d;
				Br(e, !1), t ? (t.el = c.el, ce(e, t, o)) : t = c, n && ie(n), (d = t.props && t.props.onVnodeBeforeUpdate) && mi(d, s, t, c), Br(e, !0);
				let f = pr(e), p = e.subTree;
				e.subTree = f, v(p, f, m(p.el), ve(p), e, i, a), t.el = f.el, u === null && yr(e, f.el), r && H(r, i), (d = t.props && t.props.onVnodeUpdated) && H(() => mi(d, s, t, c), i);
			} else {
				let o, { el: s, props: c } = t, { bm: l, m: u, parent: d, root: f, type: p } = e, m = Jn(t);
				if (Br(e, !1), l && ie(l), !m && (o = c && c.onVnodeBeforeMount) && mi(o, d, t), Br(e, !0), s && Se) {
					let t = () => {
						e.subTree = pr(e), Se(s, e.subTree, e, i, null);
					};
					m && p.__asyncHydrate ? p.__asyncHydrate(s, e, t) : t();
				} else {
					f.ce && f.ce._hasShadowRoot() && f.ce._injectChildStyle(p, e.parent ? e.parent.type : void 0);
					let o = e.subTree = pr(e);
					v(null, o, n, r, e, i, a), t.el = o.el;
				}
				if (u && H(u, i), !m && (o = c && c.onVnodeMounted)) {
					let e = t;
					H(() => mi(o, d, e), i);
				}
				(t.shapeFlag & 256 || d && Jn(d.vnode) && d.vnode.shapeFlag & 256) && e.a && H(e.a, i), e.isMounted = !0, t = n = r = null;
			}
		};
		e.scope.on();
		let c = e.effect = new Oe(s);
		e.scope.off();
		let l = e.update = c.run.bind(c), u = e.job = c.runIfDirty.bind(c);
		u.i = e, u.id = e.uid, c.scheduler = () => _n(u), Br(e, !0), l();
	}, ce = (e, t, n) => {
		t.component = e;
		let r = e.vnode.props;
		e.vnode = t, e.next = null, wr(e, t.props, r, n), Ir(e, t.children, n), Ue(), bn(e), We();
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
		m & 8 ? (u & 16 && _e(l, i, a), d !== l && p(n, d)) : u & 16 ? m & 16 ? fe(l, d, n, r, i, a, o, s, c) : _e(l, i, a, !0) : (u & 8 && p(n, ""), m & 16 && D(d, n, r, i, a, o, s, c));
	}, de = (e, t, r, i, a, o, s, c, l) => {
		e ||= n, t ||= n;
		let u = e.length, d = t.length, f = Math.min(u, d), p = 0;
		for (; p < f; p++) {
			let n = t[p] = l ? di(t[p]) : ui(t[p]);
			v(e[p], n, r, null, a, o, s, c, l);
		}
		u > d ? _e(e, a, o, !0, !1, f) : D(t, r, i, a, o, s, c, l, f);
	}, fe = (e, t, r, i, a, o, s, c, l) => {
		let u = 0, d = t.length, f = e.length - 1, p = d - 1;
		for (; u <= f && u <= p;) {
			let n = e[u], i = t[u] = l ? di(t[u]) : ui(t[u]);
			if (ii(n, i)) v(n, i, r, null, a, o, s, c, l);
			else break;
			u++;
		}
		for (; u <= f && u <= p;) {
			let n = e[f], i = t[p] = l ? di(t[p]) : ui(t[p]);
			if (ii(n, i)) v(n, i, r, null, a, o, s, c, l);
			else break;
			f--, p--;
		}
		if (u > f) {
			if (u <= p) {
				let e = p + 1, n = e < d ? t[e].el : i;
				for (; u <= p;) v(null, t[u] = l ? di(t[u]) : ui(t[u]), r, n, a, o, s, c, l), u++;
			}
		} else if (u > p) for (; u <= f;) me(e[u], a, o, !0), u++;
		else {
			let m = u, h = u, g = /* @__PURE__ */ new Map();
			for (u = h; u <= p; u++) {
				let e = t[u] = l ? di(t[u]) : ui(t[u]);
				e.key != null && g.set(e.key, u);
			}
			let _, y = 0, b = p - h + 1, x = !1, S = 0, C = Array(b);
			for (u = 0; u < b; u++) C[u] = 0;
			for (u = m; u <= f; u++) {
				let n = e[u];
				if (y >= b) {
					me(n, a, o, !0);
					continue;
				}
				let i;
				if (n.key != null) i = g.get(n.key);
				else for (_ = h; _ <= p; _++) if (C[_ - h] === 0 && ii(n, t[_])) {
					i = _;
					break;
				}
				i === void 0 ? me(n, a, o, !0) : (C[i - h] = u + 1, i >= S ? S = i : x = !0, v(n, t[i], r, null, a, o, s, c, l), y++);
			}
			let w = x ? Ur(C) : n;
			for (_ = w.length - 1, u = b - 1; u >= 0; u--) {
				let e = h + u, n = t[e], f = t[e + 1], p = e + 1 < d ? f.el || Kr(f) : i;
				C[u] === 0 ? v(null, n, r, p, a, o, s, c, l) : x && (_ < 0 || u !== w[_] ? pe(n, r, p, 2) : _--);
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
		if (c === Zr) {
			S(e, t, n);
			return;
		}
		if (r !== 2 && d & 1 && l) {
			if (r === 0) l.persisted && !a[Rn] ? o(a, t, n) : (l.beforeEnter(a), o(a, t, n), H(() => l.enter(a), i));
			else {
				let { leave: r, delayLeave: i, afterLeave: c } = l, u = () => {
					e.ctx.isUnmounted ? s(a) : o(a, t, n);
				}, d = () => {
					let e = a._isLeaving || !!a[Rn];
					a._isLeaving && a[Rn](!0), l.persisted && !e ? u() : r(a, () => {
						u(), c && c();
					});
				};
				i ? i(a, u, d) : d();
			}
		} else o(a, t, n);
	}, me = (e, t, n, r = !1, i = !1) => {
		let { type: a, props: o, ref: s, children: c, dynamicChildren: l, shapeFlag: u, patchFlag: d, dirs: f, cacheIndex: p, memo: m } = e;
		if (d === -2 && (i = !1), s != null && (Ue(), Kn(s, null, n, e, !0), We()), p != null && (t.renderCache[p] = void 0), u & 256) {
			t.ctx.deactivate(e);
			return;
		}
		let h = u & 1 && f, g = !Jn(e), _;
		if (g && (_ = o && o.onVnodeBeforeUnmount) && mi(_, t, e), u & 6) ge(e.component, n, r);
		else {
			if (u & 128) {
				e.suspense.unmount(n, r);
				return;
			}
			h && kn(e, null, t, "beforeUnmount"), u & 64 ? e.type.remove(e, t, n, xe, r) : l && !l.hasOnce && (a !== U || d > 0 && d & 64) ? _e(l, t, n, !1, !0) : (a === U && d & 384 || !i && u & 16) && _e(c, t, n), r && A(e);
		}
		let v = m != null && p == null;
		(g && (_ = o && o.onVnodeUnmounted) || h || v) && H(() => {
			_ && mi(_, t, e), h && kn(e, null, t, "unmounted"), v && (e.el = null);
		}, n);
	}, A = (e) => {
		let { type: t, el: n, anchor: r, transition: i } = e;
		if (t === U) {
			he(n, r);
			return;
		}
		if (t === Zr) {
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
	}, he = (e, t) => {
		let n;
		for (; e !== t;) n = h(e), s(e), e = n;
		s(t);
	}, ge = (e, t, n) => {
		let { bum: r, scope: i, job: a, subTree: o, um: s, m: c, a: l } = e;
		Gr(c), Gr(l), r && ie(r), i.stop(), a && (a.flags |= 8, me(o, e, t, n)), s && H(s, t), H(() => {
			e.isUnmounted = !0;
		}, t);
	}, _e = (e, t, n, r = !1, i = !1, a = 0) => {
		for (let o = a; o < e.length; o++) me(e[o], t, n, r, i);
	}, ve = (e) => {
		if (e.shapeFlag & 6) return ve(e.component.subTree);
		if (e.shapeFlag & 128) return e.suspense.next();
		let t = h(e.anchor || e.el), n = t && t[In];
		return n ? h(n) : t;
	}, ye = !1, be = (e, t, n) => {
		let r;
		e == null ? t._vnode && (me(t._vnode, null, null, !0), r = t._vnode.component) : v(t._vnode || null, e, t, null, null, null, n), t._vnode = e, ye ||= (ye = !0, bn(r), xn(), !1);
	}, xe = {
		p: v,
		um: me,
		m: pe,
		r: A,
		mt: ae,
		mc: D,
		pc: ue,
		pbc: k,
		n: ve,
		o: e
	}, j, Se;
	return i && ([j, Se] = i(xe)), {
		render: be,
		hydrate: j,
		createApp: sr(be, j)
	};
}
function zr({ type: e, props: t }, n) {
	return n === "svg" && e === "foreignObject" || n === "mathml" && e === "annotation-xml" && t && t.encoding && t.encoding.includes("html") ? void 0 : n;
}
function Br({ effect: e, job: t }, n) {
	n ? (e.flags |= 32, t.flags |= 4) : (e.flags &= -33, t.flags &= -5);
}
function Vr(e, t) {
	return (!e || e && !e.pendingBranch) && t && !t.persisted;
}
function Hr(e, t, n = !1) {
	let r = e.children, i = t.children;
	if (d(r) && d(i)) for (let e = 0; e < r.length; e++) {
		let t = r[e], a = i[e];
		a.shapeFlag & 1 && !a.dynamicChildren && ((a.patchFlag <= 0 || a.patchFlag === 32) && (a = i[e] = di(i[e]), a.el = t.el), !n && a.patchFlag !== -2 && Hr(t, a)), a.type === Yr && (a.patchFlag === -1 && (a = i[e] = di(a)), a.el = t.el), a.type === Xr && !a.el && (a.el = t.el);
	}
}
function Ur(e) {
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
function Wr(e) {
	let t = e.subTree.component;
	if (t) return t.asyncDep && !t.asyncResolved ? t : Wr(t);
}
function Gr(e) {
	if (e) for (let t = 0; t < e.length; t++) e[t].flags |= 8;
}
function Kr(e) {
	if (e.placeholder) return e.placeholder;
	let t = e.component;
	return t ? Kr(t.subTree) : null;
}
var qr = (e) => e.__isSuspense;
function Jr(e, t) {
	t && t.pendingBranch ? d(e) ? t.effects.push(...e) : t.effects.push(e) : yn(e);
}
var U = /* @__PURE__ */ Symbol.for("v-fgt"), Yr = /* @__PURE__ */ Symbol.for("v-txt"), Xr = /* @__PURE__ */ Symbol.for("v-cmt"), Zr = /* @__PURE__ */ Symbol.for("v-stc"), Qr = [], W = null;
function G(e = !1) {
	Qr.push(W = e ? null : []);
}
function $r() {
	Qr.pop(), W = Qr[Qr.length - 1] || null;
}
var ei = 1;
function ti(e, t = !1) {
	ei += e, e < 0 && W && t && (W.hasOnce = !0);
}
function ni(e) {
	return e.dynamicChildren = ei > 0 ? W || n : null, $r(), ei > 0 && W && W.push(e), e;
}
function K(e, t, n, r, i, a) {
	return ni(J(e, t, n, r, i, a, !0));
}
function q(e, t, n, r, i) {
	return ni(Y(e, t, n, r, i, !0));
}
function ri(e) {
	return e ? e.__v_isVNode === !0 : !1;
}
function ii(e, t) {
	return e.type === t.type && e.key === t.key;
}
var ai = ({ key: e }) => e ?? null, oi = ({ ref: e, ref_key: t, ref_for: n }) => (typeof e == "number" && (e = "" + e), e == null ? null : g(e) || /* @__PURE__ */ I(e) || h(e) ? {
	i: wn,
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
		key: t && ai(t),
		ref: t && oi(t),
		scopeId: Tn,
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
		ctx: wn
	};
	return s ? (fi(c, n), a & 128 && e.normalize(c)) : n && (c.shapeFlag |= g(n) ? 8 : 16), ei > 0 && !o && W && (c.patchFlag > 0 || a & 6) && c.patchFlag !== 32 && W.push(c), c;
}
var Y = si;
function si(e, t = null, n = null, r = 0, i = null, a = !1) {
	if ((!e || e === er) && (e = Xr), ri(e)) {
		let r = li(e, t, !0);
		return n && fi(r, n), ei > 0 && !a && W && (r.shapeFlag & 6 ? W[W.indexOf(e)] = r : W.push(r)), r.patchFlag = -2, r;
	}
	if (Mi(e) && (e = e.__vccOpts), t) {
		t = ci(t);
		let { class: e, style: n } = t;
		e && !g(e) && (t.class = A(e)), v(n) && (/* @__PURE__ */ Vt(n) && !d(n) && (n = s({}, n)), t.style = ue(n));
	}
	let o = g(e) ? 1 : qr(e) ? 128 : Ln(e) ? 64 : v(e) ? 4 : h(e) ? 2 : 0;
	return J(e, t, n, r, i, o, a, !0);
}
function ci(e) {
	return e ? /* @__PURE__ */ Vt(e) || Sr(e) ? s({}, e) : e : null;
}
function li(e, t, n = !1, r = !1) {
	let { props: i, ref: a, patchFlag: o, children: s, transition: c } = e, l = t ? pi(i || {}, t) : i, u = {
		__v_isVNode: !0,
		__v_skip: !0,
		type: e.type,
		props: l,
		key: l && ai(l),
		ref: t && t.ref ? n && a ? d(a) ? a.concat(oi(t)) : [a, oi(t)] : oi(t) : a,
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
		ssContent: e.ssContent && li(e.ssContent),
		ssFallback: e.ssFallback && li(e.ssFallback),
		placeholder: e.placeholder,
		el: e.el,
		anchor: e.anchor,
		ctx: e.ctx,
		ce: e.ce
	};
	return c && r && Vn(u, c.clone(u)), u;
}
function X(e = " ", t = 0) {
	return Y(Yr, null, e, t);
}
function Z(e = "", t = !1) {
	return t ? (G(), q(Xr, null, e)) : Y(Xr, null, e);
}
function ui(e) {
	return e == null || typeof e == "boolean" ? Y(Xr) : d(e) ? Y(U, null, e.slice()) : ri(e) ? di(e) : Y(Yr, null, String(e));
}
function di(e) {
	return e.el === null && e.patchFlag !== -1 || e.memo ? e : li(e);
}
function fi(e, t) {
	let n = 0, { shapeFlag: r } = e;
	if (t == null) t = null;
	else if (d(t)) n = 16;
	else if (typeof t == "object") {
		if (r & 65) {
			let n = t.default;
			n && (n._c && (n._d = !1), fi(e, n()), n._c && (n._d = !0));
			return;
		}
		{
			n = 32;
			let r = t._;
			!r && !Sr(t) ? t._ctx = wn : r === 3 && wn && (wn.slots._ === 1 ? t._ = 1 : (t._ = 2, e.patchFlag |= 1024));
		}
	} else if (h(t)) {
		if (r & 65) {
			fi(e, { default: t });
			return;
		}
		t = {
			default: t,
			_ctx: wn
		}, n = 32;
	} else t = String(t), r & 64 ? (n = 16, t = [X(t)]) : n = 8;
	e.children = t, e.shapeFlag |= n;
}
function pi(...e) {
	let t = {};
	for (let n = 0; n < e.length; n++) {
		let r = e[n];
		for (let e in r) if (e === "class") t.class !== r.class && (t.class = A([t.class, r.class]));
		else if (e === "style") t.style = ue([t.style, r.style]);
		else if (a(e)) {
			let n = t[e], i = r[e];
			i && n !== i && !(d(n) && n.includes(i)) ? t[e] = n ? [].concat(n, i) : i : i == null && n == null && !o(e) && (t[e] = i);
		} else e !== "" && (t[e] = r[e]);
	}
	return t;
}
function mi(e, t, n, r = null) {
	on(e, t, 7, [n, r]);
}
var hi = ar(), gi = 0;
function _i(e, n, r) {
	let i = e.type, a = (n ? n.appContext : e.appContext) || hi, o = {
		uid: gi++,
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
		scope: new we(!0),
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
		propsOptions: Dr(i, a),
		emitsOptions: dr(i, a),
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
	return o.ctx = { _: o }, o.root = n ? n.root : o, o.emit = ur.bind(null, o), e.ce && e.ce(o), o;
}
var Q = null, vi = () => Q || wn, yi, bi;
{
	let e = le(), t = (t, n) => {
		let r;
		return (r = e[t]) || (r = e[t] = []), r.push(n), (e) => {
			r.length > 1 ? r.forEach((t) => t(e)) : r[0](e);
		};
	};
	yi = t("__VUE_INSTANCE_SETTERS__", (e) => Q = e), bi = t("__VUE_SSR_SETTERS__", (e) => wi = e);
}
var xi = (e) => {
	let t = Q;
	return yi(e), e.scope.on(), () => {
		e.scope.off(), yi(t);
	};
}, Si = () => {
	Q && Q.scope.off(), yi(null);
};
function Ci(e) {
	return e.vnode.shapeFlag & 4;
}
var wi = !1;
function Ti(e, t = !1, n = !1) {
	t && bi(t);
	let { props: r, children: i } = e.vnode, a = Ci(e);
	Cr(e, r, a, t), Fr(e, i, n || t);
	let o = a ? Ei(e, t) : void 0;
	return t && bi(!1), o;
}
function Ei(e, t) {
	let n = e.type;
	e.accessCache = /* @__PURE__ */ Object.create(null), e.proxy = new Proxy(e.ctx, ir);
	let { setup: r } = n;
	if (r) {
		Ue();
		let n = e.setupContext = r.length > 1 ? Ai(e) : null, i = xi(e), a = an(r, e, 0, [e.props, n]), o = y(a);
		if (We(), i(), (o || e.sp) && !Jn(e) && Un(e), o) {
			if (a.then(Si, Si), t) return a.then((n) => {
				bi(!0);
				try {
					Di(e, n, t);
				} finally {
					bi(!1);
				}
			}).catch((t) => {
				sn(t, e, 0);
			});
			e.asyncDep = a;
		} else Di(e, a, t);
	} else Oi(e, t);
}
function Di(e, t, n) {
	h(t) ? e.type.__ssrInlineRender ? e.ssrRender = t : e.render = t : v(t) && (e.setupState = Yt(t)), Oi(e, n);
}
function Oi(e, t, n) {
	let i = e.type;
	e.render ||= i.render || r;
}
var ki = { get(e, t) {
	return P(e, "get", ""), e[t];
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
	return e.exposed ? e.exposeProxy ||= new Proxy(Yt(Ht(e.exposed)), {
		get(t, n) {
			if (n in t) return t[n];
			if (n in nr) return nr[n](e);
		},
		has(e, t) {
			return t in e || t in nr;
		}
	}) : e.proxy;
}
function Mi(e) {
	return h(e) && "__vccOpts" in e;
}
var $ = (e, t) => /* @__PURE__ */ Zt(e, t, wi), Ni = "3.5.42", Pi = void 0, Fi = typeof window < "u" && window.trustedTypes;
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
function ia(e, t, n, r, i, a = ge(t)) {
	r && t.startsWith("xlink:") ? n == null ? e.removeAttributeNS(ra, t.slice(6, t.length)) : e.setAttributeNS(ra, t, n) : n == null || a && !_e(n) ? e.removeAttribute(t) : e.setAttribute(t, a ? "" : _(n) ? String(n) : n);
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
		r === "boolean" ? n = _e(n) : n == null && r === "string" ? (n = "", o = !0) : r === "number" && (n = 0, o = !0);
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
				e && on(e, t, 5, a);
			}
		} else on(r, t, 5, [e]);
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
	let r = /* @__PURE__ */ B(e, t);
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
				(t === Number || t && t.type === Number) && (e in this._props && (this._props[e] = se(this._props[e])), (i ||= /* @__PURE__ */ Object.create(null))[D(e)] = !0);
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
		if (t) for (let e in t) u(this, e) || Object.defineProperty(this, e, { get: () => R(t[e]) });
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
		t && this._numberProps && this._numberProps[r] && (n = se(n)), this._setProp(r, n, !1, !0);
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
		let t = Y(this._def, s(e, this._props));
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
	return d(t) ? (e) => ie(t, e) : t;
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
	return t && (e = e.trim()), n && (e = oe(e)), e;
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
		let s = (a || e.type === "number") && !/^0\d/.test(e.value) ? oe(e.value) : e.value, c = t ?? "";
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
	return La ||= Lr(Ia);
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
	let n = $(() => e()?.language.toLowerCase().startsWith("de") ? "de" : "en"), r = /* @__PURE__ */ L(!1), i = /* @__PURE__ */ L(!1), a = /* @__PURE__ */ L(null), o = $(() => a.value ? Ka[n.value][a.value] : null), s = /* @__PURE__ */ Gt([]), c = /* @__PURE__ */ Pt(/* @__PURE__ */ new Map()), l = /* @__PURE__ */ Pt(/* @__PURE__ */ new Map()), u = (e, n) => JSON.stringify([
		t(),
		e,
		n
	]), d = 0;
	function f(e = !0) {
		e && (d += 1), r.value = !1, s.value = [];
		for (let [e, t] of c) t.pending ? t.error = null : c.delete(e);
	}
	let p = Pn([
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
	Ee(() => {
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
		let o = /* @__PURE__ */ Pt({
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
		let s = /* @__PURE__ */ Pt({
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
		ready: /* @__PURE__ */ It(r),
		connected: /* @__PURE__ */ It(i),
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
}, po = ["aria-labelledby", "aria-describedby"], mo = ["id"], ho = ["id"], go = { class: "entity-control__confirmation-actions" }, _o = ["disabled"], vo = /*@__PURE__*/ B({
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
		let t = e, n = jn(qa), r = $(() => n?.entity(t.domain, t.entityKey)), i = Hn(), a = `sax-control-${i}`, o = `sax-status-${i}`, s = `sax-value-${i}`, c = /* @__PURE__ */ L(""), l = /* @__PURE__ */ L(), u = /* @__PURE__ */ Gt(null), d = $(() => r.value?.state?.state ?? ""), f = $(() => r.value?.state?.attributes ?? {}), p = $(() => {
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
		Pn([() => r.value?.metadata.entity_id, () => d.value], ([, e]) => {
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
		Pn([
			() => r.value?.metadata.entity_id,
			d,
			v,
			() => t.domain,
			() => t.entityKey,
			() => t.confirmSwitch
		], T, { flush: "sync" }), $n(T);
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
					u.value = e, await hn(), u.value === e && !v.value && l.value?.showModal();
					return;
				}
				await n.perform(t.domain, t.entityKey, a);
			}
		}
		async function k(e) {
			let r = e.target, i = r.value;
			r.value = d.value, !v.value && n && await n.perform(t.domain, t.entityKey, i);
		}
		return (t, n) => r.value ? (G(), K("form", {
			key: 0,
			class: A(["entity-control", {
				"entity-control--month": e.monthTile,
				"entity-control--selected": e.monthTile && r.value.available && d.value === "on"
			}]),
			"aria-busy": r.value.pending,
			onSubmit: Fa(ee, ["prevent"])
		}, [
			e.monthTile && e.domain === "switch" ? (G(), K("label", {
				key: 0,
				for: a,
				class: "entity-control__switch-target entity-control__month-target"
			}, [J("span", $a, j(r.value.name), 1), J("input", {
				id: a,
				type: "checkbox",
				role: "switch",
				checked: r.value.available && d.value === "on",
				indeterminate: !r.value.available || d.value !== "on" && d.value !== "off",
				disabled: v.value,
				"aria-describedby": o,
				onChange: O
			}, null, 40, eo)])) : (G(), K(U, { key: 1 }, [J("div", to, [J("label", {
				for: a,
				class: "entity-control__name"
			}, j(r.value.name), 1), e.domain === "switch" ? Z("", !0) : (G(), K("p", {
				key: 0,
				id: s,
				class: "entity-control__value"
			}, [e.hideConfirmedLabel ? Z("", !0) : (G(), K("span", no, j(_.value.confirmed) + ":", 1)), X(" " + j(g.value), 1)]))]), J("div", ro, [e.domain === "switch" ? (G(), K("label", {
				key: 0,
				for: a,
				class: "entity-control__switch-target"
			}, [J("input", {
				id: a,
				type: "checkbox",
				role: "switch",
				checked: d.value === "on",
				disabled: v.value,
				"aria-describedby": h.value,
				onChange: O
			}, null, 40, io)])) : e.domain === "select" ? (G(), K("select", {
				key: 1,
				id: a,
				value: r.value.available ? d.value : "",
				disabled: v.value,
				"aria-describedby": h.value,
				onChange: k
			}, [r.value.available ? Z("", !0) : (G(), K("option", oo, j(_.value.unavailable), 1)), (G(!0), K(U, null, V(p.value, (e) => (G(), K("option", {
				key: e,
				value: e
			}, j(w(e)), 9, so))), 128))], 40, ao)) : (G(), K(U, { key: 2 }, [J("input", {
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
			}, null, 40, co), J("button", {
				type: "submit",
				disabled: v.value || c.value === ""
			}, j(_.value.apply), 9, lo)], 64))])], 64)),
			J("div", {
				id: o,
				class: "entity-control__feedback"
			}, [r.value.error ? (G(), K("p", uo, j(r.value.error), 1)) : y.value ? (G(), K("p", fo, j(y.value), 1)) : Z("", !0)]),
			e.confirmSwitch ? (G(), K("dialog", {
				key: 2,
				ref_key: "dialog",
				ref: l,
				class: "entity-control__confirmation",
				"aria-labelledby": `${R(i)}-confirmation-title`,
				"aria-describedby": `${R(i)}-confirmation-question`,
				onCancel: Fa(T, ["prevent"]),
				onClose: E
			}, [
				J("h3", { id: `${R(i)}-confirmation-title` }, j(_.value.confirmationTitle), 9, mo),
				J("p", { id: `${R(i)}-confirmation-question` }, j(_.value.confirmationQuestion), 9, ho),
				J("div", go, [J("button", {
					type: "button",
					autofocus: "",
					onClick: T
				}, j(_.value.cancel), 1), J("button", {
					type: "button",
					disabled: v.value || !u.value,
					onClick: D
				}, j(u.value?.desired ? _.value.turnOn : _.value.turnOff), 9, _o)])
			], 40, po)) : Z("", !0)
		], 42, Qa)) : Z("", !0);
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
}, ko = /*#__PURE__*/ bo(/* @__PURE__ */ B({
	__name: "EntityGauge",
	props: {
		entityKey: { type: String },
		maximum: { type: Number },
		segments: { type: Array }
	},
	setup(e) {
		let t = e, n = jn(qa), r = $(() => n?.entity("sensor", t.entityKey)), i = `sax-gauge-${Hn()}`, a = $(() => {
			let e = r.value?.state?.state.trim();
			if (!r.value?.available || !e) return null;
			let t = Number(e);
			return Number.isFinite(t) ? t : null;
		}), o = $(() => a.value === null ? null : Math.max(0, Math.min(t.maximum, a.value))), s = $(() => a.value === null ? null : [...t.segments].reverse().find((e) => a.value >= e.from)?.label ?? t.segments[0]?.label), c = $(() => r.value?.available && a.value === null ? n?.language.value === "de" ? "Unbekannt" : "Unknown" : r.value?.displayValue), l = $(() => t.segments.map((e, n) => ({
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
			(G(), K("svg", Co, [n[1] ||= J("path", {
				class: "entity-gauge__track",
				d: "M20 110 A100 100 0 0 1 220 110"
			}, null, -1), o.value === null ? Z("", !0) : (G(), K(U, { key: 0 }, [
				(G(!0), K(U, null, V(l.value, (e) => (G(), K("path", {
					key: e.from,
					class: A(["entity-gauge__segment", `entity-gauge__segment--${e.color}`]),
					d: "M20 110 A100 100 0 0 1 220 110",
					pathLength: "100",
					"stroke-dasharray": `${e.length} 100`,
					"stroke-dashoffset": e.offset
				}, null, 10, wo))), 128)),
				J("line", {
					class: "entity-gauge__needle",
					x1: "120",
					y1: "110",
					x2: "120",
					y2: "33",
					transform: `rotate(${o.value / e.maximum * 180 - 90} 120 110)`
				}, null, 8, To),
				n[0] ||= J("circle", {
					class: "entity-gauge__pivot",
					cx: "120",
					cy: "110",
					r: "5"
				}, null, -1)
			], 64))])),
			J("div", Eo, [n[2] ||= J("span", null, "0", -1), J("span", null, j(e.maximum), 1)]),
			J("p", Do, j(c.value), 1),
			s.value ? (G(), K("p", Oo, j(s.value), 1)) : Z("", !0)
		], 8, So)])) : Z("", !0);
	}
}), [["styles", [".entity-gauge{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);text-align:center;padding:24px}.entity-gauge h2{overflow-wrap:anywhere;margin:0 0 20px;font-size:16px;font-weight:500;line-height:1.5}.entity-gauge__meter{max-width:260px;margin:0 auto}.entity-gauge svg{fill:none;width:100%;display:block}.entity-gauge__track,.entity-gauge__segment{stroke-width:15px;stroke-linecap:butt}.entity-gauge__track{stroke:var(--divider-color,#e0e0e0)}.entity-gauge__segment--red{stroke:var(--error-color,#db4437)}.entity-gauge__segment--yellow{stroke:var(--warning-color,#f4b400)}.entity-gauge__segment--green{stroke:var(--success-color,#0f9d58)}.entity-gauge__needle{stroke:var(--primary-text-color,#212121);stroke-width:3px;stroke-linecap:round}.entity-gauge__pivot{stroke:none;fill:var(--primary-text-color,#212121)}.entity-gauge__scale{color:var(--secondary-text-color,#666);justify-content:space-between;padding:2px 7px;font-size:12px;display:flex}.entity-gauge__value{overflow-wrap:anywhere;margin:10px 0 0;font-size:28px;font-weight:500;line-height:1.4}.entity-gauge__range{color:var(--secondary-text-color,#666);margin:4px 0 0;font-size:14px;line-height:1.5}@container sax-content (width>=860px){.entity-gauge{padding:16px}.entity-gauge h2{margin-bottom:8px}.entity-gauge__meter{max-width:180px}.entity-gauge__value{margin-top:6px;font-size:24px}.entity-gauge__range{margin-top:2px}}"]]]), Ao = {
	key: 0,
	class: "entity-value"
}, jo = { class: "entity-value__name" }, Mo = { class: "entity-value__state" }, No = /*#__PURE__*/ bo(/* @__PURE__ */ B({
	__name: "EntityValue",
	props: {
		domain: { type: null },
		entityKey: { type: String }
	},
	setup(e) {
		let t = e, n = jn(qa), r = $(() => n?.entity(t.domain, t.entityKey));
		return (e, t) => r.value ? (G(), K("div", Ao, [J("span", jo, j(r.value.name), 1), J("span", Mo, j(r.value.displayValue), 1)])) : Z("", !0);
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
}, Ro = ["aria-labelledby"], zo = ["id"], Bo = { class: "general-view__rows" }, Vo = /*#__PURE__*/ bo(/* @__PURE__ */ B({
	__name: "GeneralView",
	setup(e) {
		let t = jn(qa), n = Hn(), r = $(() => t?.language.value === "de" ? {
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
		return (e, i) => (G(), K("div", Po, [
			!R(t)?.ready.value && !R(t)?.error.value ? (G(), K("p", Fo, j(r.value.loading), 1)) : R(t)?.ready.value && !s.value ? (G(), K("p", Io, j(r.value.empty), 1)) : Z("", !0),
			o.value ? (G(), K("div", Lo, [Y(ko, {
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
			}, null, 8, ["segments"]), Y(ko, {
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
			}, null, 8, ["segments"])])) : Z("", !0),
			(G(!0), K(U, null, V(a.value, (e) => (G(), K("section", {
				key: e.title,
				class: A(["general-view__card", `general-view__card--${e.title}`]),
				"aria-labelledby": `${R(n)}-${e.title}`
			}, [J("h2", { id: `${R(n)}-${e.title}` }, j(r.value[e.title]), 9, zo), J("div", Bo, [(G(!0), K(U, null, V(e.entities, ([e, t]) => (G(), K(U, { key: `${e}.${t}` }, [e === "number" || e === "switch" ? (G(), q(xo, {
				key: 0,
				domain: e,
				"entity-key": t,
				"confirm-switch": e === "switch" && t === "storage_switch"
			}, null, 8, [
				"domain",
				"entity-key",
				"confirm-switch"
			])) : (G(), q(No, {
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
}, rs = { class: "month-selection__missing-target" }, is = ["aria-describedby"], as = ["id"], os = /*#__PURE__*/ bo(/* @__PURE__ */ B({
	__name: "MonthSelection",
	props: { entityKeys: { type: Array } },
	setup(e) {
		let t = e, n = jn(qa), r = /* @__PURE__ */ L(!1), i = `sax-months-${Hn()}`, a = $(() => n?.language.value ?? "en"), o = $(() => a.value === "de" ? {
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
		return (e, t) => (G(), K("div", {
			class: "month-selection",
			"aria-busy": p.value
		}, [
			J("div", Uo, [J("div", Wo, [J("p", Go, j(d.value), 1), J("p", Ko, j(f.value), 1)]), J("button", {
				type: "button",
				class: "month-selection__toggle",
				"aria-expanded": r.value,
				"aria-controls": i,
				onClick: t[0] ||= (e) => r.value = !r.value
			}, [X(j(r.value ? o.value.close : o.value.edit) + " ", 1), (G(), K("svg", {
				viewBox: "0 0 24 24",
				width: "18",
				height: "18",
				"aria-hidden": "true",
				class: A({ "month-selection__chevron--expanded": r.value })
			}, [...t[1] ||= [J("path", { d: "m6 9 6 6 6-6" }, null, -1)]], 2))], 8, qo)]),
			J("div", Jo, [
				r.value ? Z("", !0) : (G(), K(U, { key: 0 }, [(G(!0), K(U, null, V(m.value, (e) => (G(), K("p", {
					key: e,
					class: "month-selection__error",
					role: "alert"
				}, j(e), 1))), 128)), p.value ? (G(), K("p", Yo, j(o.value.pending), 1)) : Z("", !0)], 64)),
				R(n)?.connected.value ? Z("", !0) : (G(), K("p", Xo, j(o.value.disconnected), 1)),
				u.value.length ? (G(), K("p", Zo, j(o.value.unknown) + ": " + j(u.value.map((e) => e.name).join(", ")), 1)) : Z("", !0),
				h.value.length ? (G(), K("p", Qo, j(o.value.readOnly) + ": " + j(h.value.map((e) => e.name).join(", ")), 1)) : Z("", !0)
			]),
			On(J("div", {
				id: i,
				class: "month-selection__details"
			}, [J("p", $o, j(o.value.hint), 1), J("div", es, [(G(!0), K(U, null, V(c.value, (e) => (G(), K("fieldset", {
				key: e.index,
				class: "month-selection__quarter"
			}, [J("legend", null, j(e.name), 1), J("div", ts, [(G(!0), K(U, null, V(e.months, (e) => (G(), K(U, { key: e.index }, [e.entity && e.key ? (G(), q(xo, {
				key: 0,
				domain: "switch",
				"entity-key": e.key,
				"month-tile": ""
			}, null, 8, ["entity-key"])) : (G(), K("div", ns, [J("label", rs, [J("span", null, j(e.name), 1), J("input", {
				type: "checkbox",
				role: "switch",
				disabled: "",
				indeterminate: !0,
				"aria-describedby": `${i}-${e.index}-missing`
			}, null, 8, is)]), J("p", { id: `${i}-${e.index}-missing` }, j(o.value.unavailable), 9, as)]))], 64))), 128))])]))), 128))])], 512), [[Ki, r.value]])
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
}, xs = /*#__PURE__*/ bo(/* @__PURE__ */ B({
	__name: "TimeWindowControl",
	props: { kind: { type: String } },
	setup(e) {
		let t = e, n = jn(qa), r = $(() => n?.entity("time", `${t.kind}_start`)), i = $(() => n?.entity("time", `${t.kind}_end`)), a = `sax-window-${Hn()}`, o = $(() => n?.language.value ?? "en"), s = $(() => o.value === "de" ? {
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
		}), c = /* @__PURE__ */ L(""), l = /* @__PURE__ */ L(""), u = /* @__PURE__ */ L(!1), d = /* @__PURE__ */ L(), f = /* @__PURE__ */ L(!1), p = /* @__PURE__ */ L(!1), m = /* @__PURE__ */ L(!1), h = 0, g = null;
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
		let x = $(() => r.value?.state?.state ?? ""), S = $(() => i.value?.state?.state ?? ""), C = $(() => !!r.value?.available && !!i.value?.available && _(x.value) !== null && _(S.value) !== null), w = $(() => typeof r.value?.metadata.device_id == "string" && r.value.metadata.device_id.length > 0 && r.value.metadata.device_id === i.value?.metadata.device_id), ee = $(() => C.value ? `${y(x.value)} – ${y(S.value)}${s.value.unit ? ` ${s.value.unit}` : ""}` : [r.value, i.value].map((e) => e?.available && _(e.state?.state ?? "") !== null ? `${y(e.state.state)}${s.value.unit ? ` ${s.value.unit}` : ""}` : s.value.missingValue).join(" – ")), T = $(() => _(c.value) !== null && _(l.value) !== null), E = $(() => u.value && (_(c.value) !== _(x.value) || _(l.value) !== _(S.value))), D = $(() => f.value || !!r.value?.pending || !!i.value?.pending), O = $(() => !n?.ready.value || !n.connected.value || !C.value || !w.value || !r.value?.canControl || !i.value?.canControl || D.value), k = $(() => r.value?.error || i.value?.error), te = $(() => n?.connected.value ? C.value ? w.value ? !r.value?.canControl || !i.value?.canControl ? s.value.readOnly : D.value ? s.value.pending : p.value ? s.value.awaiting : m.value ? s.value.changed : T.value ? "" : s.value.invalid : s.value.incompatible : s.value.unavailable : s.value.disconnected), ne = $(() => u.value || !C.value ? c.value : x.value), re = $(() => u.value || !C.value ? l.value : S.value), ie = $(() => {
			let e = _(ne.value), t = _(re.value);
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
		}), ae = $(() => {
			let e = _(ne.value), t = _(re.value);
			return e === null || t === null || e === t ? [] : (t > e ? [[e, t]] : [[e, 86400], [0, t]]).filter(([e, t]) => e !== t).map(([e, t]) => ({
				left: `${e / 864}%`,
				width: `${(t - e) / 864}%`
			}));
		}), oe = $(() => [{
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
		function se() {
			let e = g;
			g = null, e?.target.hasPointerCapture?.(e.pointerId) && e.target.releasePointerCapture(e.pointerId);
		}
		Pn([
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
			h += 1, se(), f.value = !1, p.value = !1, u.value = !1, m.value = !!t?.length && i && !a && C.value, c.value = C.value ? b(x.value) : "", l.value = C.value ? b(S.value) : "";
		}, {
			immediate: !0,
			flush: "sync"
		}), Pn(O, (e) => {
			e && se();
		}, { flush: "sync" }), $n(se);
		function ce(e, t) {
			O.value || (e === "start" ? c.value = b(t) : l.value = b(t), u.value = !0, p.value = !1, m.value = !1);
		}
		function le(e, t) {
			let n = t.target;
			ce(e, n.value), n.value = e === "start" ? c.value : l.value;
		}
		function de(e, t) {
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
			(t.key in r || t.key === "Home" || t.key === "End") && (t.preventDefault(), ce(e, v(t.key === "Home" ? 0 : t.key === "End" ? 86340 : Math.max(0, Math.min(86340, Math.floor(n / 60) * 60 + r[t.key])))));
		}
		function fe(e) {
			if (!g || g.pointerId !== e.pointerId || O.value || !d.value) return;
			let t = d.value.getBoundingClientRect();
			if (t.width <= 0 || !g.moved && e.clientX === g.originX) return;
			let n = Math.max(0, Math.min(1439, Math.round(g.originSeconds / 60 + (e.clientX - g.originX) / t.width * 1440)));
			g.moved = !0, ce(g.boundary, v(n * 60));
		}
		function pe(e, t) {
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
		function me(e) {
			g?.pointerId === e.pointerId && (g.moved && fe(e), se());
		}
		async function he() {
			if (!n || O.value || !T.value || !E.value) return;
			let e = h;
			f.value = !0, m.value = !1;
			let r = await n.performTimeWindow(t.kind, `${c.value}:00`, `${l.value}:00`);
			e === h && (f.value = !1, p.value = r && E.value);
		}
		return (e, t) => r.value || i.value ? (G(), K("form", {
			key: 0,
			class: "time-window-control",
			"aria-busy": D.value,
			onSubmit: Fa(he, ["prevent"])
		}, [
			J("div", cs, [(G(!0), K(U, null, V(oe.value, (e) => (G(), K("label", {
				key: e.key,
				for: `${a}-${e.key}`,
				class: "time-window-control__field"
			}, [J("span", null, [X(j(e.name), 1), s.value.unit ? (G(), K(U, { key: 0 }, [X(" (" + j(s.value.unit) + ")", 1)], 64)) : Z("", !0)]), J("input", {
				id: `${a}-${e.key}`,
				type: "time",
				step: "60",
				required: "",
				value: e.value,
				disabled: O.value,
				"aria-describedby": `${a}-confirmed ${a}-status`,
				onInput: (t) => le(e.key, t)
			}, null, 40, us)], 8, ls))), 128)), J("button", {
				class: "time-window-control__apply",
				type: "submit",
				disabled: O.value || !T.value || !E.value
			}, j(s.value.apply), 9, ds)]),
			J("p", {
				id: `${a}-confirmed`,
				class: "time-window-control__confirmed"
			}, j(s.value.confirmed) + ": " + j(ee.value), 9, fs),
			J("div", {
				class: "time-window-control__timeline",
				"aria-label": s.value.timeline,
				role: "group"
			}, [J("div", {
				ref_key: "rail",
				ref: d,
				class: A(["time-window-control__rail", { "time-window-control__rail--draft": E.value }])
			}, [(G(!0), K(U, null, V(ae.value, (e, t) => (G(), K("span", {
				key: t,
				class: "time-window-control__segment",
				style: ue(e)
			}, null, 4))), 128))], 2), (G(!0), K(U, null, V(oe.value, (e) => (G(), K("button", {
				key: e.key,
				type: "button",
				role: "slider",
				class: A(["time-window-control__handle", `time-window-control__handle--${e.key}`]),
				style: ue({ left: `${(_(e.value) ?? 0) / 864}%` }),
				disabled: O.value || !T.value,
				"aria-label": e.marker,
				"aria-valuemin": "0",
				"aria-valuemax": "86340",
				"aria-valuenow": _(e.value) ?? 0,
				"aria-valuetext": `${y(e.value)}${s.value.unit ? ` ${s.value.unit}` : ""}`,
				"aria-describedby": `${a}-help ${a}-confirmed`,
				"aria-orientation": "horizontal",
				onKeydown: (t) => de(e.key, t),
				onPointerdown: (t) => pe(e.key, t),
				onPointermove: fe,
				onPointerup: me,
				onPointercancel: se,
				onLostpointercapture: se
			}, [J("span", hs, j(e.shortName), 1), t[0] ||= J("span", {
				class: "time-window-control__marker-dot",
				"aria-hidden": "true"
			}, null, -1)], 46, ms))), 128))], 8, ps),
			t[1] ||= J("div", {
				class: "time-window-control__ticks",
				"aria-hidden": "true"
			}, [
				J("span", null, "00"),
				J("span", null, "06"),
				J("span", null, "12"),
				J("span", null, "18"),
				J("span", null, "24")
			], -1),
			J("p", gs, [J("span", null, j(E.value ? s.value.draft : s.value.duration) + ":", 1), X(" " + j(ie.value), 1)]),
			J("p", {
				id: `${a}-help`,
				class: "time-window-control__sr-only"
			}, j(s.value.help), 9, _s),
			J("div", {
				id: `${a}-status`,
				class: "time-window-control__feedback"
			}, [k.value ? (G(), K("p", ys, j(k.value), 1)) : te.value ? (G(), K("p", bs, j(te.value), 1)) : Z("", !0)], 8, vs)
		], 40, ss)) : Z("", !0);
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
}, Es = ["aria-labelledby"], Ds = ["id"], Os = /*#__PURE__*/ bo(/* @__PURE__ */ B({
	__name: "ChargingLayout",
	props: {
		switchKey: { type: String },
		hideConfirmedLabel: { type: Boolean },
		cards: { type: Array }
	},
	setup(e) {
		let t = e, n = jn(qa), r = Hn(), i = $(() => n?.language.value ?? "en"), a = $(() => t.cards.map((e) => {
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
		return (t, l) => (G(), K("div", Ss, [
			!R(n)?.ready.value && !R(n)?.error.value ? (G(), K("p", Cs, j(c.value.loading), 1)) : R(n)?.ready.value && !s.value && !a.value.length ? (G(), K("p", ws, j(c.value.empty), 1)) : Z("", !0),
			s.value ? (G(), q(xo, {
				key: 2,
				domain: "switch",
				"entity-key": e.switchKey,
				"hide-confirmed-label": e.hideConfirmedLabel
			}, null, 8, ["entity-key", "hide-confirmed-label"])) : Z("", !0),
			o.value.length ? (G(), K("div", Ts, [(G(!0), K(U, null, V(o.value, (t) => (G(), K("div", {
				key: t.key,
				class: A(["charging-view__group", { "charging-view__group--wide": t.wide }])
			}, [(G(!0), K(U, null, V(t.cards, (t) => (G(), K("section", {
				key: t.key,
				class: "charging-view__card",
				"aria-labelledby": `${R(r)}-${t.key}`
			}, [
				J("h2", { id: `${R(r)}-${t.key}` }, j(t.title[i.value]), 9, Ds),
				t.showTimeWindow && t.timeWindow ? (G(), q(xs, {
					key: 0,
					kind: t.timeWindow
				}, null, 8, ["kind"])) : Z("", !0),
				t.entities.length ? (G(), K("div", {
					key: 1,
					class: A(["charging-view__rows", {
						"charging-view__rows--columns": t.layout === "columns",
						"charging-view__rows--months": t.layout === "months"
					}])
				}, [t.layout === "months" ? (G(), q(os, {
					key: 0,
					"entity-keys": t.entities.map(([, e]) => e)
				}, null, 8, ["entity-keys"])) : (G(!0), K(U, { key: 1 }, V(t.entities, ([t, n]) => (G(), K(U, { key: `${t}.${n}` }, [t === "switch" || t === "number" || t === "time" || t === "select" ? (G(), q(xo, {
					key: 0,
					domain: t,
					"entity-key": n,
					"hide-confirmed-label": e.hideConfirmedLabel
				}, null, 8, [
					"domain",
					"entity-key",
					"hide-confirmed-label"
				])) : (G(), q(No, {
					key: 1,
					domain: t,
					"entity-key": n
				}, null, 8, ["domain", "entity-key"]))], 64))), 128))], 2)) : Z("", !0)
			], 8, Es))), 128))], 2))), 128))])) : Z("", !0)
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
	let r = /* @__PURE__ */ Gt(null), i = /* @__PURE__ */ L(!1), a = /* @__PURE__ */ L(null), o, s = 0, c = !1;
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
	return Pn([
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
	}, { immediate: !0 }), Ee(() => {
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
var Is = ["aria-labelledby"], Ls = ["id"], Rs = { class: "tariff-plan__scroll" }, zs = { class: "tariff-plan__table" }, Bs = ["aria-label"], Vs = { colspan: "2" }, Hs = { key: 0 }, Us = { key: 0 }, Ws = { key: 1 }, Gs = /*#__PURE__*/ bo(/* @__PURE__ */ B({
	__name: "TariffPlan",
	props: { hass: { type: Object } },
	setup(e) {
		let t = e, n = jn(qa), r = Hn(), i = $(() => n?.language.value === "de" ? {
			tariff: "Tarifpreisfenster",
			from: "Von",
			to: "Bis",
			price: "Arbeitspreis",
			status: "Status",
			now: "jetzt",
			base: "Grundpreis",
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
			feed: "Feed-in remuneration",
			next: "Next price change",
			unavailable: "Unavailable",
			noPrice: "No price currently applies. Please check the tariff configuration."
		}), a = $(() => n?.entity("sensor", "economics_current_import_price")), o = (e) => {
			let n = js(e, t.hass, 4);
			return n === null ? i.value.unavailable : `${n} EUR/kWh`;
		}, s = (e) => Ms(e, t.hass) ?? i.value.unavailable, c = $(() => a.value?.state?.attributes ?? {}), l = $(() => c.value.tariff_type === "time_of_use"), u = $(() => Array.isArray(c.value.windows) ? c.value.windows.filter((e) => !!e && typeof e == "object" && typeof e.start == "string" && typeof e.end == "string") : []), d = $(() => c.value.unavailable_reason), f = $(() => a.value?.available && ks(a.value.state?.state) !== null && d.value == null), p = $(() => {
			let e = c.value.active_window;
			return e && typeof e == "object" ? e : null;
		}), m = (e) => f.value && ks(e.price_eur_kwh) !== null && p.value?.start === e.start && p.value?.end === e.end, h = $(() => f.value && p.value === null && ks(c.value.base_price_eur_kwh) !== null), g = (e) => Ms(`2000-01-01T${e.length === 5 ? `${e}:00` : e}Z`, t.hass, {
			timeStyle: "short",
			timeZone: "UTC"
		}) ?? e.slice(0, 5);
		return (e, t) => l.value ? (G(), K("section", {
			key: 0,
			class: "tariff-plan",
			"aria-labelledby": `${R(r)}-tariff`
		}, [
			J("h2", { id: `${R(r)}-tariff` }, j(i.value.tariff), 9, Ls),
			J("div", Rs, [J("table", zs, [J("thead", null, [J("tr", null, [
				J("th", { "aria-label": i.value.status }, null, 8, Bs),
				J("th", null, j(i.value.from), 1),
				J("th", null, j(i.value.to), 1),
				J("th", null, j(i.value.price), 1)
			])]), J("tbody", null, [(G(!0), K(U, null, V(u.value, (e, t) => (G(), K("tr", {
				key: t,
				class: A({ "tariff-plan__current": m(e) })
			}, [
				J("td", null, j(m(e) ? i.value.now : ""), 1),
				J("td", null, j(g(e.start)), 1),
				J("td", null, j(g(e.end)), 1),
				J("td", null, j(o(e.price_eur_kwh)), 1)
			], 2))), 128)), J("tr", { class: A({ "tariff-plan__current": h.value }) }, [
				J("td", null, j(h.value ? i.value.now : ""), 1),
				J("td", Vs, j(i.value.base), 1),
				J("td", null, j(o(c.value.base_price_eur_kwh)), 1)
			], 2)])])]),
			J("p", null, [J("strong", null, j(i.value.feed) + ":", 1), X(" " + j(o(c.value.feed_in_price_eur_kwh)), 1)]),
			f.value ? c.value.next_price_change_at ? (G(), K("p", Ws, [J("strong", null, j(i.value.next) + ":", 1), X(" " + j(s(c.value.next_price_change_at)), 1)])) : Z("", !0) : (G(), K("p", Hs, [X(j(i.value.noPrice), 1), typeof d.value == "string" && d.value ? (G(), K("span", Us, " (" + j(d.value) + ")", 1)) : Z("", !0)]))
		], 8, Is)) : Z("", !0);
	}
}), [["styles", [".tariff-plan{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.tariff-plan h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.tariff-plan p{overflow-wrap:anywhere;line-height:1.6}.tariff-plan p:last-child{margin-bottom:0}.tariff-plan__scroll{overflow-x:auto}.tariff-plan__table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%;line-height:1.5}.tariff-plan__table th,.tariff-plan__table td{text-align:left;white-space:nowrap;border-bottom:1px solid var(--divider-color,#e0e0e0);padding:10px 8px}.tariff-plan__table th:last-child,.tariff-plan__table td:last-child{text-align:right}.tariff-plan__current{background:var(--secondary-background-color,color-mix(in srgb, currentColor 8%, transparent));font-weight:600}@media (max-width:600px){.tariff-plan{padding:20px}}@container sax-content (width>=860px){.tariff-plan{padding:18px}.tariff-plan h2{margin-bottom:12px;font-size:16px}.tariff-plan p{margin-top:10px;line-height:1.5}.tariff-plan__table th,.tariff-plan__table td{padding:7px 8px}}"]]]), Ks = {
	soc_stale: ["Der Ladezustand ist für eine sichere Ladefreigabe zu alt.", "State of charge is too old to permit charging safely."],
	below_start_threshold: ["Der berechnete Ladebedarf liegt unter der Startschwelle für eine neue Netzladung.", "Calculated charging demand is below the threshold for starting a new grid charge."],
	price_limit_missing: ["Für die bedarfsgesteuerte Strategie fehlt eine gültige Preisgrenze.", "Demand-based charging requires a valid price limit."],
	no_price_data: ["Für die benötigten Tarifzeiten fehlen Preisdaten.", "Price data is missing for the required tariff periods."],
	invalid_planning_time: ["Der Prüfzeitpunkt ist ungültig.", "The evaluation time is invalid."],
	invalid_device_data: ["Für den sicheren Ladevollzug fehlen gültige Gerätedaten.", "Valid device data required for safe charging is missing."],
	discharge_power_unavailable: ["Die verfügbare Entladeleistung fehlt.", "Available discharging power is unknown."],
	night_geometry_unavailable: ["Der Nachtzeitraum ist nicht zuverlässig bestimmt.", "The night period is not known reliably."],
	unsupported_load_basis: ["Die Quelle liefert keine nächtliche SAX-Entladeenergie.", "The source does not provide night-time SAX discharge energy."],
	invalid_forecast_intervals: ["Die Prognoseintervalle sind ungültig.", "Forecast intervals are invalid."],
	invalid_tariff_constraints: ["Die Tarifzeiten oder Ladegrenzen sind ungültig.", "Tariff periods or charging limits are invalid."],
	no_charge_window: ["Im zulässigen Zeitraum ist kein Ladefenster freigegeben.", "No charging window is permitted in the available period."],
	planning_solver_failed: ["Es konnte kein verlässlicher Ladeplan berechnet werden.", "A reliable charging plan could not be calculated."],
	history_invalid: ["Die aufgezeichnete Entladehistorie enthält ungültige Daten.", "Recorded discharge history contains invalid data."],
	max_soc: ["Die maximale SOC-Grenze verhindert derzeit Netzladen.", "The maximum SOC limit currently prevents grid charging."],
	grid_serving: ["Die netzdienliche Steuerung hat derzeit Vorrang.", "Grid-serving control currently takes priority."],
	pv_invalid_intervals: ["Die Grenzen der PV-Prognoseintervalle sind ungültig.", "Solar forecast interval boundaries are invalid."],
	pv_overlapping_intervals: ["Überlappende PV-Angaben wurden als Datenlücken behandelt.", "Overlapping solar intervals were treated as missing data."],
	pv_partial_coverage: ["Die PV-Abdeckung ist teilweise. Maßgeblich ist die vollständige Abdeckung bis zur PV-Versorgung und ihrem 60-Minuten-Nachweis.", "Solar coverage is partial. Complete coverage up to solar supply and its 60-minute confirmation is what matters."],
	pv_invalid_interval_value: ["Ungültige PV-Energie- oder Leistungsangaben wurden ausgelassen.", "Invalid solar energy or power values were omitted."],
	pv_input_fallbacks: ["PV-Intervalle mit Ersatzwerten wurden ausgelassen.", "Solar intervals using fallback input values were omitted."],
	pv_incomplete_forecast: ["Unvollständige PV-Intervalle wurden ausgelassen.", "Incomplete solar intervals were omitted."],
	pv_no_valid_intervals: ["Die PV-Prognose enthält keine nutzbaren Intervalle.", "The solar forecast contains no usable intervals."],
	pv_unsupported_schema: ["Die PV-Quelle liefert ein nicht unterstütztes Antwortformat.", "The solar source returned an unsupported response format."],
	pv_invalid_scope: ["Die PV-Prognose beschreibt nicht die vollständige Anlage.", "The solar forecast does not describe the whole installation."],
	pv_invalid_metadata: ["Zeitzone oder Abdeckungsangaben der PV-Prognose sind ungültig.", "The solar forecast time zone or coverage metadata is invalid."],
	pv_missing_update_status: ["Die PV-Quelle bestätigt keinen erfolgreichen Abruf.", "The solar source does not confirm a successful update."],
	pv_invalid_response: ["Die PV-Quelle hat keine gültige Prognose geliefert.", "The solar source did not return a valid forecast."],
	pv_invalid_fetched_at: ["Der PV-Abrufzeitpunkt ist ungültig.", "The solar retrieval timestamp is invalid."],
	pv_future_fetched_at: ["Der PV-Abrufzeitpunkt liegt in der Zukunft.", "The solar retrieval timestamp is in the future."],
	pv_adapter_closed: ["Die PV-Quelle wurde entladen.", "The solar source was unloaded."],
	pv_query_in_progress: ["Eine PV-Abfrage läuft bereits.", "A solar query is already running."],
	night_slot_mean: ["Direkt beobachteter Uhrzeitslot", "Directly observed time slot"],
	pooled_night_estimate: ["Gepooltes Nachtlastniveau", "Pooled night load level"],
	dawn_extrapolation: ["Begrenzte Dämmerungsfortschreibung", "Limited dawn estimate"],
	pooled_dawn_estimate: ["Dämmerungsschätzung aus dem gepoolten Nachtlastniveau", "Dawn estimate based on the pooled night load level"],
	battery_covers_bridge: ["Die nutzbare Speicherenergie deckt den Bedarf bis zur erwarteten PV-Versorgung.", "Usable battery energy covers demand until the expected solar supply."],
	night_bridge_required: ["Die Nachtbrücke benötigt zusätzliche Netzenergie innerhalb der freigegebenen Tarifzeiten.", "The night bridge needs additional grid energy within permitted tariff periods."],
	waiting_for_pv_in_cheap_window: ["Kein Netzladen geplant: PV versorgt den Bedarf noch innerhalb des günstigen Zeitfensters.", "No grid charging planned: solar supply will cover demand within the cheap window."],
	pv_supplies_load: ["Die PV-Prognose deckt den verbleibenden Bedarf.", "The solar forecast covers remaining demand."],
	unmet_need: ["Der Bedarf kann unter den geltenden Zeit-, Leistungs- und SOC-Grenzen nicht vollständig gedeckt werden.", "Demand cannot be fully covered within the available time, power and SOC limits."],
	outside_model_scope: ["Außerhalb des Nachtmodells: Die Planung umfasst die Nacht und höchstens vier Stunden nach Sonnenaufgang.", "Outside the night model: planning covers the night and at most four hours after sunrise."],
	pv_supply_unconfirmed: ["Innerhalb der Dämmerungsgrenze ist keine durchgehend ausreichende PV-Versorgung für 60 Minuten nachgewiesen.", "Continuous sufficient solar supply for 60 minutes is not confirmed within the dawn limit."],
	invalid_soc_limits: ["Die SOC-Grenzen passen nicht zusammen. Reserve und maximale Ladegrenze prüfen.", "The SOC limits conflict. Check the reserve and maximum charging limit."],
	soc_unavailable: ["Der Ladezustand fehlt oder ist veraltet.", "Battery state of charge is missing or stale."],
	capacity_unavailable: ["Die nutzbare Speicherkapazität fehlt.", "Usable battery capacity is unavailable."],
	charge_power_unavailable: ["Die verfügbare Ladeleistung fehlt.", "Available charging power is unknown."],
	device_unavailable: ["Der Speicher ist nicht verfügbar.", "The battery is unavailable."],
	invalid_efficiency: ["Die Wirkungsgradannahmen sind ungültig.", "The efficiency assumptions are invalid."],
	pv_provider_not_configured: ["Für die Nachtregelung ist noch keine PV-Quelle eingerichtet.", "No solar source is configured for night control."],
	pv_source_unavailable: ["Die ausgewählte PV-Anlage ist nicht verfügbar oder nicht eindeutig zugeordnet.", "The selected solar installation is unavailable or cannot be identified uniquely."],
	pv_missing_fetched_at: ["Der tatsächliche Abrufzeitpunkt der PV-Prognose fehlt.", "The actual solar forecast retrieval timestamp is missing."],
	pv_stale_forecast: ["Die PV-Prognose überschreitet ihr zulässiges Datenalter.", "The solar forecast exceeds its permitted age."],
	pv_stale: ["Die PV-Prognose ist veraltet.", "The solar forecast is stale."],
	pv_update_failed: ["Der letzte gemeldete PV-Abruf ist fehlgeschlagen.", "The last reported solar update failed."],
	pv_source_changed: ["Die PV-Quelle wurde während der Prüfung geändert. Eine neue Prüfung ist erforderlich.", "The solar source changed during evaluation. A new evaluation is required."],
	pv_query_timeout: ["Die PV-Abfrage hat nicht rechtzeitig geantwortet.", "The solar query timed out."],
	pv_query_failed: ["Die PV-Quelle konnte nicht gelesen werden.", "The solar source could not be read."],
	pv_coverage_missing: ["Im entscheidungsrelevanten Zeitraum fehlen PV-Intervalle.", "Solar intervals are missing in the period required for this decision."],
	load_coverage_missing: ["Im entscheidungsrelevanten Zeitraum fehlt eine belastbare Nachtlastschätzung.", "The required period has no usable night load estimate."],
	history_unavailable: ["Die SAX-Entladehistorie ist noch nicht verfügbar.", "SAX discharge history is not yet available."],
	history_stale: ["Die Entladehistorie ist veraltet.", "Discharge history is stale."],
	insufficient_history: ["Es fehlen verwertbare Beobachtungen aus mindestens drei Nächten mit zusammen sechs Stunden.", "Usable observations from at least three nights with six hours in total are required."],
	unsupported_night_geometry: ["Sonnenaufgang und Sonnenuntergang konnten nicht zuverlässig bestimmt werden.", "Sunrise and sunset could not be determined reliably."],
	awaiting_evaluation: ["Die nächste Prüfung wird vorbereitet.", "The next evaluation is being prepared."],
	evaluating: ["Die Prüfung läuft.", "Evaluation is running."],
	evaluation_failed: ["Die Prüfung konnte nicht abgeschlossen werden.", "Evaluation could not be completed."],
	calibration: ["Mehrladung für Zellkalibrierung bis 100 %. Der reguläre Bedarf bleibt separat sichtbar.", "Additional charging to 100% for cell calibration. Regular demand remains visible separately."],
	manual_override: ["Manuelle Steuerung verhindert derzeit die Ausführung des Plans.", "Manual control currently prevents the plan from running."],
	pv_surplus: ["PV-Überschuss verhindert derzeit die geplante Netzladung.", "Solar surplus currently prevents planned grid charging."],
	price_limit: ["Die Preisgrenze erlaubt derzeit keine Netzladung.", "The price limit currently prevents grid charging."],
	outside_window: ["Das freigegebene Ladezeitfenster ist derzeit geschlossen.", "The permitted charging window is currently closed."],
	inactive: ["Die bedarfsgesteuerte Regelung ist für diesen Tarif deaktiviert.", "Demand-based control is disabled for this tariff."],
	observed_slot: ["Direkt beobachteter Uhrzeitslot", "Directly observed time slot"],
	pooled_night: ["Gepooltes Nachtlastniveau", "Pooled night load level"],
	dawn_extension: ["Begrenzte Dämmerungsfortschreibung", "Limited dawn estimate"]
};
function qs(e, t) {
	return typeof e != "string" || !e ? t === "de" ? "Unbekannt" : "Unknown" : !Ks[e] && e.startsWith("pv_source_") ? t === "de" ? `Qualitätshinweis der PV-Quelle: ${e.slice(10)}` : `Solar source quality flag: ${e.slice(10)}` : Ks[e]?.[t === "de" ? 0 : 1] ?? (t === "de" ? `Weitere Einschränkung: ${e}` : `Additional constraint: ${e}`);
}
function Js(e, t, n = "") {
	return typeof e != "number" || !Number.isFinite(e) ? t === "de" ? "Unbekannt" : "Unknown" : `${new Intl.NumberFormat(t === "de" ? "de-DE" : "en-GB", { maximumFractionDigits: 2 }).format(e)}${n ? ` ${n}` : ""}`;
}
function Ys(e, t, n) {
	if (typeof e != "string" || !/(Z|[+-]\d{2}:\d{2})$/.test(e)) return t === "de" ? "Unbekannt" : "Unknown";
	let r = new Date(e);
	if (!Number.isFinite(r.getTime())) return t === "de" ? "Unbekannt" : "Unknown";
	try {
		return new Intl.DateTimeFormat(n?.locale?.language ?? (t === "de" ? "de-DE" : "en-GB"), {
			dateStyle: "medium",
			timeStyle: "short",
			timeZone: n?.config?.time_zone,
			hour12: n?.locale?.time_format === "am_pm"
		}).format(r);
	} catch {
		return t === "de" ? "Unbekannt" : "Unknown";
	}
}
//#endregion
//#region src/components/HemsCard.vue?vue&type=script&setup=true&lang.ts
var Xs = ["aria-labelledby"], Zs = ["id"], Qs = { class: "hems-card__badge" }, $s = {
	class: "hems-card__explanation",
	role: "status",
	"aria-live": "polite"
}, ec = { key: 0 }, tc = { key: 0 }, nc = { key: 1 }, rc = { key: 2 }, ic = { key: 2 }, ac = {
	key: 0,
	class: "hems-card__metrics"
}, oc = { class: "hems-card__next" }, sc = { "data-testid": "hems-next" }, cc = { key: 1 }, lc = { class: "hems-card__data" }, uc = /*#__PURE__*/ bo(/* @__PURE__ */ B({
	__name: "HemsCard",
	props: {
		tariff: { type: String },
		hass: { type: Object }
	},
	setup(e) {
		let t = e, n = jn(qa), r = Hn(), i = $(() => n?.language.value ?? "en"), a = $(() => n?.entity("sensor", "hems_status")), o = $(() => a.value?.available ? a.value.state?.attributes ?? {} : {}), s = $(() => o.value.mode === t.tariff), c = $(() => a.value?.available ? s.value ? String(o.value.status ?? "unknown") : "inactive" : "unavailable"), l = $(() => s.value && (o.value.fallback === !0 || c.value === "fallback")), u = {
			title: ["Bedarfsgesteuerte Nachtregelung", "Demand-based night control"],
			unknown: ["Unbekannt", "Unknown"],
			unavailable: ["Nicht verfügbar", "Unavailable"],
			inactive: ["Deaktiviert", "Disabled"],
			dynamicInactive: ["Die Strategie Bedarfsgesteuert / Nachtbrücke ist im Feld Strategie auswählbar.", "Select Demand-based / Night bridge in the Strategy field."],
			planned: ["Netzladung geplant", "Grid charging planned"],
			no_need: ["Kein Netzladen geplant", "No grid charging planned"],
			limited: ["Bedarf nur teilweise gedeckt", "Demand only partly covered"],
			blocked: ["Plan gesperrt", "Plan blocked"],
			fallback: ["Rückfall auf Min-/Max-SOC", "Fallback to min/max SOC"],
			evaluating: ["Prüfung läuft", "Evaluating"],
			awaiting_evaluation: ["Prüfung wird vorbereitet", "Preparing evaluation"],
			execution: ["Ausführung", "Execution"],
			confirmed: ["Netzladebefehl vom Gerät bestätigt", "Grid charge command acknowledged by device"],
			waiting: ["Derzeit keine bestätigte Netzladung", "No acknowledged grid charging at present"],
			target: ["Berechnetes Ladeziel", "Calculated SOC target"],
			remaining: ["Verbleibende Netzladeenergie", "Remaining grid charging energy"],
			start: ["Geplanter Beginn", "Planned start"],
			end: ["Geplantes Ende", "Planned end"],
			next: ["Nächste Prüfung", "Next evaluation"],
			details: ["Datenbasis und Erklärung", "Data and explanation"],
			evaluated: ["Letzte Prüfung", "Last evaluation"],
			supply: ["Erwartete PV-Versorgung", "Expected solar supply"],
			load: ["Erwarteter Bedarf", "Expected demand"],
			pvUsed: ["Zeitlich genutzte PV-Energie", "Solar energy used at the right time"],
			available: ["Nutzbare Speicherenergie", "Usable battery energy"],
			reserve: ["Planungsreserve", "Planning reserve"],
			unmet: ["Ungedeckter Bedarf", "Unmet demand"],
			history: ["Nachtbeobachtung", "Night observations"],
			nights: ["Nächte", "nights"],
			hours: ["Stunden beobachtet", "hours observed"],
			coverage: ["Beobachtete Abdeckung", "Observed coverage"],
			model: ["Modellzeitraum", "Model period"],
			provider: ["PV-Anbieter / Anlage", "Solar provider / installation"],
			fetched: ["PV-Daten abgerufen", "Solar data retrieved"],
			pvCoverage: ["PV-Abdeckung", "Solar coverage"],
			full: ["angefragter Zeitraum vollständig", "requested period complete"],
			partial: ["teilweise; benötigt wird die vollständige Nachtbrücke einschließlich 60 Minuten PV-Nachweis", "partial; the full night bridge including 60 minutes of solar confirmation is required"],
			maxAge: ["Zulässiges PV-Datenalter", "Maximum solar data age"],
			success: ["Letzter PV-Abruf erfolgreich", "Last solar update successful"],
			yes: ["Ja", "Yes"],
			no: ["Nein", "No"],
			unknownSuccess: ["Unbekannt; keine Erfolgszusage des Anbieters", "Unknown; provider does not guarantee update success"],
			efficiencies: ["Annahmen: Lade- / Entladewirkungsgrad", "Assumptions: charge / discharge efficiency"],
			policy: ["SAX-Annahme zum Prognosealter", "SAX assumption for forecast age"],
			modelInfo: ["Nachtmodell aus SAX-Entladeenergie der letzten sieben Tage. Eine vollständige Tagesoptimierung ist nicht enthalten.", "Night model based on SAX discharge energy over the last seven days. Full-day optimisation is not included."],
			reserveInfo: ["Min-SOC ist die Reserve der Planung; er ist keine neue Gerätesperre gegen Entladung. Max-SOC begrenzt das Ladeziel. Im Rückfall gelten dieselben gespeicherten Werte nach den klassischen Regeln.", "Min SOC is the planning reserve; it is not a new physical discharge lock. Max SOC limits the target. Fallback applies the same saved values using the classic rules."],
			classicInfo: ["Min-SOC bleibt die Startschwelle; Max-SOC das Ladeziel der klassischen Regelung.", "Min SOC remains the start threshold; max SOC is the target of classic control."],
			setup: ["PV-Anbieter und Anlage sowie Wirkungsgradannahmen lassen sich unter Einstellungen → Geräte & Dienste → SAX Power → Konfigurieren auswählen.", "Select the solar provider, installation and efficiency assumptions in Settings → Devices & services → SAX Power → Configure."],
			fallbackInfo: ["Die gespeicherte Min-/Max-SOC-Regel gilt. Tarifgrenzen und Geräteschutz bleiben wirksam.", "The saved min/max SOC rule applies. Tariff limits and device protection remain in force."],
			calibrationExtra: ["Zusätzliche Netzenergie für Kalibrierung", "Additional grid energy for calibration"],
			executionRemaining: ["Verbleibende Energie der aktuellen Ladefreigabe", "Remaining energy of the current charging permission"],
			executionDeadline: ["Ende der aktuellen Ladefreigabe", "Current charging permission ends"],
			calibrationTarget: ["Ladeziel für Zellkalibrierung", "Cell calibration target"],
			disconnected: ["Die Verbindung fehlt. Plan und nächster Prüftermin sind nicht verfügbar.", "Connection unavailable. The plan and next evaluation time are unavailable."],
			methods: ["Verwendete Schätzverfahren", "Estimation methods used"],
			quality: ["Datenqualität", "Data quality"]
		}, d = (e) => u[e]?.[i.value === "de" ? 0 : 1] ?? u.unknown[i.value === "de" ? 0 : 1], f = $(() => d(l.value ? "fallback" : c.value)), p = $(() => s.value && Array.isArray(o.value.reason_codes) ? o.value.reason_codes.filter((e) => typeof e == "string").slice(0, 10) : []), m = $(() => [
			o.value.load_quality,
			o.value.pv_quality,
			...Array.isArray(o.value.pv_quality_flags) ? o.value.pv_quality_flags : []
		].filter((e) => typeof e == "string" && !!e)), h = $(() => Array.isArray(o.value.load_quality_flags) ? o.value.load_quality_flags.filter((e) => typeof e == "string").slice(0, 8) : []), g = (e, t = "") => Js(e, i.value, t), _ = (e) => Ys(e, i.value, t.hass), v = $(() => s.value && c.value !== "evaluating" ? _(o.value.next_evaluation_at) : d("unknown")), y = $(() => d(o.value.execution_charging === !0 ? "confirmed" : o.value.execution_charging === !1 ? "waiting" : "unknown")), b = $(() => [
			["remaining", g(o.value.remaining_grid_kwh, "kWh")],
			["target", g(o.value.target_soc, "%")],
			["start", _(o.value.planned_start)],
			["end", _(o.value.planned_end)]
		]), x = $(() => [
			["executionRemaining", g(o.value.execution_remaining_kwh, "kWh")],
			["executionDeadline", _(o.value.execution_deadline)],
			["evaluated", _(o.value.evaluated_at)],
			["supply", _(o.value.pv_supply_at)],
			["load", g(o.value.expected_load_kwh, "kWh")],
			["pvUsed", g(o.value.pv_used_kwh, "kWh")],
			["available", g(o.value.available_battery_kwh, "kWh")],
			["reserve", `${g(o.value.reserve_soc, "%")} / ${g(o.value.reserve_kwh, "kWh")}`],
			["unmet", g(o.value.unmet_grid_kwh, "kWh")],
			["history", `${g(o.value.nights_count)} ${d("nights")} · ${g(o.value.observed_hours)} ${d("hours")}`],
			["coverage", typeof o.value.load_coverage == "number" ? g(o.value.load_coverage * 100, "%") : d("unknown")],
			["model", `${_(o.value.load_model_start)} – ${_(o.value.load_model_end)}`],
			["methods", h.value.length ? h.value.map((e) => qs(e, i.value)).join(" · ") : d("unknown")],
			["provider", `${o.value.pv_provider || d("unknown")} / ${o.value.pv_source_id || d("unknown")}`],
			["fetched", _(o.value.pv_fetched_at)],
			["pvCoverage", `${_(o.value.pv_coverage_start)} – ${_(o.value.pv_coverage_end)} · ${d(o.value.pv_coverage_complete === !0 ? "full" : o.value.pv_coverage_complete === !1 ? "partial" : "unknown")}`],
			["maxAge", `${typeof o.value.pv_max_age_seconds == "number" ? g(o.value.pv_max_age_seconds / 3600, "h") : d("unknown")}${o.value.pv_freshness_policy === "sax_max_age_assumption" ? ` · ${d("policy")}` : ""}`],
			["success", d(o.value.pv_update_success === !0 ? "yes" : o.value.pv_update_success === !1 ? "no" : "unknownSuccess")],
			["efficiencies", `${g(o.value.eta_charge_assumption)} / ${g(o.value.eta_discharge_assumption)}`]
		]);
		return (t, n) => a.value ? (G(), K("section", {
			key: 0,
			class: A(["hems-card", { "hems-card--fallback": l.value }]),
			"aria-labelledby": `${R(r)}-title`
		}, [
			J("header", null, [J("h2", { id: `${R(r)}-title` }, j(d("title")), 9, Zs), J("span", Qs, j(f.value), 1)]),
			J("div", $s, [a.value.available ? s.value ? (G(), K(U, { key: 1 }, [
				l.value ? (G(), K("p", tc, j(d("fallbackInfo")), 1)) : Z("", !0),
				(G(!0), K(U, null, V(p.value, (e) => (G(), K("p", { key: e }, j(R(qs)(e, i.value)), 1))), 128)),
				typeof o.value.execution_constraint == "string" ? (G(), K("p", nc, j(R(qs)(o.value.execution_constraint, i.value)), 1)) : Z("", !0),
				J("p", null, [
					J("strong", null, j(d("execution")) + ":", 1),
					X(" " + j(y.value), 1),
					typeof o.value.execution_reason == "string" && !p.value.includes(o.value.execution_reason) ? (G(), K(U, { key: 0 }, [X(". " + j(R(qs)(o.value.execution_reason, i.value)), 1)], 64)) : Z("", !0)
				]),
				o.value.calibration === !0 ? (G(), K("p", rc, j(R(qs)("calibration", i.value)) + " " + j(d("calibrationTarget")) + ": " + j(g(o.value.execution_target_soc, "%")) + " · " + j(d("calibrationExtra")) + ": " + j(g(o.value.calibration_extra_kwh, "kWh")), 1)) : Z("", !0)
			], 64)) : (G(), K("p", ic, j(d(e.tariff === "timed" ? "classicInfo" : "dynamicInactive")), 1)) : (G(), K("p", ec, j(d("disconnected")), 1))]),
			s.value ? (G(), K("dl", ac, [(G(!0), K(U, null, V(b.value, ([e, t]) => (G(), K("div", { key: e }, [J("dt", null, j(d(e)), 1), J("dd", null, j(t), 1)]))), 128)), J("div", oc, [J("dt", null, j(d("next")), 1), J("dd", sc, j(v.value), 1)])])) : Z("", !0),
			a.value.available ? (G(), K("details", cc, [
				J("summary", null, j(d("details")), 1),
				J("p", null, j(d("modelInfo")), 1),
				J("p", null, j(d(s.value ? "reserveInfo" : e.tariff === "timed" ? "classicInfo" : "dynamicInactive")), 1),
				J("p", null, j(d("setup")), 1),
				s.value ? (G(), K(U, { key: 0 }, [J("dl", lc, [(G(!0), K(U, null, V(x.value, ([e, t]) => (G(), K("div", { key: e }, [J("dt", null, j(d(e)), 1), J("dd", null, j(t), 1)]))), 128))]), (G(!0), K(U, null, V(m.value, (e) => (G(), K("p", { key: e }, j(d("quality")) + ": " + j(R(qs)(e, i.value)), 1))), 128))], 64)) : Z("", !0)
			])) : Z("", !0)
		], 10, Xs)) : Z("", !0);
	}
}), [["styles", [".hems-card{border:1px solid var(--divider-color,#ddd);border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));color:var(--primary-text-color,#212121);overflow-wrap:anywhere;min-width:0;margin-top:20px;padding:22px;line-height:1.55}.hems-card header{flex-wrap:wrap;justify-content:space-between;align-items:center;gap:10px 20px;display:flex}.hems-card h2{margin:0;font-size:18px;font-weight:500}.hems-card__badge{border:1px solid var(--divider-color,#ddd);border-radius:20px;padding:3px 12px;font-size:13px}.hems-card--fallback{border-left:4px solid var(--warning-color,#b87900)}.hems-card p{margin:12px 0}.hems-card__metrics{grid-template-columns:repeat(2,minmax(0,1fr));gap:14px 24px;margin:18px 0;display:grid}.hems-card dt{color:var(--secondary-text-color,#666);font-size:14px}.hems-card dd{font-variant-numeric:tabular-nums;margin:3px 0 0}.hems-card__metrics dd{font-weight:600}.hems-card__next{grid-column:1/-1}.hems-card summary{cursor:pointer;color:var(--primary-text-color,#212121);padding:8px 0;font-weight:500}.hems-card summary:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:3px;border-radius:4px}.hems-card__data{gap:12px;display:grid}.hems-card__data>div{grid-template-columns:minmax(120px,1fr) minmax(0,1.4fr);gap:12px;display:grid}@media (max-width:600px){.hems-card{margin-top:16px;padding:18px}.hems-card__data>div{grid-template-columns:1fr;gap:0}}"]]]), dc = { class: "timed-charging-view" }, fc = /*#__PURE__*/ bo(/* @__PURE__ */ B({
	__name: "TimedChargingView",
	props: { hass: { type: Object } },
	setup(e) {
		let t = [
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
				entities: [
					["select", "timed_charge_mode"],
					["number", "timed_charge_max_soc"],
					["number", "timed_charge_min_soc"]
				]
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
		];
		return (n, r) => (G(), K("div", dc, [
			Y(Os, {
				"switch-key": "timed_charge_enabled",
				cards: t,
				"hide-confirmed-label": ""
			}),
			Y(uc, {
				tariff: "timed",
				hass: e.hass
			}, null, 8, ["hass"]),
			Y(Gs, {
				hass: e.hass,
				class: "timed-charging-view__tariff"
			}, null, 8, ["hass"])
		]));
	}
}), [["styles", [".timed-charging-view{min-width:0}.timed-charging-view__tariff{margin-top:20px}@media (max-width:600px){.timed-charging-view__tariff{margin-top:16px}}@container sax-content (width>=860px){.timed-charging-view__tariff{margin-top:16px}}"]]]), pc = /* @__PURE__ */ B({
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
		return (e, n) => (G(), q(Os, {
			"switch-key": "grid_serving_enabled",
			cards: t
		}));
	}
}), mc = /* @__PURE__ */ B({
	__name: "DynamicChargingView",
	props: { hass: { type: Object } },
	setup(e) {
		let t = jn(qa), n = $(() => t?.entity("select", "price_charge_strategy")?.state?.state === "adaptive"), r = $(() => [{
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
				...n.value ? [["number", "timed_charge_min_soc"], ["number", "timed_charge_max_soc"]] : [],
				["sensor", "price_charge_active_text"],
				["sensor", "price_charge_status_text"],
				...n.value ? [] : [["sensor", "grid_serving_forecast"]],
				["sensor", "price_charge_next_start"],
				["sensor", "price_charge_current_price"]
			]
		}]);
		return (t, n) => (G(), K(U, null, [Y(Os, {
			"switch-key": "price_charge_enabled",
			cards: r.value,
			"hide-confirmed-label": ""
		}, null, 8, ["cards"]), Y(uc, {
			tariff: "dynamic",
			hass: e.hass
		}, null, 8, ["hass"])], 64));
	}
}), hc = { class: "savings-view" }, gc = { class: "savings-overview" }, _c = ["aria-labelledby"], vc = ["id"], yc = ["aria-labelledby"], bc = ["id"], xc = {
	key: 0,
	class: "savings-progress"
}, Sc = ["id"], Cc = { class: "savings-large" }, wc = [
	"role",
	"aria-labelledby",
	"aria-valuemin",
	"aria-valuemax",
	"aria-valuenow"
], Tc = {
	key: 1,
	class: "savings-rows"
}, Ec = { key: 0 }, Dc = { key: 1 }, Oc = { key: 2 }, kc = { key: 3 }, Ac = ["aria-label"], jc = { class: "savings-large" }, Mc = ["aria-labelledby"], Nc = ["id"], Pc = ["for"], Fc = ["id", "max"], Ic = ["for"], Lc = ["id", "min"], Rc = { type: "submit" }, zc = ["disabled"], Bc = {
	key: 0,
	role: "status"
}, Vc = {
	key: 1,
	role: "alert"
}, Hc = { class: "savings-selected-dates" }, Uc = { class: "savings-large" }, Wc = ["id"], Gc = { class: "savings-chart-hint" }, Kc = [
	"viewBox",
	"aria-labelledby",
	"aria-describedby"
], qc = ["id"], Jc = [
	"x1",
	"x2",
	"y1",
	"y2"
], Yc = ["x"], Xc = ["x"], Zc = ["x"], Qc = ["x"], $c = [
	"x",
	"y",
	"width",
	"height"
], el = { class: "savings-chart-table" }, tl = { class: "savings-table-scroll" }, nl = { class: "savings-table" }, rl = {
	key: 1,
	class: "savings-empty"
}, il = { class: "savings-card savings-explanation" }, al = {
	key: 1,
	class: "savings-card savings-status",
	role: "status"
}, ol = /*#__PURE__*/ bo(/* @__PURE__ */ B({
	__name: "SavingsView",
	props: {
		hass: { type: Object },
		entryId: { type: String }
	},
	setup(e) {
		let t = e, n = jn(qa), r = Hn(), i = $(() => n?.language.value === "de"), a = $(() => i.value ? {
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
		}), v = Fs(() => t.hass, () => t.entryId, () => u.value?.metadata.entity_id), y = /* @__PURE__ */ L(""), b = /* @__PURE__ */ L(""), x = null;
		Pn(v.data, (e) => {
			e && ((!y.value && !b.value || y.value === x?.start && b.value === x?.end) && (y.value = e.selected.start_date, b.value = e.selected.end_date), x = {
				start: e.selected.start_date,
				end: e.selected.end_date
			});
		}), Pn(() => t.entryId, () => {
			y.value = "", b.value = "", x = null;
		});
		let S = $(() => v.error.value === "invalid" ? a.value.invalid : v.error.value === "failed" ? a.value.failed : v.error.value === "unavailable" || v.data.value?.status === "recorder_unavailable" ? a.value.noRecorder : null), C = [
			"day",
			"week",
			"month",
			"year"
		], w = $(() => v.data.value?.selected.buckets ?? []), ee = /* @__PURE__ */ L(null), T = /* @__PURE__ */ L(720);
		Pn(ee, (e, t, n) => {
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
		return (t, i) => (G(), K("div", hc, [
			J("div", gc, [o.value?.available && o.value.state?.state === "off" ? (G(), K("section", {
				key: 0,
				class: "savings-card savings-payback",
				"aria-labelledby": `${R(r)}-investment`
			}, [J("h2", { id: `${R(r)}-investment` }, j(a.value.payback), 9, vc), J("p", null, j(a.value.investment), 1)], 8, _c)) : o.value?.available && o.value.state?.state === "on" && (s.value || c.value || l.value || u.value || d.value) ? (G(), K("section", {
				key: 1,
				class: "savings-card savings-payback",
				"aria-labelledby": `${R(r)}-payback`
			}, [
				J("h2", { id: `${R(r)}-payback` }, j(a.value.payback), 9, bc),
				s.value ? (G(), K("div", xc, [
					J("h3", { id: `${R(r)}-progress` }, j(s.value.name), 9, Sc),
					J("p", Cc, j(f.value === null ? a.value.unavailable : `${R(js)(f.value, e.hass)} %`), 1),
					J("div", {
						class: "savings-progress__track",
						role: p.value === null ? void 0 : "meter",
						"aria-labelledby": `${R(r)}-progress`,
						"aria-valuemin": p.value === null ? void 0 : 0,
						"aria-valuemax": p.value === null ? void 0 : 100,
						"aria-valuenow": p.value ?? void 0
					}, [p.value === null ? Z("", !0) : (G(), K("span", {
						key: 0,
						style: ue({ width: `${p.value}%` })
					}, null, 4))], 8, wc)
				])) : Z("", !0),
				c.value || l.value || u.value || d.value ? (G(), K("dl", Tc, [
					c.value ? (G(), K("div", Ec, [J("dt", null, j(c.value.name), 1), J("dd", null, j(m(c.value.available ? c.value.state?.state : null)), 1)])) : Z("", !0),
					l.value ? (G(), K("div", Dc, [J("dt", null, j(a.value.prior), 1), J("dd", null, j(m(l.value.available ? l.value.state?.attributes.prior_result_eur ?? l.value.state?.attributes.prior_result_eur_formatted : null)), 1)])) : Z("", !0),
					u.value ? (G(), K("div", Oc, [J("dt", null, j(a.value.net), 1), J("dd", null, j(m(u.value.available ? u.value.state?.state : null)), 1)])) : Z("", !0),
					d.value ? (G(), K("div", kc, [J("dt", null, j(a.value.started), 1), J("dd", null, j(h(d.value.available ? d.value.state?.attributes.economics_started_at : null)), 1)])) : Z("", !0)
				])) : Z("", !0)
			], 8, yc)) : Z("", !0), u.value ? (G(), K("section", {
				key: 2,
				class: "savings-periods",
				"aria-label": a.value.periods
			}, [(G(), K(U, null, V(C, (e) => J("article", {
				key: e,
				class: "savings-card"
			}, [J("h2", null, j(a.value[e]), 1), J("p", jc, j(R(v).loading.value ? "…" : m(R(v).data.value?.periods[e].change)), 1)])), 64))], 8, Ac)) : Z("", !0)]),
			Y(Gs, {
				hass: e.hass,
				class: "savings-tariff"
			}, null, 8, ["hass"]),
			u.value ? (G(), K("section", {
				key: 0,
				class: "savings-card savings-range",
				"aria-labelledby": `${R(r)}-range`
			}, [
				J("h2", { id: `${R(r)}-range` }, j(a.value.range), 9, Nc),
				J("form", {
					class: "savings-dates",
					onSubmit: i[3] ||= Fa((e) => R(v).select(y.value, b.value), ["prevent"])
				}, [
					J("label", { for: `${R(r)}-from` }, [X(j(a.value.from), 1), On(J("input", {
						id: `${R(r)}-from`,
						"onUpdate:modelValue": i[0] ||= (e) => y.value = e,
						type: "date",
						required: "",
						max: b.value || void 0
					}, null, 8, Fc), [[Ma, y.value]])], 8, Pc),
					J("label", { for: `${R(r)}-to` }, [X(j(a.value.to), 1), On(J("input", {
						id: `${R(r)}-to`,
						"onUpdate:modelValue": i[1] ||= (e) => b.value = e,
						type: "date",
						required: "",
						min: y.value || void 0
					}, null, 8, Lc), [[Ma, b.value]])], 8, Ic),
					J("button", Rc, j(a.value.apply), 1),
					J("button", {
						type: "button",
						disabled: R(v).loading.value,
						onClick: i[2] ||= (...e) => R(v).refresh && R(v).refresh(...e)
					}, j(a.value.refresh), 9, zc)
				], 32),
				R(v).loading.value ? (G(), K("p", Bc, j(a.value.loading), 1)) : S.value ? (G(), K("p", Vc, j(S.value), 1)) : R(v).data.value ? (G(), K(U, { key: 2 }, [
					J("p", Hc, j(g(R(v).data.value.selected.start_date)) + " – " + j(g(R(v).data.value.selected.end_date)), 1),
					J("h3", null, j(a.value.selected), 1),
					J("p", Uc, j(m(R(v).data.value.selected.change)), 1),
					J("h3", { id: `${R(r)}-chart` }, j(a.value.chart), 9, Wc),
					J("p", Gc, j(a.value.chartHint), 1),
					D.value ? (G(), K(U, { key: 0 }, [(G(), K("svg", {
						ref_key: "chartElement",
						ref: ee,
						class: "savings-chart",
						viewBox: `0 0 ${T.value} 240`,
						role: "img",
						"aria-labelledby": `${R(r)}-chart`,
						"aria-describedby": `${R(r)}-chart-description`
					}, [
						J("desc", { id: `${R(r)}-chart-description` }, j(a.value.net) + ": " + j(m(R(v).data.value.selected.change)) + ". " + j(a.value.table) + ". ", 9, qc),
						J("line", {
							x1: E.value.left - 2,
							x2: E.value.right + 2,
							y1: E.value.zero,
							y2: E.value.zero,
							class: "savings-chart__axis"
						}, null, 8, Jc),
						J("text", {
							x: E.value.left - 8,
							y: "24",
							"text-anchor": "end"
						}, j(E.value.highLabel), 9, Yc),
						J("text", {
							x: E.value.left - 8,
							y: "204",
							"text-anchor": "end"
						}, j(E.value.lowLabel), 9, Xc),
						i[4] ||= J("text", {
							x: "10",
							y: "226"
						}, "EUR", -1),
						w.value.length ? (G(), K("text", {
							key: 0,
							x: E.value.left,
							y: "226"
						}, j(O(E.value.start)), 9, Zc)) : Z("", !0),
						w.value.length > 1 ? (G(), K("text", {
							key: 1,
							x: E.value.right,
							y: "226",
							"text-anchor": "end"
						}, j(O(E.value.end)), 9, Qc)) : Z("", !0),
						(G(!0), K(U, null, V(E.value.bars, (e, t) => (G(), K("rect", {
							key: t,
							x: e.x,
							y: e.y,
							width: e.width,
							height: e.height,
							class: A(["savings-chart__bar", { "savings-chart__bar--negative": (e.value ?? 0) < 0 }])
						}, [J("title", null, j(e.label) + ": " + j(m(e.value)), 1)], 10, $c))), 128))
					], 8, Kc)), J("details", el, [J("summary", null, j(a.value.table), 1), J("div", tl, [J("table", nl, [J("thead", null, [J("tr", null, [
						J("th", null, j(a.value.from), 1),
						J("th", null, j(a.value.to), 1),
						J("th", null, j(a.value.net), 1)
					])]), J("tbody", null, [(G(!0), K(U, null, V(E.value.bars, (e, t) => (G(), K("tr", { key: t }, [
						J("td", null, j(e.label), 1),
						J("td", null, j(h(e.end)), 1),
						J("td", null, j(m(e.value)), 1)
					]))), 128))])])])])], 64)) : Z("", !0),
					!D.value || R(v).data.value.selected.change === null ? (G(), K("p", rl, j(R(v).data.value.selected.change === null ? a.value.noData : a.value.noChartData), 1)) : Z("", !0)
				], 64)) : Z("", !0)
			], 8, Mc)) : Z("", !0),
			J("details", il, [
				J("summary", null, j(a.value.explain), 1),
				J("p", null, j(a.value.netHint), 1),
				J("p", null, j(a.value.calendarHint), 1),
				J("p", null, j(a.value.rangeHint), 1)
			]),
			_.value && R(n)?.ready.value ? (G(), K("p", al, j(_.value), 1)) : Z("", !0)
		]));
	}
}), [["styles", [".savings-view{gap:20px;min-width:0;margin-top:24px;display:grid}.savings-overview{display:contents}.savings-card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.savings-card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.savings-card h3{margin:20px 0 8px;font-size:16px;font-weight:500}.savings-card p{overflow-wrap:anywhere;line-height:1.6}.savings-card p:last-child{margin-bottom:0}.savings-large{font-variant-numeric:tabular-nums;margin:0 0 12px;font-size:28px;font-weight:500}.savings-progress__track{background:var(--divider-color,#e0e0e0);border-radius:8px;height:16px;overflow:hidden}.savings-progress__track span{background:var(--info-color,#039be5);height:100%;display:block}.savings-rows{margin:20px 0 0}.savings-rows>div{border-bottom:1px solid var(--divider-color,#e0e0e0);justify-content:space-between;gap:16px;padding:12px 0;line-height:1.5;display:flex}.savings-rows>div:last-child{border-bottom:0;padding-bottom:0}.savings-rows dd{text-align:right;font-variant-numeric:tabular-nums;margin:0}.savings-periods{grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:16px;display:grid}.savings-periods h2{font-size:16px}.savings-table-scroll{overflow-x:auto}.savings-table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%;line-height:1.5}.savings-table th,.savings-table td{text-align:left;border-bottom:1px solid var(--divider-color,#e0e0e0);padding:10px 8px}.savings-table th:last-child,.savings-table td:last-child{text-align:right}.savings-dates{flex-wrap:wrap;align-items:end;gap:16px;display:flex}.savings-dates label{flex:180px;gap:8px;min-width:0;display:grid}.savings-dates input,.savings-dates button{box-sizing:border-box;font:inherit;border:1px solid var(--divider-color,#bdbdbd);background:var(--ha-card-background,var(--card-background-color,#fff));min-height:44px;color:var(--primary-text-color,#212121);border-radius:6px;padding:10px 12px}.savings-dates input{--lightningcss-light:initial;--lightningcss-dark: ;color-scheme:light dark;width:100%}@media (prefers-color-scheme:dark){.savings-dates input{--lightningcss-light: ;--lightningcss-dark:initial}}.savings-dates button{cursor:pointer;color:var(--primary-color,#0288d1)}.savings-dates button:disabled{opacity:.6;cursor:default}.savings-dates :focus-visible,.savings-card summary:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:3px}.savings-selected-dates,.savings-empty{color:var(--secondary-text-color,#666)}.savings-chart{width:100%;height:auto;display:block;overflow:visible}.savings-chart text{fill:var(--secondary-text-color,#666);font-size:12px}.savings-chart__axis{stroke:var(--primary-text-color,#212121);stroke-width:1px}.savings-chart__bar{fill:var(--info-color,#039be5)}.savings-chart__bar--negative{fill:var(--error-color,#db4437)}.savings-card summary{cursor:pointer;min-height:24px;font-weight:500;line-height:1.6}.savings-chart-table{margin-top:16px}.savings-status{margin:0;line-height:1.6}@container sax-content (width>=860px){.savings-view{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;gap:16px;margin-top:16px}.savings-view>*{grid-column:1/-1}.savings-overview{gap:16px;min-width:0;display:grid}.savings-overview:empty{display:none}.savings-view:has(>.savings-overview>section):has(>.savings-tariff)>:is(.savings-overview,.savings-tariff){grid-column:auto}.savings-card{padding:18px}.savings-card h2{margin-bottom:12px;font-size:16px}.savings-card h3{margin-top:16px;font-size:14px}.savings-card p{margin-top:10px;line-height:1.5}.savings-progress h3{margin-top:0}.savings-card .savings-large{margin-top:0;margin-bottom:8px;font-size:24px}.savings-rows{margin-top:12px}.savings-rows>div{gap:12px;padding:8px 0}.savings-rows dt{min-width:0}.savings-rows dd{flex-shrink:0;max-width:58%}.savings-periods{grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.savings-view:has(>.savings-tariff) .savings-periods{grid-template-columns:repeat(2,minmax(0,1fr))}.savings-periods .savings-card{padding:14px 16px}.savings-periods h2{margin-bottom:6px;font-size:14px}.savings-periods .savings-large{margin-bottom:0;font-size:22px}.savings-table th,.savings-table td{padding:7px 8px}.savings-dates{gap:12px}.savings-dates label{flex:0 220px;gap:6px}.savings-range .savings-selected-dates{margin-bottom:8px}.savings-range .savings-chart-hint{margin-top:0;margin-bottom:8px}.savings-chart-table{margin-top:12px}}@media (max-width:600px){.savings-view{gap:16px}.savings-card{padding:20px}.savings-rows>div{flex-wrap:wrap;gap:4px 16px}.savings-rows dd{margin-left:auto}}"]]]), sl = ["lang"], cl = { class: "header" }, ll = ["aria-label"], ul = ["aria-label"], dl = [
	"href",
	"aria-current",
	"onClick"
], fl = {
	key: 0,
	class: "status",
	role: "alert"
}, pl = { class: "introduction" }, ml = {
	class: "section",
	"aria-labelledby": "section-heading"
}, hl = {
	key: 0,
	class: "status",
	role: "status"
}, gl = {
	key: 1,
	class: "status",
	role: "status"
}, _l = {
	key: 7,
	class: "status"
}, vl = ["href"], yl = /* @__PURE__ */ Sa(/* @__PURE__ */ bo(/* @__PURE__ */ B({
	__name: "Panel.ce",
	props: {
		hass: { type: Object },
		narrow: { type: Boolean },
		panel: { type: Object },
		route: { type: Object }
	},
	setup(e) {
		let t = e, n = Ta(), r = Za(() => t.hass, () => t.panel?.config?.entry_id);
		An(qa, r);
		let i = $(() => t.hass?.language.toLowerCase().startsWith("de") ? "de" : "en"), a = $(() => Ga[i.value]), o = $(() => !t.hass?.kioskMode && (t.narrow || t.hass?.dockedSidebar === "always_hidden")), s = $(() => `/${t.panel?.url_path || "sax-power-vue"}`), c = /* @__PURE__ */ L(t.route?.path ?? window.location.pathname), l = $(() => {
			let e = r.entity("switch", "timed_charge_enabled"), t = r.entity("switch", "price_charge_enabled");
			if (e?.available && t?.available) {
				if (e.state?.state === "on" && t.state?.state === "off") return "ladeautomatik";
				if (t.state?.state === "on" && e.state?.state === "off") return "dynamisches-laden";
			}
		}), u = $(() => Ua.filter((e) => !l.value || !["ladeautomatik", "dynamisches-laden"].includes(e.path) || e.path === l.value)), d = $(() => Wa(c.value, s.value)), f = $(() => l.value && ["ladeautomatik", "dynamisches-laden"].includes(d.value) ? l.value : d.value), p = $(() => Ua.find((e) => e.path === f.value)), m = /* @__PURE__ */ L();
		Pn(() => t.route?.path, (e) => {
			e !== void 0 && (c.value = e);
		}), Pn([d, f], ([e, t]) => {
			if (e === t) return;
			let n = `${s.value}/${t}`;
			c.value = n, window.history.replaceState(null, "", n), window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: !0 } })), hn(() => m.value?.focus());
		}, { immediate: !0 });
		function h() {
			c.value = window.location.pathname;
		}
		Qn(() => {
			window.addEventListener("popstate", h), window.addEventListener("location-changed", h);
		}), $n(() => {
			window.removeEventListener("popstate", h), window.removeEventListener("location-changed", h);
		});
		function g(e, t) {
			e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || (e.preventDefault(), window.location.pathname !== t && (window.history.pushState(null, "", t), window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: !1 } }))), h(), hn(() => m.value?.focus()));
		}
		function _() {
			n?.dispatchEvent(new CustomEvent("hass-toggle-menu", {
				bubbles: !0,
				composed: !0
			}));
		}
		return (t, n) => (G(), K("div", {
			class: A(["dashboard", { narrow: e.narrow }]),
			lang: i.value
		}, [
			J("header", cl, [o.value ? (G(), K("button", {
				key: 0,
				class: "menu-button",
				type: "button",
				"aria-label": a.value.menu,
				onClick: _
			}, [...n[1] ||= [J("svg", {
				viewBox: "0 0 24 24",
				"aria-hidden": "true"
			}, [J("path", { d: "M4 6h16M4 12h16M4 18h16" })], -1)]], 8, ll)) : Z("", !0), n[2] ||= J("div", { class: "brand" }, [J("svg", {
				class: "brand-icon",
				viewBox: "0 0 24 24",
				"aria-hidden": "true"
			}, [J("path", { d: "M9 3h6M8 5h8a1 1 0 0 1 1 1v14H7V6a1 1 0 0 1 1-1Z" }), J("path", { d: "m13 8-3 5h4l-3 5" })]), J("span", null, "SAX Power")], -1)]),
			J("nav", {
				class: "navigation",
				"aria-label": a.value.navigation
			}, [(G(!0), K(U, null, V(u.value, (e) => (G(), K("a", {
				key: e.path,
				href: `${s.value}/${e.path}`,
				"aria-current": f.value === e.path ? "page" : void 0,
				onClick: (t) => g(t, `${s.value}/${e.path}`)
			}, j(e[i.value]), 9, dl))), 128))], 8, ul),
			J("main", null, [
				R(r).error.value ? (G(), K("p", fl, j(R(r).error.value), 1)) : Z("", !0),
				J("p", pl, j(a.value.introduction), 1),
				J("section", ml, [J("h1", {
					id: "section-heading",
					ref_key: "heading",
					ref: m,
					tabindex: "-1"
				}, j(p.value?.[i.value] ?? a.value.notFound), 513), e.hass ? e.panel?.config?.entry_id ? f.value === "allgemein" ? (G(), q(Vo, { key: 2 })) : f.value === "ladeautomatik" ? (G(), q(fc, {
					key: 3,
					hass: e.hass
				}, null, 8, ["hass"])) : f.value === "netzdienliches-laden" ? (G(), q(pc, { key: 4 })) : f.value === "dynamisches-laden" ? (G(), q(mc, {
					key: 5,
					hass: e.hass
				}, null, 8, ["hass"])) : f.value === "ersparnis" ? (G(), q(ol, {
					key: 6,
					hass: e.hass,
					"entry-id": e.panel?.config?.entry_id
				}, null, 8, ["hass", "entry-id"])) : (G(), K("div", _l, [J("p", null, j(a.value.notFoundDescription), 1), J("a", {
					href: `${s.value}/allgemein`,
					onClick: n[0] ||= (e) => g(e, `${s.value}/allgemein`)
				}, j(a.value.returnToOverview), 9, vl)])) : (G(), K("p", gl, j(a.value.missingEntry), 1)) : (G(), K("p", hl, j(a.value.loading), 1))])
			])
		], 10, sl));
	}
}), [["styles", [":host{height:100%;color:var(--primary-text-color,#212121);background:var(--primary-background-color,#fafafa);font-family:var(--paper-font-body1_-_font-family,Roboto, sans-serif);font-size:14px;display:block}*{box-sizing:border-box}.dashboard{min-height:100%;container:sax-panel/inline-size}.header{background:var(--app-header-background-color,var(--primary-color,#03a9f4));min-height:64px;color:var(--app-header-text-color,#fff);align-items:center;gap:14px;padding:8px 24px;display:flex}.brand{align-items:center;gap:10px;font-size:20px;font-weight:500;display:flex}.header svg{fill:none;stroke:currentColor;stroke-width:1.7px;stroke-linecap:round;stroke-linejoin:round}.brand-icon{width:30px;height:30px}.menu-button{width:44px;height:44px;color:inherit;cursor:pointer;background:0 0;border:0;border-radius:50%;place-items:center;margin-left:-10px;display:grid}.menu-button svg{width:24px;height:24px}.navigation{border-bottom:1px solid var(--divider-color,#e0e0e0);background:var(--card-background-color,#fff);padding:0 16px;display:flex;overflow-x:auto}.navigation a{min-height:56px;color:var(--secondary-text-color,#666);white-space:nowrap;border-bottom:3px solid #0000;align-items:center;padding:12px 16px;text-decoration:none;display:flex}.navigation a[aria-current=page]{border-color:var(--primary-color,#03a9f4);color:var(--primary-text-color,#212121);font-weight:600}a{color:var(--primary-text-color,#212121);text-underline-offset:3px}a:focus-visible,button:focus-visible{outline-offset:-4px;outline:2px solid}main{max-width:1120px;margin:0 auto;padding:28px 24px 48px}.introduction{color:var(--secondary-text-color,#666);margin:0 0 24px;line-height:1.6}.section{overflow-wrap:anywhere;border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));box-shadow:var(--ha-card-box-shadow,none);padding:28px;container:sax-content/inline-size}h1{margin:0;font-size:24px;font-weight:500;line-height:1.35}h1:focus{outline:none}h2{margin:0 0 12px;font-size:18px;font-weight:500;line-height:1.5}.status{margin-top:24px;line-height:1.7}.narrow .header{padding-left:16px;padding-right:16px}.narrow main{padding:16px 12px 32px}@container sax-panel (width>=940px){.header{min-height:56px;padding:6px 20px}.navigation a{min-height:48px;padding:8px 14px}main{max-width:1360px;padding:16px 20px 20px}.introduction{margin-bottom:12px}.section{padding:20px}h1{font-size:22px}}@media (max-width:600px){.header{gap:8px;padding:8px 16px}.brand{gap:6px;font-size:18px}.brand-icon{display:none}.navigation{padding:0 4px}main{padding:16px 12px 32px}.introduction{margin-bottom:16px}.section{padding:20px}h1{font-size:22px}}"]]]));
customElements.get("sax-power-vue-panel") || customElements.define("sax-power-vue-panel", yl);
//#endregion
export { yl as SaxPowerVuePanel };
