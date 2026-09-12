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
}, l = Object.prototype.hasOwnProperty, u = (e, t) => l.call(e, t), d = Array.isArray, f = (e) => x(e) === "[object Map]", p = (e) => x(e) === "[object Set]", m = (e) => x(e) === "[object Date]", h = (e) => typeof e == "function", g = (e) => typeof e == "string", _ = (e) => typeof e == "symbol", v = (e) => typeof e == "object" && !!e, y = (e) => (v(e) || h(e)) && h(e.then) && h(e.catch), b = Object.prototype.toString, x = (e) => b.call(e), S = (e) => x(e).slice(8, -1), C = (e) => x(e) === "[object Object]", w = (e) => g(e) && e !== "NaN" && e[0] !== "-" && "" + parseInt(e, 10) === e, ee = /* @__PURE__ */ e(",key,ref,ref_for,ref_key,onVnodeBeforeMount,onVnodeMounted,onVnodeBeforeUpdate,onVnodeUpdated,onVnodeBeforeUnmount,onVnodeUnmounted"), te = (e) => {
	let t = /* @__PURE__ */ Object.create(null);
	return ((n) => t[n] || (t[n] = e(n)));
}, ne = /-\w/g, T = te((e) => e.replace(ne, (e) => e.slice(1).toUpperCase())), re = /\B([A-Z])/g, E = te((e) => e.replace(re, "-$1").toLowerCase()), ie = te((e) => e.charAt(0).toUpperCase() + e.slice(1)), ae = te((e) => e ? `on${ie(e)}` : ""), D = (e, t) => !Object.is(e, t), oe = (e, ...t) => {
	for (let n = 0; n < e.length; n++) e[n](...t);
}, se = (e, t, n, r = !1) => {
	Object.defineProperty(e, t, {
		configurable: !0,
		enumerable: !1,
		writable: r,
		value: n
	});
}, ce = (e) => {
	let t = parseFloat(e);
	return isNaN(t) ? e : t;
}, le = (e) => {
	let t = g(e) ? Number(e) : NaN;
	return isNaN(t) ? e : t;
}, ue, de = () => ue ||= typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : typeof global < "u" ? global : {};
function fe(e) {
	if (d(e)) {
		let t = {};
		for (let n = 0; n < e.length; n++) {
			let r = e[n], i = g(r) ? O(r) : fe(r);
			if (i) for (let e in i) t[e] = i[e];
		}
		return t;
	}
	if (g(e) || v(e)) return e;
}
var pe = /;(?![^(]*\))/g, me = /:([^]+)/, he = /\/\*[^]*?\*\//g;
function O(e) {
	let t = {};
	return e.replace(he, "").split(pe).forEach((e) => {
		if (e) {
			let n = e.split(me);
			n.length > 1 && (t[n[0].trim()] = n[1].trim());
		}
	}), t;
}
function ge(e) {
	let t = "";
	if (g(e)) t = e;
	else if (d(e)) for (let n = 0; n < e.length; n++) {
		let r = ge(e[n]);
		r && (t += r + " ");
	}
	else if (v(e)) for (let n in e) e[n] && (t += n + " ");
	return t.trim();
}
var _e = "itemscope,allowfullscreen,formnovalidate,ismap,nomodule,novalidate,readonly", ve = /* @__PURE__ */ e(_e);
_e + "";
function ye(e) {
	return !!e || e === "";
}
function be(e, t) {
	if (e.length !== t.length) return !1;
	let n = !0;
	for (let r = 0; n && r < e.length; r++) n = Se(e[r], t[r]);
	return n;
}
function xe(e, t) {
	if (e.size !== t.size) return !1;
	let n = Array.from(t), r = new Uint8Array(n.length);
	for (let t of e) {
		let e = -1;
		for (let i = 0; i < n.length; i++) if (!r[i] && Se(t, n[i])) {
			e = i;
			break;
		}
		if (e < 0) return !1;
		r[e] = 1;
	}
	return !0;
}
function Se(e, t) {
	if (e === t) return !0;
	let n = m(e), r = m(t);
	if (n || r) return n && r ? e.getTime() === t.getTime() : !1;
	if (n = _(e), r = _(t), n || r) return e === t;
	if (n = d(e), r = d(t), n || r) return n && r ? be(e, t) : !1;
	if (n = v(e), r = v(t), n || r) {
		if (!n || !r) return !1;
		if (n = f(e), r = f(t), n || r || (n = p(e), r = p(t), n || r)) return n && r ? xe(e, t) : !1;
		if (Object.keys(e).length !== Object.keys(t).length) return !1;
		for (let n in e) {
			let r = e.hasOwnProperty(n), i = t.hasOwnProperty(n);
			if (r && !i || !r && i || !Se(e[n], t[n])) return !1;
		}
	}
	return String(e) === String(t);
}
var Ce = (e) => !!(e && e.__v_isRef === !0), k = (e) => g(e) ? e : e == null ? "" : d(e) || v(e) && (e.toString === b || !h(e.toString)) ? Ce(e) ? k(e.value) : JSON.stringify(e, we, 2) : String(e), we = (e, t) => Ce(t) ? we(e, t.value) : f(t) ? { [`Map(${t.size})`]: [...t.entries()].reduce((e, [t, n], r) => (e[Te(t, r) + " =>"] = n, e), {}) } : p(t) ? { [`Set(${t.size})`]: [...t.values()].map((e) => Te(e)) } : _(t) ? Te(t) : v(t) && !d(t) && !C(t) ? String(t) : t, Te = (e, t = "") => _(e) ? `Symbol(${e.description ?? t})` : e, A, Ee = class {
	constructor(e = !1) {
		this.detached = e, this._active = !0, this._on = 0, this.effects = [], this.cleanups = [], this._isPaused = !1, this._warnOnRun = !0, this.__v_skip = !0, !e && A && (A.active ? (this.parent = A, this.index = (A.scopes || (A.scopes = [])).push(this) - 1) : (this._active = !1, this._warnOnRun = !1));
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
			let t = A;
			try {
				return A = this, e();
			} finally {
				A = t;
			}
		}
	}
	on() {
		++this._on === 1 && (this.prevScope = A, A = this);
	}
	off() {
		if (this._on > 0 && --this._on === 0) {
			if (A === this) A = this.prevScope;
			else {
				let e = A;
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
function De() {
	return A;
}
var j, Oe = /* @__PURE__ */ new WeakSet(), ke = class {
	constructor(e) {
		this.fn = e, this.deps = void 0, this.depsTail = void 0, this.flags = 5, this.next = void 0, this.cleanup = void 0, this.scheduler = void 0, A && (A.active ? A.effects.push(this) : this.flags &= -2);
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
		this.flags |= 2, Ge(this), Ie(this);
		let e = j, t = M;
		j = this, M = !0;
		try {
			return this.fn();
		} finally {
			Le(this), j = e, M = t, this.flags &= -3;
		}
	}
	stop() {
		if (this.flags & 1) {
			for (let e = this.deps; e; e = e.nextDep) Be(e);
			this.deps = this.depsTail = void 0, Ge(this), this.onStop && this.onStop(), this.flags &= -2;
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
	if (e.flags & 4 && !(e.flags & 16) || (e.flags &= -17, e.globalVersion === Ke) || (e.globalVersion = Ke, !e.isSSR && e.flags & 128 && (!e.deps && !e._dirty || !Re(e)))) return;
	e.flags |= 2;
	let t = e.dep, n = j, r = M;
	j = e, M = !0;
	try {
		Ie(e);
		let n = e.fn(e._value);
		(t.version === 0 || D(n, e._value)) && (e.flags |= 128, e._value = n, t.version++);
	} catch (e) {
		throw t.version++, e;
	} finally {
		j = n, M = r, Le(e), e.flags &= -3;
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
var M = !0, He = [];
function Ue() {
	He.push(M), M = !1;
}
function We() {
	let e = He.pop();
	M = e === void 0 || e;
}
function Ge(e) {
	let { cleanup: t } = e;
	if (e.cleanup = void 0, t) {
		let e = j;
		j = void 0;
		try {
			t();
		} finally {
			j = e;
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
		if (!j || !M || j === this.computed) return;
		let t = this.activeLink;
		if (t === void 0 || t.sub !== j) t = this.activeLink = new qe(j, this), j.deps ? (t.prevDep = j.depsTail, j.depsTail.nextDep = t, j.depsTail = t) : j.deps = j.depsTail = t, Ye(t);
		else if (t.version === -1 && (t.version = this.version, t.nextDep)) {
			let e = t.nextDep;
			e.prevDep = t.prevDep, t.prevDep && (t.prevDep.nextDep = e), t.prevDep = j.depsTail, t.nextDep = void 0, j.depsTail.nextDep = t, j.depsTail = t, j.deps === t && (j.deps = e);
		}
		return t;
	}
	trigger(e) {
		this.version++, Ke++, this.notify(e);
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
function N(e, t, n) {
	if (M && j) {
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
	if (Pe(), t === "clear") o.forEach(s);
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
	Fe();
}
function tt(e) {
	let t = /* @__PURE__ */ R(e);
	return t === e ? t : (N(t, "iterate", $e), /* @__PURE__ */ L(e) ? t : t.map(z));
}
function nt(e) {
	return N(e = /* @__PURE__ */ R(e), "iterate", $e), e;
}
function P(e, t) {
	return /* @__PURE__ */ I(e) ? zt(/* @__PURE__ */ It(e) ? z(t) : t) : z(t);
}
var rt = {
	__proto__: null,
	[Symbol.iterator]() {
		return it(this, Symbol.iterator, (e) => P(this, e));
	},
	concat(...e) {
		return tt(this).concat(...e.map((e) => d(e) ? tt(e) : e));
	},
	entries() {
		return it(this, "entries", (e) => (e[1] = P(this, e[1]), e));
	},
	every(e, t) {
		return F(this, "every", e, t, void 0, arguments);
	},
	filter(e, t) {
		return F(this, "filter", e, t, (e) => e.map((e) => P(this, e)), arguments);
	},
	find(e, t) {
		return F(this, "find", e, t, (e) => P(this, e), arguments);
	},
	findIndex(e, t) {
		return F(this, "findIndex", e, t, void 0, arguments);
	},
	findLast(e, t) {
		return F(this, "findLast", e, t, (e) => P(this, e), arguments);
	},
	findLastIndex(e, t) {
		return F(this, "findLastIndex", e, t, void 0, arguments);
	},
	forEach(e, t) {
		return F(this, "forEach", e, t, void 0, arguments);
	},
	includes(...e) {
		return st(this, "includes", e);
	},
	indexOf(...e) {
		return st(this, "indexOf", e);
	},
	join(e) {
		return tt(this).join(e);
	},
	lastIndexOf(...e) {
		return st(this, "lastIndexOf", e);
	},
	map(e, t) {
		return F(this, "map", e, t, void 0, arguments);
	},
	pop() {
		return ct(this, "pop");
	},
	push(...e) {
		return ct(this, "push", e);
	},
	reduce(e, ...t) {
		return ot(this, "reduce", e, t);
	},
	reduceRight(e, ...t) {
		return ot(this, "reduceRight", e, t);
	},
	shift() {
		return ct(this, "shift");
	},
	some(e, t) {
		return F(this, "some", e, t, void 0, arguments);
	},
	splice(...e) {
		return ct(this, "splice", e);
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
		return ct(this, "unshift", e);
	},
	values() {
		return it(this, "values", (e) => P(this, e));
	}
};
function it(e, t, n) {
	let r = nt(e), i = r[t]();
	return r !== e && !/* @__PURE__ */ L(e) && (i._next = i.next, i.next = () => {
		let e = i._next();
		return e.done || (e.value = n(e.value)), e;
	}), i;
}
var at = Array.prototype;
function F(e, t, n, r, i, a) {
	let o = nt(e), s = o !== e && !/* @__PURE__ */ L(e), c = o[t];
	if (c !== at[t]) {
		let t = c.apply(e, a);
		return s ? z(t) : t;
	}
	let l = n;
	o !== e && (s ? l = function(t, r) {
		return n.call(this, P(e, t), r, e);
	} : n.length > 2 && (l = function(t, r) {
		return n.call(this, t, r, e);
	}));
	let u = c.call(o, l, r);
	return s && i ? i(u) : u;
}
function ot(e, t, n, r) {
	let i = nt(e), a = i !== e && !/* @__PURE__ */ L(e), o = n, s = !1;
	i !== e && (a ? (s = r.length === 0, o = function(t, r, i) {
		return s && (s = !1, t = P(e, t)), n.call(this, t, P(e, r), i, e);
	}) : n.length > 3 && (o = function(t, r, i) {
		return n.call(this, t, r, i, e);
	}));
	let c = i[t](o, ...r);
	return s ? P(e, c) : c;
}
function st(e, t, n) {
	let r = /* @__PURE__ */ R(e);
	N(r, "iterate", $e);
	let i = r[t](...n);
	return (i === -1 || i === !1) && /* @__PURE__ */ Lt(n[0]) ? (n[0] = /* @__PURE__ */ R(n[0]), r[t](...n)) : i;
}
function ct(e, t, n = []) {
	Ue(), Pe();
	let r = (/* @__PURE__ */ R(e))[t].apply(e, n);
	return Fe(), We(), r;
}
var lt = /* @__PURE__ */ e("__proto__,__v_isRef,__isVue"), ut = new Set(/* @__PURE__ */ Object.getOwnPropertyNames(Symbol).filter((e) => e !== "arguments" && e !== "caller").map((e) => Symbol[e]).filter(_));
function dt(e) {
	_(e) || (e = String(e));
	let t = /* @__PURE__ */ R(this);
	return N(t, "has", e), t.hasOwnProperty(e);
}
var ft = class {
	constructor(e = !1, t = !1) {
		this._isReadonly = e, this._isShallow = t;
	}
	get(e, t, n) {
		if (t === "__v_skip") return e.__v_skip;
		let r = this._isReadonly, i = this._isShallow;
		if (t === "__v_isReactive") return !r;
		if (t === "__v_isReadonly") return r;
		if (t === "__v_isShallow") return i;
		if (t === "__v_raw") return n === (r ? i ? At : kt : i ? Ot : Dt).get(e) || Object.getPrototypeOf(e) === Object.getPrototypeOf(n) ? e : void 0;
		let a = d(e);
		if (!r) {
			let e;
			if (a && (e = rt[t])) return e;
			if (t === "hasOwnProperty") return dt;
		}
		let o = Reflect.get(e, t, /* @__PURE__ */ B(e) ? e : n);
		if ((_(t) ? ut.has(t) : lt(t)) || (r || N(e, "get", t), i)) return o;
		if (/* @__PURE__ */ B(o)) {
			let e = a && w(t) ? o : o.value;
			return r && v(e) ? /* @__PURE__ */ Pt(e) : e;
		}
		return v(o) ? r ? /* @__PURE__ */ Pt(o) : /* @__PURE__ */ Mt(o) : o;
	}
}, pt = class extends ft {
	constructor(e = !1) {
		super(!1, e);
	}
	set(e, t, n, r) {
		let i = e[t], a = d(e) && w(t);
		if (!this._isShallow) {
			let e = /* @__PURE__ */ I(i);
			if (!/* @__PURE__ */ L(n) && !/* @__PURE__ */ I(n) && (i = /* @__PURE__ */ R(i), n = /* @__PURE__ */ R(n)), !a && /* @__PURE__ */ B(i) && !/* @__PURE__ */ B(n)) return e || (i.value = n), !0;
		}
		let o = a ? Number(t) < e.length : u(e, t), s = Reflect.set(e, t, n, /* @__PURE__ */ B(e) ? e : r);
		return e === /* @__PURE__ */ R(r) && s && (o ? D(n, i) && et(e, "set", t, n, i) : et(e, "add", t, n)), s;
	}
	deleteProperty(e, t) {
		let n = u(e, t), r = e[t], i = Reflect.deleteProperty(e, t);
		return i && n && et(e, "delete", t, void 0, r), i;
	}
	has(e, t) {
		let n = Reflect.has(e, t);
		return (!_(t) || !ut.has(t)) && N(e, "has", t), n;
	}
	ownKeys(e) {
		return N(e, "iterate", d(e) ? "length" : Ze), Reflect.ownKeys(e);
	}
}, mt = class extends ft {
	constructor(e = !1) {
		super(!0, e);
	}
	set(e, t) {
		return !0;
	}
	deleteProperty(e, t) {
		return !0;
	}
}, ht = /* @__PURE__ */ new pt(), gt = /* @__PURE__ */ new mt(), _t = /* @__PURE__ */ new pt(!0), vt = (e) => e, yt = (e) => Reflect.getPrototypeOf(e);
function bt(e, t, n) {
	return function(...r) {
		let i = this.__v_raw, a = /* @__PURE__ */ R(i), o = f(a), c = e === "entries" || e === Symbol.iterator && o, l = e === "keys" && o, u = i[e](...r), d = n ? vt : t ? zt : z;
		return !t && N(a, "iterate", l ? Qe : Ze), s(Object.create(u), { next() {
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
function xt(e) {
	return function(...t) {
		return e === "delete" ? !1 : e === "clear" ? void 0 : this;
	};
}
function St(e, t) {
	let n = {
		get(n) {
			let r = this.__v_raw, i = /* @__PURE__ */ R(r), a = /* @__PURE__ */ R(n);
			e || (D(n, a) && N(i, "get", n), N(i, "get", a));
			let { has: o } = yt(i), s = t ? vt : e ? zt : z;
			if (o.call(i, n)) return s(r.get(n));
			if (o.call(i, a)) return s(r.get(a));
			r !== i && r.get(n);
		},
		get size() {
			let t = this.__v_raw;
			return !e && N(/* @__PURE__ */ R(t), "iterate", Ze), t.size;
		},
		has(t) {
			let n = this.__v_raw, r = /* @__PURE__ */ R(n), i = /* @__PURE__ */ R(t);
			return e || (D(t, i) && N(r, "has", t), N(r, "has", i)), t === i ? n.has(t) : n.has(t) || n.has(i);
		},
		forEach(n, r) {
			let i = this, a = i.__v_raw, o = /* @__PURE__ */ R(a), s = t ? vt : e ? zt : z;
			return !e && N(o, "iterate", Ze), a.forEach((e, t) => n.call(r, s(e), s(t), i));
		}
	};
	return s(n, e ? {
		add: xt("add"),
		set: xt("set"),
		delete: xt("delete"),
		clear: xt("clear")
	} : {
		add(e) {
			let n = /* @__PURE__ */ R(this), r = yt(n), i = /* @__PURE__ */ R(e), a = !t && !/* @__PURE__ */ L(e) && !/* @__PURE__ */ I(e) ? i : e;
			return r.has.call(n, a) || D(e, a) && r.has.call(n, e) || D(i, a) && r.has.call(n, i) || (n.add(a), et(n, "add", a, a)), this;
		},
		set(e, n) {
			!t && !/* @__PURE__ */ L(n) && !/* @__PURE__ */ I(n) && (n = /* @__PURE__ */ R(n));
			let r = /* @__PURE__ */ R(this), { has: i, get: a } = yt(r), o = i.call(r, e);
			o ||= (e = /* @__PURE__ */ R(e), i.call(r, e));
			let s = a.call(r, e);
			return r.set(e, n), o ? D(n, s) && et(r, "set", e, n, s) : et(r, "add", e, n), this;
		},
		delete(e) {
			let t = /* @__PURE__ */ R(this), { has: n, get: r } = yt(t), i = n.call(t, e);
			i ||= (e = /* @__PURE__ */ R(e), n.call(t, e));
			let a = r ? r.call(t, e) : void 0, o = t.delete(e);
			return i && et(t, "delete", e, void 0, a), o;
		},
		clear() {
			let e = /* @__PURE__ */ R(this), t = e.size !== 0, n = e.clear();
			return t && et(e, "clear", void 0, void 0, void 0), n;
		}
	}), [
		"keys",
		"values",
		"entries",
		Symbol.iterator
	].forEach((r) => {
		n[r] = bt(r, e, t);
	}), n;
}
function Ct(e, t) {
	let n = St(e, t);
	return (t, r, i) => r === "__v_isReactive" ? !e : r === "__v_isReadonly" ? e : r === "__v_raw" ? t : Reflect.get(u(n, r) && r in t ? n : t, r, i);
}
var wt = { get: /* @__PURE__ */ Ct(!1, !1) }, Tt = { get: /* @__PURE__ */ Ct(!1, !0) }, Et = { get: /* @__PURE__ */ Ct(!0, !1) }, Dt = /* @__PURE__ */ new WeakMap(), Ot = /* @__PURE__ */ new WeakMap(), kt = /* @__PURE__ */ new WeakMap(), At = /* @__PURE__ */ new WeakMap();
function jt(e) {
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
function Mt(e) {
	return /* @__PURE__ */ I(e) ? e : Ft(e, !1, ht, wt, Dt);
}
// @__NO_SIDE_EFFECTS__
function Nt(e) {
	return Ft(e, !1, _t, Tt, Ot);
}
// @__NO_SIDE_EFFECTS__
function Pt(e) {
	return Ft(e, !0, gt, Et, kt);
}
function Ft(e, t, n, r, i) {
	if (!v(e) || e.__v_raw && !(t && e.__v_isReactive) || e.__v_skip || !Object.isExtensible(e)) return e;
	let a = i.get(e);
	if (a) return a;
	let o = jt(S(e));
	if (o === 0) return e;
	let s = new Proxy(e, o === 2 ? r : n);
	return i.set(e, s), s;
}
// @__NO_SIDE_EFFECTS__
function It(e) {
	return /* @__PURE__ */ I(e) ? /* @__PURE__ */ It(e.__v_raw) : !!(e && e.__v_isReactive);
}
// @__NO_SIDE_EFFECTS__
function I(e) {
	return !!(e && e.__v_isReadonly);
}
// @__NO_SIDE_EFFECTS__
function L(e) {
	return !!(e && e.__v_isShallow);
}
// @__NO_SIDE_EFFECTS__
function Lt(e) {
	return e ? !!e.__v_raw : !1;
}
// @__NO_SIDE_EFFECTS__
function R(e) {
	let t = e && e.__v_raw;
	return t ? /* @__PURE__ */ R(t) : e;
}
function Rt(e) {
	return !u(e, "__v_skip") && Object.isExtensible(e) && se(e, "__v_skip", !0), e;
}
var z = (e) => v(e) ? /* @__PURE__ */ Mt(e) : e, zt = (e) => v(e) ? /* @__PURE__ */ Pt(e) : e;
// @__NO_SIDE_EFFECTS__
function B(e) {
	return e ? e.__v_isRef === !0 : !1;
}
// @__NO_SIDE_EFFECTS__
function Bt(e) {
	return Vt(e, !1);
}
function Vt(e, t) {
	return /* @__PURE__ */ B(e) ? e : new Ht(e, t);
}
var Ht = class {
	constructor(e, t) {
		this.dep = new Je(), this.__v_isRef = !0, this.__v_isShallow = !1, this._rawValue = t ? e : /* @__PURE__ */ R(e), this._value = t ? e : z(e), this.__v_isShallow = t;
	}
	get value() {
		return this.dep.track(), this._value;
	}
	set value(e) {
		let t = this._rawValue, n = this.__v_isShallow || /* @__PURE__ */ L(e) || /* @__PURE__ */ I(e);
		e = n ? e : /* @__PURE__ */ R(e), D(e, t) && (this._rawValue = e, this._value = n ? e : z(e), this.dep.trigger());
	}
};
function Ut(e) {
	return /* @__PURE__ */ B(e) ? e.value : e;
}
var Wt = {
	get: (e, t, n) => t === "__v_raw" ? e : Ut(Reflect.get(e, t, n)),
	set: (e, t, n, r) => {
		let i = e[t];
		return /* @__PURE__ */ B(i) && !/* @__PURE__ */ B(n) ? (i.value = n, !0) : Reflect.set(e, t, n, r);
	}
};
function Gt(e) {
	return /* @__PURE__ */ It(e) ? e : new Proxy(e, Wt);
}
var Kt = class {
	constructor(e, t, n) {
		this.fn = e, this.setter = t, this._value = void 0, this.dep = new Je(this), this.__v_isRef = !0, this.deps = void 0, this.depsTail = void 0, this.flags = 16, this.globalVersion = Ke - 1, this.next = void 0, this.effect = this, this.__v_isReadonly = !t, this.isSSR = n;
	}
	notify() {
		if (this.flags |= 16, !(this.flags & 8) && j !== this) return Ne(this, !0), !0;
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
function qt(e, t, n = !1) {
	let r, i;
	return h(e) ? r = e : (r = e.get, i = e.set), new Kt(r, i, n);
}
var Jt = {}, Yt = /* @__PURE__ */ new WeakMap(), Xt = void 0;
function Zt(e, t = !1, n = Xt) {
	if (n) {
		let t = Yt.get(n);
		t || Yt.set(n, t = []), t.push(e);
	}
}
function Qt(e, n, i = t) {
	let { immediate: a, deep: o, once: s, scheduler: l, augmentJob: u, call: f } = i, p = (e) => o ? e : /* @__PURE__ */ L(e) || o === !1 || o === 0 ? $t(e, 1) : $t(e), m, g, _, v, y = !1, b = !1;
	if (/* @__PURE__ */ B(e) ? (g = () => e.value, y = /* @__PURE__ */ L(e)) : /* @__PURE__ */ It(e) ? (g = () => p(e), y = !0) : d(e) ? (b = !0, y = e.some((e) => /* @__PURE__ */ It(e) || /* @__PURE__ */ L(e)), g = () => e.map((e) => {
		if (/* @__PURE__ */ B(e)) return e.value;
		if (/* @__PURE__ */ It(e)) return p(e);
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
		let t = Xt;
		Xt = m;
		try {
			return f ? f(e, 3, [v]) : e(v);
		} finally {
			Xt = t;
		}
	} : r, n && o) {
		let e = g, t = o === !0 ? Infinity : o;
		g = () => $t(e(), t);
	}
	let x = De(), S = () => {
		m.stop(), x && x.active && c(x.effects, m);
	};
	if (s && n) {
		let e = n;
		n = (...t) => {
			let n = e(...t);
			return S(), n;
		};
	}
	let C = b ? Array(e.length).fill(Jt) : Jt, w = (e) => {
		if (m.flags & 1 && (m.dirty || e)) {
			if (n) {
				let t = m.run();
				if (e || o || y || (b ? t.some((e, t) => D(e, C[t])) : D(t, C))) {
					_ && _();
					let e = Xt;
					Xt = m;
					try {
						let e = [
							t,
							C === Jt ? void 0 : b && C[0] === Jt ? [] : C,
							v
						];
						C = t, f ? f(n, 3, e) : n(...e);
					} finally {
						Xt = e;
					}
				}
			} else m.run();
		}
	};
	return u && u(w), m = new ke(g), m.scheduler = l ? () => l(w, !1) : w, v = (e) => Zt(e, !1, m), _ = m.onStop = () => {
		let e = Yt.get(m);
		if (e) {
			if (f) f(e, 4);
			else for (let t of e) t();
			Yt.delete(m);
		}
	}, n ? a ? w(!0) : C = m.run() : l ? l(w.bind(null, !0), !0) : m.run(), S.pause = m.pause.bind(m), S.resume = m.resume.bind(m), S.stop = S, S;
}
function $t(e, t = Infinity, n) {
	if (t <= 0 || !v(e) || e.__v_skip || (n ||= /* @__PURE__ */ new Map(), (n.get(e) || 0) >= t)) return e;
	if (n.set(e, t), t--, /* @__PURE__ */ B(e)) $t(e.value, t, n);
	else if (d(e)) for (let r = 0; r < e.length; r++) $t(e[r], t, n);
	else if (p(e) || f(e)) e.forEach((e) => {
		$t(e, t, n);
	});
	else if (C(e)) {
		for (let r in e) $t(e[r], t, n);
		for (let r of Object.getOwnPropertySymbols(e)) Object.prototype.propertyIsEnumerable.call(e, r) && $t(e[r], t, n);
	}
	return e;
}
//#endregion
//#region node_modules/@vue/runtime-core/dist/runtime-core.esm-bundler.js
function en(e, t, n, r) {
	try {
		return r ? e(...r) : e();
	} catch (e) {
		tn(e, t, n);
	}
}
function V(e, t, n, r) {
	if (h(e)) {
		let i = en(e, t, n, r);
		return i && y(i) && i.catch((e) => {
			tn(e, t, n);
		}), i;
	}
	if (d(e)) {
		let i = [];
		for (let a = 0; a < e.length; a++) i.push(V(e[a], t, n, r));
		return i;
	}
}
function tn(e, n, r, i = !0) {
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
			Ue(), en(o, null, 10, [
				e,
				i,
				a
			]), We();
			return;
		}
	}
	nn(e, r, a, i, s);
}
function nn(e, t, n, r = !0, i = !1) {
	if (i) throw e;
	console.error(e);
}
var H = [], U = -1, rn = [], an = null, on = 0, sn = /* @__PURE__ */ Promise.resolve(), cn = null;
function ln(e) {
	let t = cn || sn;
	return e ? t.then(this ? e.bind(this) : e) : t;
}
function un(e) {
	let t = U + 1, n = H.length;
	for (; t < n;) {
		let r = t + n >>> 1, i = H[r], a = gn(i);
		a < e || a === e && i.flags & 2 ? t = r + 1 : n = r;
	}
	return t;
}
function dn(e) {
	if (!(e.flags & 1)) {
		let t = gn(e), n = H[H.length - 1];
		!n || !(e.flags & 2) && t >= gn(n) ? H.push(e) : H.splice(un(t), 0, e), e.flags |= 1, fn();
	}
}
function fn() {
	cn ||= sn.then(_n);
}
function pn(e) {
	if (!d(e)) an && e.id === -1 ? an.splice(on + 1, 0, e) : e.flags & 1 || (rn.push(e), e.flags |= 1);
	else for (let t = 0; t < e.length; t++) rn.push(e[t]);
	fn();
}
function mn(e, t, n = U + 1) {
	for (; n < H.length; n++) {
		let t = H[n];
		if (t && t.flags & 2) {
			if (e && t.id !== e.uid) continue;
			H.splice(n, 1), n--, t.flags & 4 && (t.flags &= -2), t(), t.flags & 4 || (t.flags &= -2);
		}
	}
}
function hn(e) {
	if (rn.length) {
		let e = [...new Set(rn)].sort((e, t) => gn(e) - gn(t));
		if (rn.length = 0, an) {
			for (let t = 0; t < e.length; t++) an.push(e[t]);
			return;
		}
		for (an = e, on = 0; on < an.length; on++) {
			let e = an[on];
			e.flags & 4 && (e.flags &= -2), e.flags & 8 || e(), e.flags &= -2;
		}
		an = null, on = 0;
	}
}
var gn = (e) => e.id == null ? e.flags & 2 ? -1 : Infinity : e.id;
function _n(e) {
	try {
		for (U = 0; U < H.length; U++) {
			let e = H[U];
			e && !(e.flags & 8) && (e.flags & 4 && (e.flags &= -2), en(e, e.i, e.i ? 15 : 14), e.flags & 4 || (e.flags &= -2));
		}
	} finally {
		for (; U < H.length; U++) {
			let e = H[U];
			e && (e.flags &= -2);
		}
		U = -1, H.length = 0, hn(e), cn = null, (H.length || rn.length) && _n(e);
	}
}
var W = null, vn = null;
function yn(e) {
	let t = W;
	return W = e, vn = e && e.type.__scopeId || null, t;
}
function bn(e, t = W, n) {
	if (!t || e._n) return e;
	let r = (...n) => {
		r._d && Kr(-1);
		let i = yn(t), a = Ur.length, o;
		try {
			o = e(...n);
		} finally {
			for (let e = Ur.length; e > a; e--) Wr();
			yn(i), r._d && Kr(1);
		}
		return o;
	};
	return r._n = !0, r._c = !0, r._d = !0, r;
}
function xn(e, t, n, r) {
	let i = e.dirs, a = t && t.dirs;
	for (let o = 0; o < i.length; o++) {
		let s = i[o];
		a && (s.oldValue = a[o].value);
		let c = s.dir[r];
		c && (Ue(), V(c, n, 8, [
			e.el,
			s,
			e,
			t
		]), We());
	}
}
function Sn(e, t, n = !1) {
	let r = pi();
	if (r || er) {
		let i = er ? er._context.provides : r ? r.parent == null || r.ce ? r.vnode.appContext && r.vnode.appContext.provides : r.parent.provides : void 0;
		if (i && e in i) return i[e];
		if (arguments.length > 1) return n && h(t) ? t.call(r && r.proxy) : t;
	}
}
var Cn = /* @__PURE__ */ Symbol.for("v-scx"), wn = () => Sn(Cn);
function Tn(e, t, n) {
	return En(e, t, n);
}
function En(e, n, i = t) {
	let { immediate: a, deep: o, flush: c, once: l } = i, u = s({}, i), d = n && a || !n && c !== "post", f;
	if (yi) {
		if (c === "sync") {
			let e = wn();
			f = e.__watcherHandles ||= [];
		} else if (!d) {
			let e = () => {};
			return e.stop = r, e.resume = r, e.pause = r, e;
		}
	}
	let p = fi;
	u.call = (e, t, n) => V(e, p, t, n);
	let m = !1;
	c === "post" ? u.scheduler = (e) => {
		G(e, p && p.suspense);
	} : c !== "sync" && (m = !0, u.scheduler = (e, t) => {
		t ? e() : dn(e);
	}), u.augmentJob = (e) => {
		n && (e.flags |= 4), m && (e.flags |= 2, p && (e.id = p.uid, e.i = p));
	};
	let h = Qt(e, n, u);
	return yi && (f ? f.push(h) : d && h()), h;
}
var Dn = /* @__PURE__ */ Symbol("_vte"), On = (e) => e.__isTeleport, kn = /* @__PURE__ */ Symbol("_leaveCb");
function An(e) {
	let t = e[0];
	if (e.length > 1) {
		for (let n of e) if (n.type !== q) {
			t = n;
			break;
		}
	}
	return t;
}
function jn(e) {
	if (!Bn(e)) return On(e.type) && e.children ? An(e.children) : e;
	if (e.component) return e.component.subTree;
	let { shapeFlag: t, children: n } = e;
	if (n) {
		if (t & 16) return n[0];
		if (t & 32 && h(n.default)) return n.default();
	}
}
function Mn(e, t) {
	if (e.shapeFlag & 6 && e.component) {
		e.transition = t;
		let n = e.component.subTree;
		Mn(On(n.type) && jn(n) || n, t);
	} else e.shapeFlag & 128 ? (e.ssContent.transition = t.clone(e.ssContent), e.ssFallback.transition = t.clone(e.ssFallback)) : e.transition = t;
}
// @__NO_SIDE_EFFECTS__
function Nn(e, t) {
	return h(e) ? /* @__PURE__ */ s({ name: e.name }, t, { setup: e }) : e;
}
function Pn(e) {
	e.ids = [
		e.ids[0] + e.ids[2]++ + "-",
		0,
		0
	];
}
function Fn(e, t) {
	let n;
	return !!((n = Object.getOwnPropertyDescriptor(e, t)) && !n.configurable);
}
var In = /* @__PURE__ */ new WeakMap();
function Ln(e, n, r, a, o = !1) {
	if (d(e)) {
		e.forEach((e, t) => Ln(e, n && (d(n) ? n[t] : n), r, a, o));
		return;
	}
	if (zn(a) && !o) {
		a.shapeFlag & 512 && a.type.__asyncResolved && a.component.subTree.component && Ln(e, n, r, a.component.subTree);
		return;
	}
	let s = a.shapeFlag & 4 ? Ei(a.component) : a.el, l = o ? null : s, { i: f, r: p } = e, m = n && n.r, _ = f.refs === t ? f.refs = {} : f.refs, v = f.setupState, y = /* @__PURE__ */ R(v), b = v === t ? i : (e) => !Fn(_, e) && u(y, e), x = (e, t) => !(t && Fn(_, t));
	if (m != null && m !== p) {
		if (Rn(n), g(m)) _[m] = null, b(m) && (v[m] = null);
		else if (/* @__PURE__ */ B(m)) {
			let e = n;
			x(m, e.k) && (m.value = null), e.k && (_[e.k] = null);
		}
	}
	if (h(p)) en(p, f, 12, [l, _]);
	else {
		let t = g(p), n = /* @__PURE__ */ B(p);
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
					i(), In.delete(e);
				};
				t.id = -1, In.set(e, t), G(t, r);
			} else Rn(e), i();
		}
	}
}
function Rn(e) {
	let t = In.get(e);
	t && (t.flags |= 8, In.delete(e));
}
de().requestIdleCallback, de().cancelIdleCallback;
var zn = (e) => !!e.type.__asyncLoader, Bn = (e) => e.type.__isKeepAlive;
function Vn(e, t, n = fi, r = !1) {
	if (n) {
		let i = n[e] || (n[e] = []), a = t.__weh ||= (...r) => {
			Ue();
			let i = gi(n), a = V(t, n, e, r);
			return i(), We(), a;
		};
		return r ? i.unshift(a) : i.push(a), a;
	}
}
var Hn = (e) => (t, n = fi) => {
	(!yi || e === "sp") && Vn(e, (...e) => t(...e), n);
}, Un = Hn("m"), Wn = Hn("bum"), Gn = /* @__PURE__ */ Symbol.for("v-ndc");
function Kn(e, t, n, r) {
	let i, a = n && n[r], o = d(e);
	if (o || g(e)) {
		let n = o && /* @__PURE__ */ It(e), r = !1, s = !1;
		n && (r = !/* @__PURE__ */ L(e), s = /* @__PURE__ */ I(e), e = nt(e)), i = Array(e.length);
		for (let n = 0, o = e.length; n < o; n++) i[n] = t(r ? s ? zt(z(e[n])) : z(e[n]) : e[n], n, void 0, a && a[n]);
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
var qn = (e) => e ? vi(e) ? Ei(e) : qn(e.parent) : null, Jn = /* @__PURE__ */ s(/* @__PURE__ */ Object.create(null), {
	$: (e) => e,
	$el: (e) => e.vnode.el,
	$data: (e) => e.data,
	$props: (e) => e.props,
	$attrs: (e) => e.attrs,
	$slots: (e) => e.slots,
	$refs: (e) => e.refs,
	$parent: (e) => qn(e.parent),
	$root: (e) => qn(e.root),
	$host: (e) => e.ce,
	$emit: (e) => e.emit,
	$options: (e) => e.type,
	$forceUpdate: (e) => e.f ||= () => {
		dn(e.update);
	},
	$nextTick: (e) => e.n ||= ln.bind(e.proxy),
	$watch: (e) => r
}), Yn = (e, n) => e !== t && !e.__isScriptSetup && u(e, n), Xn = {
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
			else if (Yn(i, n)) return s[n] = 1, i[n];
			else if (u(o, n)) return s[n] = 3, o[n];
			else if (r !== t && u(r, n)) return s[n] = 4, r[n];
			else s[n] = 0;
		}
		let d = Jn[n], f, p;
		if (d) return n === "$attrs" && N(e.attrs, "get", ""), d(e);
		if ((f = c.__cssModules) && (f = f[n])) return f;
		if (r !== t && u(r, n)) return s[n] = 4, r[n];
		if (p = l.config.globalProperties, u(p, n)) return p[n];
	},
	set({ _: e }, t, n) {
		let { data: r, setupState: i, ctx: a } = e;
		return Yn(i, t) ? (i[t] = n, !0) : u(e.props, t) || t[0] === "$" && t.slice(1) in e ? !1 : (a[t] = n, !0);
	},
	has({ _: { data: e, setupState: t, accessCache: n, ctx: r, appContext: i, props: a, type: o } }, s) {
		let c;
		return !!(n[s] || Yn(t, s) || u(a, s) || u(r, s) || u(Jn, s) || u(i.config.globalProperties, s) || (c = o.__cssModules) && c[s]);
	},
	defineProperty(e, t, n) {
		return n.get == null ? u(n, "value") && this.set(e, t, n.value, null) : e._.accessCache[t] = 0, Reflect.defineProperty(e, t, n);
	}
};
function Zn() {
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
var Qn = 0;
function $n(e, t) {
	return function(n, r = null) {
		h(n) || (n = s({}, n)), r != null && !v(r) && (r = null);
		let i = Zn(), a = /* @__PURE__ */ new WeakSet(), o = [], c = !1, l = i.app = {
			_uid: Qn++,
			_component: n,
			_props: r,
			_container: null,
			_context: i,
			_instance: null,
			version: ki,
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
					let u = l._ceVNode || Z(n, r);
					return u.appContext = i, s === !0 ? s = "svg" : s === !1 && (s = void 0), o && t ? t(u, a) : e(u, a, s), c = !0, l._container = a, a.__vue_app__ = l, Ei(u.component);
				}
			},
			onUnmount(e) {
				o.push(e);
			},
			unmount() {
				c && (V(o, l._instance, 16), e(null, l._container), delete l._container.__vue_app__);
			},
			provide(e, t) {
				return i.provides[e] = t, l;
			},
			runWithContext(e) {
				let t = er;
				er = l;
				try {
					return e();
				} finally {
					er = t;
				}
			}
		};
		return l;
	};
}
var er = null, tr = (e, t) => t === "modelValue" || t === "model-value" ? e.modelModifiers : e[`${t}Modifiers`] || e[`${T(t)}Modifiers`] || e[`${E(t)}Modifiers`];
function nr(e, n, ...r) {
	if (e.isUnmounted) return;
	let i = e.vnode.props || t, a = r, o = n.startsWith("update:"), s = o && tr(i, n.slice(7));
	s && (s.trim && (a = r.map((e) => g(e) ? e.trim() : e)), s.number && (a = a.map(ce)));
	let c, l = i[c = ae(n)] || i[c = ae(T(n))];
	!l && o && (l = i[c = ae(E(n))]), l && V(l, e, 6, a);
	let u = i[c + "Once"];
	if (u) {
		if (!e.emitted) e.emitted = {};
		else if (e.emitted[c]) return;
		e.emitted[c] = !0, V(u, e, 6, a);
	}
}
function rr(e, t, n = !1) {
	let r = t.emitsCache, i = r.get(e);
	if (i !== void 0) return i;
	let a = e.emits, o = {};
	return a ? (d(a) ? a.forEach((e) => o[e] = null) : s(o, a), v(e) && r.set(e, o), o) : (v(e) && r.set(e, null), null);
}
function ir(e, t) {
	return !e || !a(t) ? !1 : (t = t.slice(2), t = t === "Once" ? t : t.replace(/Once$/, ""), u(e, t[0].toLowerCase() + t.slice(1)) || u(e, E(t)) || u(e, t));
}
function ar(e) {
	let { type: t, vnode: n, proxy: r, withProxy: i, propsOptions: [a], slots: s, attrs: c, emit: l, render: u, renderCache: d, props: f, data: p, setupState: m, ctx: h, inheritAttrs: g } = e, _ = yn(e), v, y;
	try {
		if (n.shapeFlag & 4) {
			let e = i || r, t = e;
			v = Q(u.call(t, e, d, f, m, p, h)), y = c;
		} else {
			let e = t;
			v = Q(e.length > 1 ? e(f, {
				attrs: c,
				slots: s,
				emit: l
			}) : e(f, null)), y = t.props ? c : or(c);
		}
	} catch (t) {
		Ur.length = 0, tn(t, e, 1), v = Z(q);
	}
	let b = v;
	if (y && g !== !1) {
		let e = Object.keys(y), { shapeFlag: t } = b;
		e.length && t & 7 && (a && e.some(o) && (y = sr(y, a)), b = ni(b, y, !1, !0));
	}
	return n.dirs && (b = ni(b, null, !1, !0), b.dirs = b.dirs ? b.dirs.concat(n.dirs) : n.dirs), n.transition && Mn(On(b.type) && jn(b) || b, n.transition), v = b, yn(_), v;
}
var or = (e) => {
	let t;
	for (let n in e) (n === "class" || n === "style" || a(n)) && ((t ||= {})[n] = e[n]);
	return t;
}, sr = (e, t) => {
	let n = {};
	for (let r in e) (!o(r) || !(r.slice(9) in t)) && (n[r] = e[r]);
	return n;
};
function cr(e, t, n) {
	let { props: r, children: i, component: a } = e, { props: o, children: s, patchFlag: c } = t, l = a.emitsOptions;
	if (t.dirs || t.transition) return !0;
	if (n && c >= 0) {
		if (c & 1024) return !0;
		if (c & 16) return r ? lr(r, o, l) : !!o;
		if (c & 8) {
			let e = t.dynamicProps;
			for (let t = 0; t < e.length; t++) {
				let n = e[t];
				if (ur(o, r, n) && !ir(l, n)) return !0;
			}
		}
	} else return (i || s) && (!s || !s.$stable) ? !0 : r === o ? !1 : r ? !o || lr(r, o, l) : !!o;
	return !1;
}
function lr(e, t, n) {
	let r = Object.keys(t);
	if (r.length !== Object.keys(e).length) return !0;
	for (let i = 0; i < r.length; i++) {
		let a = r[i];
		if (ur(t, e, a) && !ir(n, a)) return !0;
	}
	return !1;
}
function ur(e, t, n) {
	let r = e[n], i = t[n];
	return n === "style" && v(r) && v(i) ? !Se(r, i) : r !== i;
}
function dr({ vnode: e, parent: t, suspense: n }, r) {
	for (; t;) {
		let n = t.subTree;
		if (n.suspense && n.suspense.activeBranch === e && (n.suspense.vnode.el = n.el = r, e = n), n === e) (e = t.vnode).el = r, t = t.parent;
		else break;
	}
	n && n.activeBranch === e && (n.vnode.el = r);
}
var fr = {}, pr = () => Object.create(fr), mr = (e) => Object.getPrototypeOf(e) === fr;
function hr(e, t, n, r = !1) {
	let i = {}, a = pr();
	e.propsDefaults = /* @__PURE__ */ Object.create(null), _r(e, t, i, a);
	for (let t in e.propsOptions[0]) t in i || (i[t] = void 0);
	e.props = n ? r ? i : /* @__PURE__ */ Nt(i) : e.type.props ? i : a, e.attrs = a;
}
function gr(e, t, n, r) {
	let { props: i, attrs: a, vnode: { patchFlag: o } } = e, s = /* @__PURE__ */ R(i), [c] = e.propsOptions, l = !1;
	if ((r || o > 0) && !(o & 16)) {
		if (o & 8) {
			let n = e.vnode.dynamicProps;
			for (let r = 0; r < n.length; r++) {
				let o = n[r];
				if (ir(e.emitsOptions, o)) continue;
				let d = t[o];
				if (c) {
					if (u(a, o)) d !== a[o] && (a[o] = d, l = !0);
					else {
						let t = T(o);
						i[t] = vr(c, s, t, d, e, !1);
					}
				} else d !== a[o] && (a[o] = d, l = !0);
			}
		}
	} else {
		_r(e, t, i, a) && (l = !0);
		let r;
		for (let a in s) (!t || !u(t, a) && ((r = E(a)) === a || !u(t, r))) && (c ? n && (n[a] !== void 0 || n[r] !== void 0) && (i[a] = vr(c, s, a, void 0, e, !0)) : delete i[a]);
		if (a !== s) for (let e in a) (!t || !u(t, e)) && (delete a[e], l = !0);
	}
	l && et(e.attrs, "set", "");
}
function _r(e, n, r, i) {
	let [a, o] = e.propsOptions, s = !1, c;
	if (n) for (let t in n) {
		if (ee(t)) continue;
		let l = n[t], d;
		a && u(a, d = T(t)) ? !o || !o.includes(d) ? r[d] = l : (c ||= {})[d] = l : ir(e.emitsOptions, t) || (!(t in i) || l !== i[t]) && (i[t] = l, s = !0);
	}
	if (o) {
		let n = /* @__PURE__ */ R(r), i = c || t;
		for (let t = 0; t < o.length; t++) {
			let s = o[t];
			r[s] = vr(a, n, s, i[s], e, !u(i, s));
		}
	}
	return s;
}
function vr(e, t, n, r, i, a) {
	let o = e[n];
	if (o != null) {
		let e = u(o, "default");
		if (e && r === void 0) {
			let e = o.default;
			if (o.type !== Function && !o.skipFactory && h(e)) {
				let { propsDefaults: a } = i;
				if (n in a) r = a[n];
				else {
					let o = gi(i);
					r = a[n] = e.call(null, t), o();
				}
			} else r = e;
			i.ce && i.ce._setProp(n, r);
		}
		o[0] && (a && !e ? r = !1 : o[1] && (r === "" || r === E(n)) && (r = !0));
	}
	return r;
}
function yr(e, r, i = !1) {
	let a = r.propsCache, o = a.get(e);
	if (o) return o;
	let c = e.props, l = {}, f = [];
	if (!c) return v(e) && a.set(e, n), n;
	if (d(c)) for (let e = 0; e < c.length; e++) {
		let n = T(c[e]);
		br(n) && (l[n] = t);
	}
	else if (c) for (let e in c) {
		let t = T(e);
		if (br(t)) {
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
function br(e) {
	return e[0] !== "$" && !ee(e);
}
var xr = (e) => e === "_" || e === "_ctx" || e === "$stable", Sr = (e) => d(e) ? e.map(Q) : [Q(e)], Cr = (e, t, n) => {
	if (t._n) return t;
	let r = bn((...e) => Sr(t(...e)), n);
	return r._c = !1, r;
}, wr = (e, t, n) => {
	let r = e._ctx;
	for (let n in e) {
		if (xr(n)) continue;
		let i = e[n];
		if (h(i)) t[n] = Cr(n, i, r);
		else if (i != null) {
			let e = Sr(i);
			t[n] = () => e;
		}
	}
}, Tr = (e, t) => {
	let n = Sr(t);
	e.slots.default = () => n;
}, Er = (e, t, n) => {
	for (let r in t) (n || !xr(r)) && (e[r] = t[r]);
}, Dr = (e, t, n) => {
	let r = e.slots = pr();
	if (e.vnode.shapeFlag & 32) {
		let e = t._;
		e ? (Er(r, t, n), n && se(r, "_", e, !0)) : wr(t, r);
	} else t && Tr(e, t);
}, Or = (e, n, r) => {
	let { vnode: i, slots: a } = e, o = !0, s = t;
	if (i.shapeFlag & 32) {
		let e = n._;
		e ? r && e === 1 ? o = !1 : Er(a, n, r) : (o = !n.$stable, wr(n, a)), s = n;
	} else n && (Tr(e, n), s = { default: 1 });
	if (o) for (let e in a) !xr(e) && s[e] == null && delete a[e];
}, G = Br;
function kr(e) {
	return Ar(e);
}
function Ar(e, i) {
	let a = de();
	a.__VUE__ = !0;
	let { insert: o, remove: s, patchProp: c, createElement: l, createText: u, createComment: d, setText: f, setElementText: p, parentNode: m, nextSibling: h, setScopeId: g = r, insertStaticContent: _ } = e, v = (e, t, n, r = null, i = null, a = null, o = void 0, s = null, c = !!t.dynamicChildren) => {
		if (e === t) return;
		e && !Zr(e, t) && (r = be(e), O(e, i, a, !0), e = null), t.patchFlag === -2 && (c = !1, t.dynamicChildren = null);
		let { type: l, ref: u, shapeFlag: d } = t;
		switch (l) {
			case Vr:
				y(e, t, n, r);
				break;
			case q:
				b(e, t, n, r);
				break;
			case Hr:
				e ?? x(t, n, r, o);
				break;
			case K:
				ae(e, t, n, r, i, a, o, s, c);
				break;
			default: d & 1 ? w(e, t, n, r, i, a, o, s, c) : d & 6 ? D(e, t, n, r, i, a, o, s, c) : (d & 64 || d & 128) && l.process(e, t, n, r, i, a, o, s, c, Ce);
		}
		u != null && i ? Ln(u, e && e.ref, a, t || e, !t) : u == null && e && e.ref != null && Ln(e.ref, null, a, e, !0);
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
		if (t.type === "svg" ? o = "svg" : t.type === "math" && (o = "mathml"), e == null) te(t, n, r, i, a, o, s, c);
		else {
			let n = e.el && e.el._isVueCE ? e.el : null;
			try {
				n && n._beginPatch(), re(e, t, i, a, o, s, c);
			} finally {
				n && n._endPatch();
			}
		}
	}, te = (e, t, n, r, i, a, s, u) => {
		let d, f, { props: m, shapeFlag: h, transition: g, dirs: _ } = e;
		if (d = e.el = l(e.type, a, m && m.is, m), h & 8 ? p(d, e.children) : h & 16 && T(e.children, d, null, r, i, jr(e, a), s, u), _ && xn(e, null, r, "created"), ne(d, e, e.scopeId, s, r), m) {
			for (let e in m) e !== "value" && !ee(e) && c(d, e, null, m[e], a, r);
			"value" in m && c(d, "value", null, m.value, a), (f = m.onVnodeBeforeMount) && $(f, r, e);
		}
		_ && xn(e, null, r, "beforeMount");
		let v = Nr(i, g);
		v && g.beforeEnter(d), o(d, t, n), ((f = m && m.onVnodeMounted) || v || _) && G(() => {
			try {
				f && $(f, r, e), v && g.enter(d), _ && xn(e, null, r, "mounted");
			} finally {}
		}, i);
	}, ne = (e, t, n, r, i) => {
		if (n && g(e, n), r) for (let t = 0; t < r.length; t++) g(e, r[t]);
		if (i) {
			let n = i.subTree;
			if (t === n || zr(n.type) && (n.ssContent === t || n.ssFallback === t)) {
				let t = i.vnode;
				ne(e, t, t.scopeId, t.slotScopeIds, i.parent);
			}
		}
	}, T = (e, t, n, r, i, a, o, s, c = 0) => {
		for (let l = c; l < e.length; l++) {
			let c = e[l] = s ? oi(e[l]) : Q(e[l]);
			v(null, c, t, n, r, i, a, o, s);
		}
	}, re = (e, n, r, i, a, o, s) => {
		let l = n.el = e.el, { patchFlag: u, dynamicChildren: d, dirs: f } = n;
		u |= e.patchFlag & 16;
		let m = e.props || t, h = n.props || t, g;
		if (r && Mr(r, !1), (g = h.onVnodeBeforeUpdate) && $(g, r, n, e), f && xn(n, e, r, "beforeUpdate"), r && Mr(r, !0), d && (!e.dynamicChildren || e.dynamicChildren.length !== d.length) && (u = 0, s = !1, d = null), (m.innerHTML && h.innerHTML == null || m.textContent && h.textContent == null) && p(l, ""), d ? E(e.dynamicChildren, d, l, r, i, jr(n, a), o) : s || fe(e, n, l, null, r, i, jr(n, a), o, !1), u > 0) {
			if (u & 16) ie(l, m, h, r, a);
			else if (u & 2 && m.class !== h.class && c(l, "class", null, h.class, a), u & 4 && c(l, "style", m.style, h.style, a), u & 8) {
				let e = n.dynamicProps;
				for (let t = 0; t < e.length; t++) {
					let n = e[t], i = m[n], o = h[n];
					(o !== i || n === "value") && c(l, n, i, o, a, r);
				}
			}
			u & 1 && e.children !== n.children && p(l, n.children);
		} else !s && d == null && ie(l, m, h, r, a);
		((g = h.onVnodeUpdated) || f) && G(() => {
			g && $(g, r, n, e), f && xn(n, e, r, "updated");
		}, i);
	}, E = (e, t, n, r, i, a, o) => {
		for (let s = 0; s < t.length; s++) {
			let c = e[s], l = t[s], u = c.el && (c.type === K || !Zr(c, l) || c.shapeFlag & 198) ? m(c.el) : n;
			v(c, l, u, null, r, i, a, o, !0);
		}
	}, ie = (e, n, r, i, a) => {
		if (n !== r) {
			if (n !== t) for (let t in n) !ee(t) && !(t in r) && c(e, t, n[t], null, a, i);
			for (let t in r) {
				if (ee(t)) continue;
				let o = r[t], s = n[t];
				o !== s && t !== "value" && c(e, t, s, o, a, i);
			}
			"value" in r && c(e, "value", n.value, r.value, a);
		}
	}, ae = (e, t, n, r, i, a, s, c, l) => {
		let d = t.el = e ? e.el : u(""), f = t.anchor = e ? e.anchor : u(""), { patchFlag: p, dynamicChildren: m, slotScopeIds: h } = t;
		h && (c = c ? c.concat(h) : h), e == null ? (o(d, n, r), o(f, n, r), T(t.children || [], n, f, i, a, s, c, l)) : p > 0 && p & 64 && m && e.dynamicChildren && e.dynamicChildren.length === m.length ? (E(e.dynamicChildren, m, n, i, a, s, c), (t.key != null || i && t === i.subTree) && Pr(e, t, !0)) : fe(e, t, n, f, i, a, s, c, l);
	}, D = (e, t, n, r, i, a, o, s, c) => {
		t.slotScopeIds = s, e == null ? t.shapeFlag & 512 ? i.ctx.activate(t, n, r, o, c) : se(t, n, r, i, a, o, c) : ce(e, t, c);
	}, se = (e, t, n, r, i, a, o) => {
		let s = e.component = di(e, r, i);
		if (Bn(e) && (s.ctx.renderer = Ce), bi(s, !1, o), s.asyncDep) {
			if (i && i.registerDep(s, le, o), !e.el) {
				let r = s.subTree = Z(q);
				b(null, r, t, n), e.placeholder = r.el;
			}
		} else le(s, e, t, n, i, a, o);
	}, ce = (e, t, n) => {
		let r = t.component = e.component;
		if (cr(e, t, n)) {
			if (r.asyncDep && !r.asyncResolved) {
				ue(r, t, n);
				return;
			}
			r.next = t, r.update();
		} else t.el = e.el, r.vnode = t;
	}, le = (e, t, n, r, i, a, o) => {
		let s = () => {
			if (e.isMounted) {
				let { next: t, bu: n, u: r, parent: s, vnode: c } = e;
				{
					let n = Ir(e);
					if (n) {
						t && (t.el = c.el, ue(e, t, o)), n.asyncDep.then(() => {
							G(() => {
								e.isUnmounted || l();
							}, i);
						});
						return;
					}
				}
				let u = t, d;
				Mr(e, !1), t ? (t.el = c.el, ue(e, t, o)) : t = c, n && oe(n), (d = t.props && t.props.onVnodeBeforeUpdate) && $(d, s, t, c), Mr(e, !0);
				let f = ar(e), p = e.subTree;
				e.subTree = f, v(p, f, m(p.el), be(p), e, i, a), t.el = f.el, u === null && dr(e, f.el), r && G(r, i), (d = t.props && t.props.onVnodeUpdated) && G(() => $(d, s, t, c), i);
			} else {
				let o, { el: s, props: c } = t, { bm: l, m: u, parent: d, root: f, type: p } = e, m = zn(t);
				if (Mr(e, !1), l && oe(l), !m && (o = c && c.onVnodeBeforeMount) && $(o, d, t), Mr(e, !0), s && we) {
					let t = () => {
						e.subTree = ar(e), we(s, e.subTree, e, i, null);
					};
					m && p.__asyncHydrate ? p.__asyncHydrate(s, e, t) : t();
				} else {
					f.ce && f.ce._hasShadowRoot() && f.ce._injectChildStyle(p, e.parent ? e.parent.type : void 0);
					let o = e.subTree = ar(e);
					v(null, o, n, r, e, i, a), t.el = o.el;
				}
				if (u && G(u, i), !m && (o = c && c.onVnodeMounted)) {
					let e = t;
					G(() => $(o, d, e), i);
				}
				(t.shapeFlag & 256 || d && zn(d.vnode) && d.vnode.shapeFlag & 256) && e.a && G(e.a, i), e.isMounted = !0, t = n = r = null;
			}
		};
		e.scope.on();
		let c = e.effect = new ke(s);
		e.scope.off();
		let l = e.update = c.run.bind(c), u = e.job = c.runIfDirty.bind(c);
		u.i = e, u.id = e.uid, c.scheduler = () => dn(u), Mr(e, !0), l();
	}, ue = (e, t, n) => {
		t.component = e;
		let r = e.vnode.props;
		e.vnode = t, e.next = null, gr(e, t.props, r, n), Or(e, t.children, n), Ue(), mn(e), We();
	}, fe = (e, t, n, r, i, a, o, s, c = !1) => {
		let l = e && e.children, u = e ? e.shapeFlag : 0, d = t.children, { patchFlag: f, shapeFlag: m } = t;
		if (f > 0) {
			if (f & 128) {
				me(l, d, n, r, i, a, o, s, c);
				return;
			}
			if (f & 256) {
				pe(l, d, n, r, i, a, o, s, c);
				return;
			}
		}
		m & 8 ? (u & 16 && ye(l, i, a), d !== l && p(n, d)) : u & 16 ? m & 16 ? me(l, d, n, r, i, a, o, s, c) : ye(l, i, a, !0) : (u & 8 && p(n, ""), m & 16 && T(d, n, r, i, a, o, s, c));
	}, pe = (e, t, r, i, a, o, s, c, l) => {
		e ||= n, t ||= n;
		let u = e.length, d = t.length, f = Math.min(u, d), p = 0;
		for (; p < f; p++) {
			let n = t[p] = l ? oi(t[p]) : Q(t[p]);
			v(e[p], n, r, null, a, o, s, c, l);
		}
		u > d ? ye(e, a, o, !0, !1, f) : T(t, r, i, a, o, s, c, l, f);
	}, me = (e, t, r, i, a, o, s, c, l) => {
		let u = 0, d = t.length, f = e.length - 1, p = d - 1;
		for (; u <= f && u <= p;) {
			let n = e[u], i = t[u] = l ? oi(t[u]) : Q(t[u]);
			if (Zr(n, i)) v(n, i, r, null, a, o, s, c, l);
			else break;
			u++;
		}
		for (; u <= f && u <= p;) {
			let n = e[f], i = t[p] = l ? oi(t[p]) : Q(t[p]);
			if (Zr(n, i)) v(n, i, r, null, a, o, s, c, l);
			else break;
			f--, p--;
		}
		if (u > f) {
			if (u <= p) {
				let e = p + 1, n = e < d ? t[e].el : i;
				for (; u <= p;) v(null, t[u] = l ? oi(t[u]) : Q(t[u]), r, n, a, o, s, c, l), u++;
			}
		} else if (u > p) for (; u <= f;) O(e[u], a, o, !0), u++;
		else {
			let m = u, h = u, g = /* @__PURE__ */ new Map();
			for (u = h; u <= p; u++) {
				let e = t[u] = l ? oi(t[u]) : Q(t[u]);
				e.key != null && g.set(e.key, u);
			}
			let _, y = 0, b = p - h + 1, x = !1, S = 0, C = Array(b);
			for (u = 0; u < b; u++) C[u] = 0;
			for (u = m; u <= f; u++) {
				let n = e[u];
				if (y >= b) {
					O(n, a, o, !0);
					continue;
				}
				let i;
				if (n.key != null) i = g.get(n.key);
				else for (_ = h; _ <= p; _++) if (C[_ - h] === 0 && Zr(n, t[_])) {
					i = _;
					break;
				}
				i === void 0 ? O(n, a, o, !0) : (C[i - h] = u + 1, i >= S ? S = i : x = !0, v(n, t[i], r, null, a, o, s, c, l), y++);
			}
			let w = x ? Fr(C) : n;
			for (_ = w.length - 1, u = b - 1; u >= 0; u--) {
				let e = h + u, n = t[e], f = t[e + 1], p = e + 1 < d ? f.el || Rr(f) : i;
				C[u] === 0 ? v(null, n, r, p, a, o, s, c, l) : x && (_ < 0 || u !== w[_] ? he(n, r, p, 2) : _--);
			}
		}
	}, he = (e, t, n, r, i = null) => {
		let { el: a, type: c, transition: l, children: u, shapeFlag: d } = e;
		if (d & 6) {
			he(e.component.subTree, t, n, r);
			return;
		}
		if (d & 128) {
			e.suspense.move(t, n, r);
			return;
		}
		if (d & 64) {
			c.move(e, t, n, Ce);
			return;
		}
		if (c === K) {
			o(a, t, n);
			for (let e = 0; e < u.length; e++) he(u[e], t, n, r);
			o(e.anchor, t, n);
			return;
		}
		if (c === Hr) {
			S(e, t, n);
			return;
		}
		if (r !== 2 && d & 1 && l) {
			if (r === 0) l.persisted && !a[kn] ? o(a, t, n) : (l.beforeEnter(a), o(a, t, n), G(() => l.enter(a), i));
			else {
				let { leave: r, delayLeave: i, afterLeave: c } = l, u = () => {
					e.ctx.isUnmounted ? s(a) : o(a, t, n);
				}, d = () => {
					let e = a._isLeaving || !!a[kn];
					a._isLeaving && a[kn](!0), l.persisted && !e ? u() : r(a, () => {
						u(), c && c();
					});
				};
				i ? i(a, u, d) : d();
			}
		} else o(a, t, n);
	}, O = (e, t, n, r = !1, i = !1) => {
		let { type: a, props: o, ref: s, children: c, dynamicChildren: l, shapeFlag: u, patchFlag: d, dirs: f, cacheIndex: p, memo: m } = e;
		if (d === -2 && (i = !1), s != null && (Ue(), Ln(s, null, n, e, !0), We()), p != null && (t.renderCache[p] = void 0), u & 256) {
			t.ctx.deactivate(e);
			return;
		}
		let h = u & 1 && f, g = !zn(e), _;
		if (g && (_ = o && o.onVnodeBeforeUnmount) && $(_, t, e), u & 6) ve(e.component, n, r);
		else {
			if (u & 128) {
				e.suspense.unmount(n, r);
				return;
			}
			h && xn(e, null, t, "beforeUnmount"), u & 64 ? e.type.remove(e, t, n, Ce, r) : l && !l.hasOnce && (a !== K || d > 0 && d & 64) ? ye(l, t, n, !1, !0) : (a === K && d & 384 || !i && u & 16) && ye(c, t, n), r && ge(e);
		}
		let v = m != null && p == null;
		(g && (_ = o && o.onVnodeUnmounted) || h || v) && G(() => {
			_ && $(_, t, e), h && xn(e, null, t, "unmounted"), v && (e.el = null);
		}, n);
	}, ge = (e) => {
		let { type: t, el: n, anchor: r, transition: i } = e;
		if (t === K) {
			_e(n, r);
			return;
		}
		if (t === Hr) {
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
	}, _e = (e, t) => {
		let n;
		for (; e !== t;) n = h(e), s(e), e = n;
		s(t);
	}, ve = (e, t, n) => {
		let { bum: r, scope: i, job: a, subTree: o, um: s, m: c, a: l } = e;
		Lr(c), Lr(l), r && oe(r), i.stop(), a && (a.flags |= 8, O(o, e, t, n)), s && G(s, t), G(() => {
			e.isUnmounted = !0;
		}, t);
	}, ye = (e, t, n, r = !1, i = !1, a = 0) => {
		for (let o = a; o < e.length; o++) O(e[o], t, n, r, i);
	}, be = (e) => {
		if (e.shapeFlag & 6) return be(e.component.subTree);
		if (e.shapeFlag & 128) return e.suspense.next();
		let t = h(e.anchor || e.el), n = t && t[Dn];
		return n ? h(n) : t;
	}, xe = !1, Se = (e, t, n) => {
		let r;
		e == null ? t._vnode && (O(t._vnode, null, null, !0), r = t._vnode.component) : v(t._vnode || null, e, t, null, null, null, n), t._vnode = e, xe ||= (xe = !0, mn(r), hn(), !1);
	}, Ce = {
		p: v,
		um: O,
		m: he,
		r: ge,
		mt: se,
		mc: T,
		pc: fe,
		pbc: E,
		n: be,
		o: e
	}, k, we;
	return i && ([k, we] = i(Ce)), {
		render: Se,
		hydrate: k,
		createApp: $n(Se, k)
	};
}
function jr({ type: e, props: t }, n) {
	return n === "svg" && e === "foreignObject" || n === "mathml" && e === "annotation-xml" && t && t.encoding && t.encoding.includes("html") ? void 0 : n;
}
function Mr({ effect: e, job: t }, n) {
	n ? (e.flags |= 32, t.flags |= 4) : (e.flags &= -33, t.flags &= -5);
}
function Nr(e, t) {
	return (!e || e && !e.pendingBranch) && t && !t.persisted;
}
function Pr(e, t, n = !1) {
	let r = e.children, i = t.children;
	if (d(r) && d(i)) for (let e = 0; e < r.length; e++) {
		let t = r[e], a = i[e];
		a.shapeFlag & 1 && !a.dynamicChildren && ((a.patchFlag <= 0 || a.patchFlag === 32) && (a = i[e] = oi(i[e]), a.el = t.el), !n && a.patchFlag !== -2 && Pr(t, a)), a.type === Vr && (a.patchFlag === -1 && (a = i[e] = oi(a)), a.el = t.el), a.type === q && !a.el && (a.el = t.el);
	}
}
function Fr(e) {
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
function Ir(e) {
	let t = e.subTree.component;
	if (t) return t.asyncDep && !t.asyncResolved ? t : Ir(t);
}
function Lr(e) {
	if (e) for (let t = 0; t < e.length; t++) e[t].flags |= 8;
}
function Rr(e) {
	if (e.placeholder) return e.placeholder;
	let t = e.component;
	return t ? Rr(t.subTree) : null;
}
var zr = (e) => e.__isSuspense;
function Br(e, t) {
	t && t.pendingBranch ? d(e) ? t.effects.push(...e) : t.effects.push(e) : pn(e);
}
var K = /* @__PURE__ */ Symbol.for("v-fgt"), Vr = /* @__PURE__ */ Symbol.for("v-txt"), q = /* @__PURE__ */ Symbol.for("v-cmt"), Hr = /* @__PURE__ */ Symbol.for("v-stc"), Ur = [], J = null;
function Y(e = !1) {
	Ur.push(J = e ? null : []);
}
function Wr() {
	Ur.pop(), J = Ur[Ur.length - 1] || null;
}
var Gr = 1;
function Kr(e, t = !1) {
	Gr += e, e < 0 && J && t && (J.hasOnce = !0);
}
function qr(e) {
	return e.dynamicChildren = Gr > 0 ? J || n : null, Wr(), Gr > 0 && J && J.push(e), e;
}
function Jr(e, t, n, r, i, a) {
	return qr(X(e, t, n, r, i, a, !0));
}
function Yr(e, t, n, r, i) {
	return qr(Z(e, t, n, r, i, !0));
}
function Xr(e) {
	return e ? e.__v_isVNode === !0 : !1;
}
function Zr(e, t) {
	return e.type === t.type && e.key === t.key;
}
var Qr = ({ key: e }) => e ?? null, $r = ({ ref: e, ref_key: t, ref_for: n }) => (typeof e == "number" && (e = "" + e), e == null ? null : g(e) || /* @__PURE__ */ B(e) || h(e) ? {
	i: W,
	r: e,
	k: t,
	f: !!n
} : e);
function X(e, t = null, n = null, r = 0, i = null, a = e === K ? 0 : 1, o = !1, s = !1) {
	let c = {
		__v_isVNode: !0,
		__v_skip: !0,
		type: e,
		props: t,
		key: t && Qr(t),
		ref: t && $r(t),
		scopeId: vn,
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
		ctx: W
	};
	return s ? (si(c, n), a & 128 && e.normalize(c)) : n && (c.shapeFlag |= g(n) ? 8 : 16), Gr > 0 && !o && J && (c.patchFlag > 0 || a & 6) && c.patchFlag !== 32 && J.push(c), c;
}
var Z = ei;
function ei(e, t = null, n = null, r = 0, i = null, a = !1) {
	if ((!e || e === Gn) && (e = q), Xr(e)) {
		let r = ni(e, t, !0);
		return n && si(r, n), Gr > 0 && !a && J && (r.shapeFlag & 6 ? J[J.indexOf(e)] = r : J.push(r)), r.patchFlag = -2, r;
	}
	if (Di(e) && (e = e.__vccOpts), t) {
		t = ti(t);
		let { class: e, style: n } = t;
		e && !g(e) && (t.class = ge(e)), v(n) && (/* @__PURE__ */ Lt(n) && !d(n) && (n = s({}, n)), t.style = fe(n));
	}
	let o = g(e) ? 1 : zr(e) ? 128 : On(e) ? 64 : v(e) ? 4 : h(e) ? 2 : 0;
	return X(e, t, n, r, i, o, a, !0);
}
function ti(e) {
	return e ? /* @__PURE__ */ Lt(e) || mr(e) ? s({}, e) : e : null;
}
function ni(e, t, n = !1, r = !1) {
	let { props: i, ref: a, patchFlag: o, children: s, transition: c } = e, l = t ? ci(i || {}, t) : i, u = {
		__v_isVNode: !0,
		__v_skip: !0,
		type: e.type,
		props: l,
		key: l && Qr(l),
		ref: t && t.ref ? n && a ? d(a) ? a.concat($r(t)) : [a, $r(t)] : $r(t) : a,
		scopeId: e.scopeId,
		slotScopeIds: e.slotScopeIds,
		children: s,
		target: e.target,
		targetStart: e.targetStart,
		targetAnchor: e.targetAnchor,
		staticCount: e.staticCount,
		shapeFlag: e.shapeFlag,
		patchFlag: t && e.type !== K ? o === -1 ? 16 : o | 16 : o,
		dynamicProps: e.dynamicProps,
		dynamicChildren: e.dynamicChildren,
		appContext: e.appContext,
		dirs: e.dirs,
		transition: c,
		component: e.component,
		suspense: e.suspense,
		ssContent: e.ssContent && ni(e.ssContent),
		ssFallback: e.ssFallback && ni(e.ssFallback),
		placeholder: e.placeholder,
		el: e.el,
		anchor: e.anchor,
		ctx: e.ctx,
		ce: e.ce
	};
	return c && r && Mn(u, c.clone(u)), u;
}
function ri(e = " ", t = 0) {
	return Z(Vr, null, e, t);
}
function ii(e, t) {
	let n = Z(Hr, null, e);
	return n.staticCount = t, n;
}
function ai(e = "", t = !1) {
	return t ? (Y(), Yr(q, null, e)) : Z(q, null, e);
}
function Q(e) {
	return e == null || typeof e == "boolean" ? Z(q) : d(e) ? Z(K, null, e.slice()) : Xr(e) ? oi(e) : Z(Vr, null, String(e));
}
function oi(e) {
	return e.el === null && e.patchFlag !== -1 || e.memo ? e : ni(e);
}
function si(e, t) {
	let n = 0, { shapeFlag: r } = e;
	if (t == null) t = null;
	else if (d(t)) n = 16;
	else if (typeof t == "object") {
		if (r & 65) {
			let n = t.default;
			n && (n._c && (n._d = !1), si(e, n()), n._c && (n._d = !0));
			return;
		}
		{
			n = 32;
			let r = t._;
			!r && !mr(t) ? t._ctx = W : r === 3 && W && (W.slots._ === 1 ? t._ = 1 : (t._ = 2, e.patchFlag |= 1024));
		}
	} else if (h(t)) {
		if (r & 65) {
			si(e, { default: t });
			return;
		}
		t = {
			default: t,
			_ctx: W
		}, n = 32;
	} else t = String(t), r & 64 ? (n = 16, t = [ri(t)]) : n = 8;
	e.children = t, e.shapeFlag |= n;
}
function ci(...e) {
	let t = {};
	for (let n = 0; n < e.length; n++) {
		let r = e[n];
		for (let e in r) if (e === "class") t.class !== r.class && (t.class = ge([t.class, r.class]));
		else if (e === "style") t.style = fe([t.style, r.style]);
		else if (a(e)) {
			let n = t[e], i = r[e];
			i && n !== i && !(d(n) && n.includes(i)) ? t[e] = n ? [].concat(n, i) : i : i == null && n == null && !o(e) && (t[e] = i);
		} else e !== "" && (t[e] = r[e]);
	}
	return t;
}
function $(e, t, n, r = null) {
	V(e, t, 7, [n, r]);
}
var li = Zn(), ui = 0;
function di(e, n, r) {
	let i = e.type, a = (n ? n.appContext : e.appContext) || li, o = {
		uid: ui++,
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
		scope: new Ee(!0),
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
		propsOptions: yr(i, a),
		emitsOptions: rr(i, a),
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
	return o.ctx = { _: o }, o.root = n ? n.root : o, o.emit = nr.bind(null, o), e.ce && e.ce(o), o;
}
var fi = null, pi = () => fi || W, mi, hi;
{
	let e = de(), t = (t, n) => {
		let r;
		return (r = e[t]) || (r = e[t] = []), r.push(n), (e) => {
			r.length > 1 ? r.forEach((t) => t(e)) : r[0](e);
		};
	};
	mi = t("__VUE_INSTANCE_SETTERS__", (e) => fi = e), hi = t("__VUE_SSR_SETTERS__", (e) => yi = e);
}
var gi = (e) => {
	let t = fi;
	return mi(e), e.scope.on(), () => {
		e.scope.off(), mi(t);
	};
}, _i = () => {
	fi && fi.scope.off(), mi(null);
};
function vi(e) {
	return e.vnode.shapeFlag & 4;
}
var yi = !1;
function bi(e, t = !1, n = !1) {
	t && hi(t);
	let { props: r, children: i } = e.vnode, a = vi(e);
	hr(e, r, a, t), Dr(e, i, n || t);
	let o = a ? xi(e, t) : void 0;
	return t && hi(!1), o;
}
function xi(e, t) {
	let n = e.type;
	e.accessCache = /* @__PURE__ */ Object.create(null), e.proxy = new Proxy(e.ctx, Xn);
	let { setup: r } = n;
	if (r) {
		Ue();
		let n = e.setupContext = r.length > 1 ? Ti(e) : null, i = gi(e), a = en(r, e, 0, [e.props, n]), o = y(a);
		if (We(), i(), (o || e.sp) && !zn(e) && Pn(e), o) {
			if (a.then(_i, _i), t) return a.then((n) => {
				hi(!0);
				try {
					Si(e, n, t);
				} finally {
					hi(!1);
				}
			}).catch((t) => {
				tn(t, e, 0);
			});
			e.asyncDep = a;
		} else Si(e, a, t);
	} else Ci(e, t);
}
function Si(e, t, n) {
	h(t) ? e.type.__ssrInlineRender ? e.ssrRender = t : e.render = t : v(t) && (e.setupState = Gt(t)), Ci(e, n);
}
function Ci(e, t, n) {
	let i = e.type;
	e.render ||= i.render || r;
}
var wi = { get(e, t) {
	return N(e, "get", ""), e[t];
} };
function Ti(e) {
	return {
		attrs: new Proxy(e.attrs, wi),
		slots: e.slots,
		emit: e.emit,
		expose: (t) => {
			e.exposed = t || {};
		}
	};
}
function Ei(e) {
	return e.exposed ? e.exposeProxy ||= new Proxy(Gt(Rt(e.exposed)), {
		get(t, n) {
			if (n in t) return t[n];
			if (n in Jn) return Jn[n](e);
		},
		has(e, t) {
			return t in e || t in Jn;
		}
	}) : e.proxy;
}
function Di(e) {
	return h(e) && "__vccOpts" in e;
}
var Oi = (e, t) => /* @__PURE__ */ qt(e, t, yi), ki = "3.5.42", Ai = void 0, ji = typeof window < "u" && window.trustedTypes;
if (ji) try {
	Ai = /* @__PURE__ */ ji.createPolicy("vue", { createHTML: (e) => e });
} catch {}
var Mi = Ai ? (e) => Ai.createHTML(e) : (e) => e, Ni = "http://www.w3.org/2000/svg", Pi = "http://www.w3.org/1998/Math/MathML", Fi = typeof document < "u" ? document : null, Ii = Fi && /* @__PURE__ */ Fi.createElement("template"), Li = {
	insert: (e, t, n) => {
		t.insertBefore(e, n || null);
	},
	remove: (e) => {
		let t = e.parentNode;
		t && t.removeChild(e);
	},
	createElement: (e, t, n, r) => {
		let i = t === "svg" ? Fi.createElementNS(Ni, e) : t === "mathml" ? Fi.createElementNS(Pi, e) : n ? Fi.createElement(e, { is: n }) : Fi.createElement(e);
		return e === "select" && r && r.multiple != null && i.setAttribute("multiple", r.multiple), i;
	},
	createText: (e) => Fi.createTextNode(e),
	createComment: (e) => Fi.createComment(e),
	setText: (e, t) => {
		e.nodeValue = t;
	},
	setElementText: (e, t) => {
		e.textContent = t;
	},
	parentNode: (e) => e.parentNode,
	nextSibling: (e) => e.nextSibling,
	querySelector: (e) => Fi.querySelector(e),
	setScopeId(e, t) {
		e.setAttribute(t, "");
	},
	insertStaticContent(e, t, n, r, i, a) {
		let o = n ? n.previousSibling : t.lastChild;
		if (i && (i === a || i.nextSibling)) for (; t.insertBefore(i.cloneNode(!0), n), i !== a && (i = i.nextSibling););
		else {
			Ii.innerHTML = Mi(r === "svg" ? `<svg>${e}</svg>` : r === "mathml" ? `<math>${e}</math>` : e);
			let i = Ii.content;
			if (r === "svg" || r === "mathml") {
				let e = i.firstChild;
				for (; e.firstChild;) i.appendChild(e.firstChild);
				i.removeChild(e);
			}
			t.insertBefore(i, n);
		}
		return [o ? o.nextSibling : t.firstChild, n ? n.previousSibling : t.lastChild];
	}
}, Ri = /* @__PURE__ */ Symbol("_vtc");
function zi(e, t, n) {
	let r = e[Ri];
	r && (t = (t ? [t, ...r] : [...r]).join(" ")), t == null ? e.removeAttribute("class") : n ? e.setAttribute("class", t) : e.className = t;
}
var Bi = /* @__PURE__ */ Symbol("_vod"), Vi = /* @__PURE__ */ Symbol("_vsh"), Hi = /* @__PURE__ */ Symbol(""), Ui = /(?:^|;)\s*display\s*:/;
function Wi(e, t, n) {
	let r = e.style, i = g(n), a = !1;
	if (n && !i) {
		if (t) {
			if (g(t)) for (let e of t.split(";")) {
				let t = e.slice(0, e.indexOf(":")).trim();
				n[t] ?? Ki(r, t, "");
			}
			else for (let e in t) n[e] ?? Ki(r, e, "");
		}
		for (let i in n) {
			i === "display" && (a = !0);
			let o = n[i];
			o == null ? Ki(r, i, "") : Xi(e, i, !g(t) && t ? t[i] : void 0, o) || Ki(r, i, o);
		}
	} else if (i) {
		if (t !== n) {
			let e = r[Hi];
			e && (n += ";" + e), r.cssText = n, a = Ui.test(n);
		}
	} else t && e.removeAttribute("style");
	Bi in e && (e[Bi] = a ? r.display : "", e[Vi] && (r.display = "none"));
}
var Gi = /\s*!important$/;
function Ki(e, t, n) {
	if (d(n)) n.forEach((n) => Ki(e, t, n));
	else if (n ??= "", t.startsWith("--")) Gi.test(n) ? e.setProperty(t, n.replace(Gi, ""), "important") : e.setProperty(t, n);
	else {
		let r = Yi(e, t);
		Gi.test(n) ? e.setProperty(E(r), n.replace(Gi, ""), "important") : e[r] = n;
	}
}
var qi = [
	"Webkit",
	"Moz",
	"ms"
], Ji = {};
function Yi(e, t) {
	let n = Ji[t];
	if (n) return n;
	let r = T(t);
	if (r !== "filter" && r in e) return Ji[t] = r;
	r = ie(r);
	for (let n = 0; n < qi.length; n++) {
		let i = qi[n] + r;
		if (i in e) return Ji[t] = i;
	}
	return t;
}
function Xi(e, t, n, r) {
	return e.tagName === "TEXTAREA" && (t === "width" || t === "height") && g(r) && n === r;
}
var Zi = "http://www.w3.org/1999/xlink";
function Qi(e, t, n, r, i, a = ve(t)) {
	r && t.startsWith("xlink:") ? n == null ? e.removeAttributeNS(Zi, t.slice(6, t.length)) : e.setAttributeNS(Zi, t, n) : n == null || a && !ye(n) ? e.removeAttribute(t) : e.setAttribute(t, a ? "" : _(n) ? String(n) : n);
}
function $i(e, t, n, r, i) {
	if (t === "innerHTML" || t === "textContent") {
		n != null && (e[t] = t === "innerHTML" ? Mi(n) : n);
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
		r === "boolean" ? n = ye(n) : n == null && r === "string" ? (n = "", o = !0) : r === "number" && (n = 0, o = !0);
	}
	try {
		e[t] = n;
	} catch {}
	o && e.removeAttribute(i || t);
}
function ea(e, t, n, r) {
	e.addEventListener(t, n, r);
}
function ta(e, t, n, r) {
	e.removeEventListener(t, n, r);
}
var na = /* @__PURE__ */ Symbol("_vei");
function ra(e, t, n, r, i = null) {
	let a = e[na] || (e[na] = {}), o = a[t];
	if (r && o) o.value = r;
	else {
		let [n, s] = oa(t);
		r ? ea(e, n, a[t] = ua(r, i), s) : o && (ta(e, n, o, s), a[t] = void 0);
	}
}
var ia = /(Once|Passive|Capture)$/, aa = /^on:?(?:Once|Passive|Capture)$/;
function oa(e) {
	let t, n;
	for (; (n = e.match(ia)) && !aa.test(e);) t ||= {}, e = e.slice(0, e.length - n[1].length), t[n[1].toLowerCase()] = !0;
	return [e[2] === ":" ? e.slice(3) : E(e.slice(2)), t];
}
var sa = 0, ca = /* @__PURE__ */ Promise.resolve(), la = () => sa ||= (ca.then(() => sa = 0), Date.now());
function ua(e, t) {
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
				e && V(e, t, 5, a);
			}
		} else V(r, t, 5, [e]);
	};
	return n.value = e, n.attached = la(), n;
}
var da = (e) => e.charCodeAt(0) === 111 && e.charCodeAt(1) === 110 && e.charCodeAt(2) > 96 && e.charCodeAt(2) < 123, fa = (e, t, n, r, i, s) => {
	let c = i === "svg";
	t === "class" ? zi(e, r, c) : t === "style" ? Wi(e, n, r) : a(t) ? o(t) || ra(e, t, n, r, s) : (t[0] === "." ? (t = t.slice(1), 1) : t[0] === "^" ? (t = t.slice(1), 0) : pa(e, t, r, c)) ? ($i(e, t, r), !e.tagName.includes("-") && (t === "value" || t === "checked" || t === "selected") && Qi(e, t, r, c, s, t !== "value")) : e._isVueCE && (ma(e, t) || e._def.__asyncLoader && (/[A-Z]/.test(t) || !g(r))) ? $i(e, T(t), r, s, t) : (t === "true-value" ? e._trueValue = r : t === "false-value" && (e._falseValue = r), Qi(e, t, r, c));
};
function pa(e, t, n, r) {
	if (r) return !!(t === "innerHTML" || t === "textContent" || t in e && da(t) && h(n));
	if (t === "spellcheck" || t === "draggable" || t === "translate" || t === "autocorrect" || t === "sandbox" && e.tagName === "IFRAME" || t === "form" || t === "list" && e.tagName === "INPUT" || t === "type" && e.tagName === "TEXTAREA") return !1;
	if (t === "width" || t === "height") {
		let t = e.tagName;
		if (t === "IMG" || t === "VIDEO" || t === "CANVAS" || t === "SOURCE") return !1;
	}
	return da(t) && g(n) ? !1 : t in e;
}
function ma(e, t) {
	let n = e._def.props;
	if (!n) return !1;
	let r = T(t);
	return Array.isArray(n) ? n.some((e) => T(e) === r) : Object.keys(n).some((e) => T(e) === r);
}
var ha = {};
// @__NO_SIDE_EFFECTS__
function ga(e, t, n) {
	let r = /* @__PURE__ */ Nn(e, t);
	C(r) && (r = s({}, r, t));
	class i extends va {
		constructor(e) {
			super(r, e, n);
		}
	}
	return i.def = r, i;
}
var _a = typeof HTMLElement < "u" ? HTMLElement : class {}, va = class e extends _a {
	constructor(e, t = {}, n = wa) {
		super(), this._def = e, this._props = t, this._createApp = n, this._isVueCE = !0, this._instance = null, this._app = null, this._nonce = this._def.nonce, this._connected = !1, this._resolved = !1, this._patching = !1, this._dirty = !1, this._numberProps = null, this._styleChildren = /* @__PURE__ */ new WeakSet(), this._styleAnchors = /* @__PURE__ */ new WeakMap(), this._ob = null, this.shadowRoot && n !== wa ? this._root = this.shadowRoot : e.shadowRoot === !1 ? this._root = this : (this.attachShadow(s({}, e.shadowRootOptions, { mode: "open" })), this._root = this.shadowRoot);
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
		this._connected = !1, ln(() => {
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
				(t === Number || t && t.type === Number) && (e in this._props && (this._props[e] = le(this._props[e])), (i ||= /* @__PURE__ */ Object.create(null))[T(e)] = !0);
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
		if (t) for (let e in t) u(this, e) || Object.defineProperty(this, e, { get: () => Ut(t[e]) });
	}
	_resolveProps(e) {
		let { props: t } = e, n = d(t) ? t : Object.keys(t || {});
		for (let e of Object.keys(this)) e[0] !== "_" && n.includes(e) && this._setProp(e, this[e]);
		for (let e of n.map(T)) Object.defineProperty(this, e, {
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
		let t = this.hasAttribute(e), n = t ? this.getAttribute(e) : ha, r = T(e);
		t && this._numberProps && this._numberProps[r] && (n = le(n)), this._setProp(r, n, !1, !0);
	}
	_getProp(e) {
		return this._props[e];
	}
	_setProp(e, t, n = !0, r = !1) {
		if (t !== this._props[e] && (this._dirty = !0, t === ha ? delete this._props[e] : (this._props[e] = t, e === "key" && this._app && (this._app._ceVNode.key = t)), r && this._instance && this._update(), n)) {
			let n = this._ob;
			n && (this._processMutations(n.takeRecords()), n.disconnect()), t === !0 ? this.setAttribute(E(e), "") : typeof t == "string" || typeof t == "number" ? this.setAttribute(E(e), t + "") : t || this.removeAttribute(E(e)), n && n.observe(this, { attributes: !0 });
		}
	}
	_update() {
		let e = this._createVNode();
		this._app && (e.appContext = this._app._context), Ca(e, this._root);
	}
	_createVNode() {
		let e = {};
		this.shadowRoot || (e.onVnodeMounted = e.onVnodeUpdated = this._renderSlots.bind(this));
		let t = Z(this._def, s(e, this._props));
		return this._instance || (t.ce = (e) => {
			this._instance = e, e.ce = this, e.isCE = !0;
			let t = (e, t) => {
				this.dispatchEvent(new CustomEvent(e, C(t[0]) ? s({ detail: t }, t[0]) : { detail: t }));
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
function ya(e) {
	let t = pi();
	return t && t.ce || null;
}
var ba = /* @__PURE__ */ s({ patchProp: fa }, Li), xa;
function Sa() {
	return xa ||= kr(ba);
}
var Ca = ((...e) => {
	Sa().render(...e);
}), wa = ((...e) => {
	let t = Sa().createApp(...e), { mount: n } = t;
	return t.mount = (e) => {
		let r = Ea(e);
		if (!r) return;
		let i = t._component;
		!h(i) && !i.render && !i.template && (i.template = r.innerHTML), r.nodeType === 1 && (r.textContent = "");
		let a = n(r, !1, Ta(r));
		return r instanceof Element && (r.removeAttribute("v-cloak"), r.setAttribute("data-v-app", "")), a;
	}, t;
});
function Ta(e) {
	if (e instanceof SVGElement) return "svg";
	if (typeof MathMLElement == "function" && e instanceof MathMLElement) return "mathml";
}
function Ea(e) {
	return g(e) ? document.querySelector(e) : e;
}
//#endregion
//#region src/tabs.ts
var Da = [
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
function Oa(e, t) {
	let n = e.split(/[?#]/, 1)[0].replace(/\/+$/, "");
	return (n.startsWith(`${t}/`) ? n.slice(t.length) : n === t ? "" : n).replace(/^\//, "") || Da[0].path;
}
var ka = {
	de: {
		navigation: "Dashboard-Bereiche",
		menu: "Seitenleiste öffnen",
		preview: "Vorschau",
		introduction: "Das neue Dashboard entsteht parallel zu Ihrer bisherigen Ansicht.",
		introductionStandalone: "Das neue SAX-Power-Dashboard entsteht hier.",
		existing: "Bestehendes Dashboard öffnen",
		preparation: "Dieser Bereich wird vorbereitet",
		description: "Die Anzeigen und Einstellungen finden Sie weiterhin im bestehenden SAX-Power-Dashboard. Sie werden Schritt für Schritt auch hier verfügbar.",
		descriptionStandalone: "Die Anzeigen und Einstellungen dieses Bereichs sind noch in Vorbereitung. Sie werden Schritt für Schritt hier verfügbar.",
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
		introduction: "The new dashboard is being built alongside your existing dashboard.",
		introductionStandalone: "The new SAX Power dashboard is taking shape here.",
		existing: "Open existing dashboard",
		preparation: "This section is being prepared",
		description: "Your displays and settings remain available in the existing SAX Power dashboard. They will gradually become available here too.",
		descriptionStandalone: "The displays and settings for this section are being prepared. They will gradually become available here.",
		loading: "Loading Home Assistant …",
		missingEntry: "No SAX Power device is assigned to this dashboard yet. Please reload the integration.",
		notFound: "Section not found",
		notFoundDescription: "This dashboard section is unavailable. Choose one of the sections above.",
		returnToOverview: "Back to overview"
	}
}, Aa = ["lang"], ja = { class: "header" }, Ma = ["aria-label"], Na = { class: "preview" }, Pa = ["aria-label"], Fa = [
	"href",
	"aria-current",
	"onClick"
], Ia = { class: "introduction" }, La = {
	key: 0,
	class: "existing-link",
	href: "/sax-power"
}, Ra = {
	class: "section",
	"aria-labelledby": "section-heading"
}, za = {
	key: 0,
	class: "status",
	role: "status"
}, Ba = {
	key: 1,
	class: "status",
	role: "status"
}, Va = {
	key: 2,
	class: "placeholder"
}, Ha = {
	key: 3,
	class: "status"
}, Ua = ["href"], Wa = /* @__PURE__ */ ga(/* @__PURE__ */ ((e, t) => {
	let n = e.__vccOpts || e;
	for (let [e, r] of t) n[e] = r;
	return n;
})(/* @__PURE__ */ Nn({
	__name: "Panel.ce",
	props: {
		hass: { type: Object },
		narrow: { type: Boolean },
		panel: { type: Object },
		route: { type: Object }
	},
	setup(e) {
		let t = e, n = ya(), r = Oi(() => t.hass?.language.toLowerCase().startsWith("de") ? "de" : "en"), i = Oi(() => ka[r.value]), a = Oi(() => !!t.hass?.panels?.["sax-power"]), o = Oi(() => !t.hass?.kioskMode && (t.narrow || t.hass?.dockedSidebar === "always_hidden")), s = Oi(() => `/${t.panel?.url_path || "sax-power-vue"}`), c = /* @__PURE__ */ Bt(t.route?.path ?? window.location.pathname), l = Oi(() => Oa(c.value, s.value)), u = Oi(() => Da.find((e) => e.path === l.value)), d = /* @__PURE__ */ Bt();
		Tn(() => t.route?.path, (e) => {
			e !== void 0 && (c.value = e);
		});
		function f() {
			c.value = window.location.pathname;
		}
		Un(() => {
			window.addEventListener("popstate", f), window.addEventListener("location-changed", f);
		}), Wn(() => {
			window.removeEventListener("popstate", f), window.removeEventListener("location-changed", f);
		});
		function p(e, t) {
			e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || (e.preventDefault(), window.location.pathname !== t && (window.history.pushState(null, "", t), window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: !1 } }))), f(), ln(() => d.value?.focus()));
		}
		function m() {
			n?.dispatchEvent(new CustomEvent("hass-toggle-menu", {
				bubbles: !0,
				composed: !0
			}));
		}
		return (t, n) => (Y(), Jr("div", {
			class: ge(["dashboard", { narrow: e.narrow }]),
			lang: r.value
		}, [
			X("header", ja, [
				o.value ? (Y(), Jr("button", {
					key: 0,
					class: "menu-button",
					type: "button",
					"aria-label": i.value.menu,
					onClick: m
				}, [...n[1] ||= [X("svg", {
					viewBox: "0 0 24 24",
					"aria-hidden": "true"
				}, [X("path", { d: "M4 6h16M4 12h16M4 18h16" })], -1)]], 8, Ma)) : ai("", !0),
				n[2] ||= ii("<div class=\"brand\"><svg class=\"brand-icon\" viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path d=\"M9 3h6M8 5h8a1 1 0 0 1 1 1v14H7V6a1 1 0 0 1 1-1Z\"></path><path d=\"m13 8-3 5h4l-3 5\"></path></svg><span>SAX Power <span class=\"variant\">(Vue)</span></span></div>", 1),
				X("span", Na, k(i.value.preview), 1)
			]),
			X("nav", {
				class: "navigation",
				"aria-label": i.value.navigation
			}, [(Y(!0), Jr(K, null, Kn(Ut(Da), (e) => (Y(), Jr("a", {
				key: e.path,
				href: `${s.value}/${e.path}`,
				"aria-current": l.value === e.path ? "page" : void 0,
				onClick: (t) => p(t, `${s.value}/${e.path}`)
			}, k(e[r.value]), 9, Fa))), 128))], 8, Pa),
			X("main", null, [X("div", Ia, [X("p", null, k(a.value ? i.value.introduction : i.value.introductionStandalone), 1), a.value ? (Y(), Jr("a", La, k(i.value.existing), 1)) : ai("", !0)]), X("section", Ra, [X("h1", {
				id: "section-heading",
				ref_key: "heading",
				ref: d,
				tabindex: "-1"
			}, k(u.value?.[r.value] ?? i.value.notFound), 513), e.hass ? e.panel?.config?.entry_id ? u.value ? (Y(), Jr("div", Va, [
				n[3] ||= X("svg", {
					class: "placeholder-icon",
					viewBox: "0 0 48 48",
					"aria-hidden": "true"
				}, [X("rect", {
					x: "8",
					y: "9",
					width: "32",
					height: "30",
					rx: "4"
				}), X("path", { d: "M8 18h32M19 18v21M24 26h10M24 32h7" })], -1),
				X("h2", null, k(i.value.preparation), 1),
				X("p", null, k(a.value ? i.value.description : i.value.descriptionStandalone), 1)
			])) : (Y(), Jr("div", Ha, [X("p", null, k(i.value.notFoundDescription), 1), X("a", {
				href: `${s.value}/allgemein`,
				onClick: n[0] ||= (e) => p(e, `${s.value}/allgemein`)
			}, k(i.value.returnToOverview), 9, Ua)])) : (Y(), Jr("p", Ba, k(i.value.missingEntry), 1)) : (Y(), Jr("p", za, k(i.value.loading), 1))])])
		], 10, Aa));
	}
}), [["styles", [":host{height:100%;color:var(--primary-text-color,#212121);background:var(--primary-background-color,#fafafa);font-family:var(--paper-font-body1_-_font-family,Roboto, sans-serif);font-size:14px;display:block}*{box-sizing:border-box}.dashboard{min-height:100%}.header{background:var(--app-header-background-color,var(--primary-color,#03a9f4));min-height:64px;color:var(--app-header-text-color,#fff);align-items:center;gap:14px;padding:8px 24px;display:flex}.brand{align-items:center;gap:10px;font-size:20px;font-weight:500;display:flex}.variant{font-size:16px;font-weight:400}svg{fill:none;stroke:currentColor;stroke-width:1.7px;stroke-linecap:round;stroke-linejoin:round}.brand-icon{width:30px;height:30px}.preview{border:1px solid;border-radius:12px;margin-left:auto;padding:3px 10px;font-size:12px}.menu-button{width:44px;height:44px;color:inherit;cursor:pointer;background:0 0;border:0;border-radius:50%;place-items:center;margin-left:-10px;display:grid}.menu-button svg{width:24px;height:24px}.navigation{border-bottom:1px solid var(--divider-color,#e0e0e0);background:var(--card-background-color,#fff);padding:0 16px;display:flex;overflow-x:auto}.navigation a{min-height:56px;color:var(--secondary-text-color,#666);white-space:nowrap;border-bottom:3px solid #0000;align-items:center;padding:12px 16px;text-decoration:none;display:flex}.navigation a[aria-current=page]{border-color:var(--primary-color,#03a9f4);color:var(--primary-text-color,#212121);font-weight:600}a{color:var(--primary-text-color,#212121);text-underline-offset:3px}a:focus-visible,button:focus-visible{outline-offset:-4px;outline:2px solid}main{max-width:1120px;margin:0 auto;padding:28px 24px 48px}.introduction{flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:8px 24px;margin-bottom:24px;line-height:1.6;display:flex}.introduction p{color:var(--secondary-text-color,#666);margin:0}.existing-link{align-items:center;min-height:44px;display:inline-flex}.section{overflow-wrap:anywhere;border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));box-shadow:var(--ha-card-box-shadow,none);padding:28px}h1{margin:0;font-size:24px;font-weight:500;line-height:1.35}h1:focus{outline:none}.placeholder{text-align:center;flex-direction:column;align-items:center;padding:64px 16px;display:flex}.placeholder-icon{width:52px;height:52px;color:var(--secondary-text-color,#666);margin-bottom:16px}h2{margin:0 0 12px;font-size:18px;font-weight:500;line-height:1.5}.placeholder p{max-width:480px;color:var(--secondary-text-color,#666);margin:0;line-height:1.7}.status{margin-top:24px;line-height:1.7}.narrow .header{padding-left:16px;padding-right:16px}.narrow main{padding:16px 12px 32px}@media (max-width:600px){.header{gap:8px;padding:8px 16px}.brand{gap:6px;font-size:18px}.brand-icon{display:none}.navigation{padding:0 4px}main{padding:16px 12px 32px}.introduction{gap:0;margin-bottom:16px}.section{padding:20px}h1{font-size:22px}.placeholder{padding:40px 0}}"]]]));
customElements.get("sax-power-vue-panel") || customElements.define("sax-power-vue-panel", Wa);
//#endregion
export { Wa as SaxPowerVuePanel };
