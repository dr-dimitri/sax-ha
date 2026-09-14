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
}, E = /-\w/g, D = ee((e) => e.replace(E, (e) => e.slice(1).toUpperCase())), te = /\B([A-Z])/g, O = ee((e) => e.replace(te, "-$1").toLowerCase()), ne = ee((e) => e.charAt(0).toUpperCase() + e.slice(1)), re = ee((e) => e ? `on${ne(e)}` : ""), k = (e, t) => !Object.is(e, t), A = (e, ...t) => {
	for (let n = 0; n < e.length; n++) e[n](...t);
}, j = (e, t, n, r = !1) => {
	Object.defineProperty(e, t, {
		configurable: !0,
		enumerable: !1,
		writable: r,
		value: n
	});
}, ie = (e) => {
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
			let r = e[n], i = g(r) ? N(r) : M(r);
			if (i) for (let e in i) t[e] = i[e];
		}
		return t;
	}
	if (g(e) || v(e)) return e;
}
var ce = /;(?![^(]*\))/g, le = /:([^]+)/, ue = /\/\*[^]*?\*\//g;
function N(e) {
	let t = {};
	return e.replace(ue, "").split(ce).forEach((e) => {
		if (e) {
			let n = e.split(le);
			n.length > 1 && (t[n[0].trim()] = n[1].trim());
		}
	}), t;
}
function de(e) {
	let t = "";
	if (g(e)) t = e;
	else if (d(e)) for (let n = 0; n < e.length; n++) {
		let r = de(e[n]);
		r && (t += r + " ");
	}
	else if (v(e)) for (let n in e) e[n] && (t += n + " ");
	return t.trim();
}
var fe = "itemscope,allowfullscreen,formnovalidate,ismap,nomodule,novalidate,readonly", P = /* @__PURE__ */ e(fe);
fe + "";
function F(e) {
	return !!e || e === "";
}
function pe(e, t) {
	if (e.length !== t.length) return !1;
	let n = !0;
	for (let r = 0; n && r < e.length; r++) n = I(e[r], t[r]);
	return n;
}
function me(e, t) {
	if (e.size !== t.size) return !1;
	let n = Array.from(t), r = new Uint8Array(n.length);
	for (let t of e) {
		let e = -1;
		for (let i = 0; i < n.length; i++) if (!r[i] && I(t, n[i])) {
			e = i;
			break;
		}
		if (e < 0) return !1;
		r[e] = 1;
	}
	return !0;
}
function I(e, t) {
	if (e === t) return !0;
	let n = m(e), r = m(t);
	if (n || r) return n && r ? e.getTime() === t.getTime() : !1;
	if (n = _(e), r = _(t), n || r) return e === t;
	if (n = d(e), r = d(t), n || r) return n && r ? pe(e, t) : !1;
	if (n = v(e), r = v(t), n || r) {
		if (!n || !r) return !1;
		if (n = f(e), r = f(t), n || r || (n = p(e), r = p(t), n || r)) return n && r ? me(e, t) : !1;
		if (Object.keys(e).length !== Object.keys(t).length) return !1;
		for (let n in e) {
			let r = e.hasOwnProperty(n), i = t.hasOwnProperty(n);
			if (r && !i || !r && i || !I(e[n], t[n])) return !1;
		}
	}
	return String(e) === String(t);
}
function he(e, t) {
	return e.findIndex((e) => I(e, t));
}
var ge = (e) => !!(e && e.__v_isRef === !0), L = (e) => g(e) ? e : e == null ? "" : d(e) || v(e) && (e.toString === b || !h(e.toString)) ? ge(e) ? L(e.value) : JSON.stringify(e, _e, 2) : String(e), _e = (e, t) => ge(t) ? _e(e, t.value) : f(t) ? { [`Map(${t.size})`]: [...t.entries()].reduce((e, [t, n], r) => (e[ve(t, r) + " =>"] = n, e), {}) } : p(t) ? { [`Set(${t.size})`]: [...t.values()].map((e) => ve(e)) } : _(t) ? ve(t) : v(t) && !d(t) && !C(t) ? String(t) : t, ve = (e, t = "") => _(e) ? `Symbol(${e.description ?? t})` : e, R, ye = class {
	constructor(e = !1) {
		this.detached = e, this._active = !0, this._on = 0, this.effects = [], this.cleanups = [], this._isPaused = !1, this._warnOnRun = !0, this.__v_skip = !0, !e && R && (R.active ? (this.parent = R, this.index = (R.scopes || (R.scopes = [])).push(this) - 1) : (this._active = !1, this._warnOnRun = !1));
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
			let t = R;
			try {
				return R = this, e();
			} finally {
				R = t;
			}
		}
	}
	on() {
		++this._on === 1 && (this.prevScope = R, R = this);
	}
	off() {
		if (this._on > 0 && --this._on === 0) {
			if (R === this) R = this.prevScope;
			else {
				let e = R;
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
function be() {
	return R;
}
function xe(e, t = !1) {
	R && R.cleanups.push(e);
}
var z, Se = /* @__PURE__ */ new WeakSet(), Ce = class {
	constructor(e) {
		this.fn = e, this.deps = void 0, this.depsTail = void 0, this.flags = 5, this.next = void 0, this.cleanup = void 0, this.scheduler = void 0, R && (R.active ? R.effects.push(this) : this.flags &= -2);
	}
	pause() {
		this.flags |= 64;
	}
	resume() {
		this.flags & 64 && (this.flags &= -65, Se.has(this) && (Se.delete(this), this.trigger()));
	}
	notify() {
		this.flags & 2 && !(this.flags & 32) || this.flags & 8 || De(this);
	}
	run() {
		if (!(this.flags & 1)) return this.fn();
		this.flags |= 2, Be(this), Ae(this);
		let e = z, t = Ie;
		z = this, Ie = !0;
		try {
			return this.fn();
		} finally {
			je(this), z = e, Ie = t, this.flags &= -3;
		}
	}
	stop() {
		if (this.flags & 1) {
			for (let e = this.deps; e; e = e.nextDep) Pe(e);
			this.deps = this.depsTail = void 0, Be(this), this.onStop && this.onStop(), this.flags &= -2;
		}
	}
	trigger() {
		this.flags & 64 ? Se.add(this) : this.scheduler ? this.scheduler() : this.runIfDirty();
	}
	runIfDirty() {
		Me(this) && this.run();
	}
	get dirty() {
		return Me(this);
	}
}, we = 0, Te, Ee;
function De(e, t = !1) {
	if (e.flags |= 8, t) {
		e.next = Ee, Ee = e;
		return;
	}
	e.next = Te, Te = e;
}
function Oe() {
	we++;
}
function ke() {
	if (--we > 0) return;
	if (Ee) {
		let e = Ee;
		for (Ee = void 0; e;) {
			let t = e.next;
			e.next = void 0, e.flags &= -9, e = t;
		}
	}
	let e;
	for (; Te;) {
		let t = Te;
		for (Te = void 0; t;) {
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
function Ae(e) {
	for (let t = e.deps; t; t = t.nextDep) t.version = -1, t.prevActiveLink = t.dep.activeLink, t.dep.activeLink = t;
}
function je(e) {
	let t, n = e.depsTail, r = n;
	for (; r;) {
		let e = r.prevDep;
		r.version === -1 ? (r === n && (n = e), Pe(r), Fe(r)) : t = r, r.dep.activeLink = r.prevActiveLink, r.prevActiveLink = void 0, r = e;
	}
	e.deps = t, e.depsTail = n;
}
function Me(e) {
	for (let t = e.deps; t; t = t.nextDep) if (t.dep.version !== t.version || t.dep.computed && (Ne(t.dep.computed) || t.dep.version !== t.version)) return !0;
	return !!e._dirty;
}
function Ne(e) {
	if (e.flags & 4 && !(e.flags & 16) || (e.flags &= -17, e.globalVersion === Ve) || (e.globalVersion = Ve, !e.isSSR && e.flags & 128 && (!e.deps && !e._dirty || !Me(e)))) return;
	e.flags |= 2;
	let t = e.dep, n = z, r = Ie;
	z = e, Ie = !0;
	try {
		Ae(e);
		let n = e.fn(e._value);
		(t.version === 0 || k(n, e._value)) && (e.flags |= 128, e._value = n, t.version++);
	} catch (e) {
		throw t.version++, e;
	} finally {
		z = n, Ie = r, je(e), e.flags &= -3;
	}
}
function Pe(e, t = !1) {
	let { dep: n, prevSub: r, nextSub: i } = e;
	if (r && (r.nextSub = i, e.prevSub = void 0), i && (i.prevSub = r, e.nextSub = void 0), n.subs === e && (n.subs = r, !r && n.computed)) {
		n.computed.flags &= -5;
		for (let e = n.computed.deps; e; e = e.nextDep) Pe(e, !0);
	}
	!t && !--n.sc && n.map && n.map.delete(n.key);
}
function Fe(e) {
	let { prevDep: t, nextDep: n } = e;
	t && (t.nextDep = n, e.prevDep = void 0), n && (n.prevDep = t, e.nextDep = void 0);
}
var Ie = !0, Le = [];
function Re() {
	Le.push(Ie), Ie = !1;
}
function ze() {
	let e = Le.pop();
	Ie = e === void 0 || e;
}
function Be(e) {
	let { cleanup: t } = e;
	if (e.cleanup = void 0, t) {
		let e = z;
		z = void 0;
		try {
			t();
		} finally {
			z = e;
		}
	}
}
var Ve = 0, He = class {
	constructor(e, t) {
		this.sub = e, this.dep = t, this.version = t.version, this.nextDep = this.prevDep = this.nextSub = this.prevSub = this.prevActiveLink = void 0;
	}
}, Ue = class {
	constructor(e) {
		this.computed = e, this.version = 0, this.activeLink = void 0, this.subs = void 0, this.map = void 0, this.key = void 0, this.sc = 0, this.__v_skip = !0;
	}
	track(e) {
		if (!z || !Ie || z === this.computed) return;
		let t = this.activeLink;
		if (t === void 0 || t.sub !== z) t = this.activeLink = new He(z, this), z.deps ? (t.prevDep = z.depsTail, z.depsTail.nextDep = t, z.depsTail = t) : z.deps = z.depsTail = t, We(t);
		else if (t.version === -1 && (t.version = this.version, t.nextDep)) {
			let e = t.nextDep;
			e.prevDep = t.prevDep, t.prevDep && (t.prevDep.nextDep = e), t.prevDep = z.depsTail, t.nextDep = void 0, z.depsTail.nextDep = t, z.depsTail = t, z.deps === t && (z.deps = e);
		}
		return t;
	}
	trigger(e) {
		this.version++, Ve++, this.notify(e);
	}
	notify(e) {
		Oe();
		try {
			for (let e = this.subs; e; e = e.prevSub) e.sub.notify() && e.sub.dep.notify();
		} finally {
			ke();
		}
	}
};
function We(e) {
	if (e.dep.sc++, e.sub.flags & 4) {
		let t = e.dep.computed;
		if (t && !e.dep.subs) {
			t.flags |= 20;
			for (let e = t.deps; e; e = e.nextDep) We(e);
		}
		let n = e.dep.subs;
		n !== e && (e.prevSub = n, n && (n.nextSub = e)), e.dep.subs = e;
	}
}
var Ge = /* @__PURE__ */ new WeakMap(), Ke = /* @__PURE__ */ Symbol(""), qe = /* @__PURE__ */ Symbol(""), Je = /* @__PURE__ */ Symbol("");
function Ye(e, t, n) {
	if (Ie && z) {
		let t = Ge.get(e);
		t || Ge.set(e, t = /* @__PURE__ */ new Map());
		let r = t.get(n);
		r || (t.set(n, r = new Ue()), r.map = t, r.key = n), r.track();
	}
}
function Xe(e, t, n, r, i, a) {
	let o = Ge.get(e);
	if (!o) {
		Ve++;
		return;
	}
	let s = (e) => {
		e && e.trigger();
	};
	if (Oe(), t === "clear") o.forEach(s);
	else {
		let i = d(e), a = i && w(n);
		if (i && n === "length") {
			let e = Number(r);
			o.forEach((t, n) => {
				(n === "length" || n === Je || !_(n) && n >= e) && s(t);
			});
		} else switch ((n !== void 0 || o.has(void 0)) && s(o.get(n)), a && s(o.get(Je)), t) {
			case "add":
				i ? a && s(o.get("length")) : (s(o.get(Ke)), f(e) && s(o.get(qe)));
				break;
			case "delete":
				i || (s(o.get(Ke)), f(e) && s(o.get(qe)));
				break;
			case "set": f(e) && s(o.get(Ke));
		}
	}
	ke();
}
function Ze(e) {
	let t = /* @__PURE__ */ B(e);
	return t === e ? t : (Ye(t, "iterate", Je), /* @__PURE__ */ It(e) ? t : t.map(zt));
}
function Qe(e) {
	return Ye(e = /* @__PURE__ */ B(e), "iterate", Je), e;
}
function $e(e, t) {
	return /* @__PURE__ */ Ft(e) ? Bt(/* @__PURE__ */ Pt(e) ? zt(t) : t) : zt(t);
}
var et = {
	__proto__: null,
	[Symbol.iterator]() {
		return tt(this, Symbol.iterator, (e) => $e(this, e));
	},
	concat(...e) {
		return Ze(this).concat(...e.map((e) => d(e) ? Ze(e) : e));
	},
	entries() {
		return tt(this, "entries", (e) => (e[1] = $e(this, e[1]), e));
	},
	every(e, t) {
		return rt(this, "every", e, t, void 0, arguments);
	},
	filter(e, t) {
		return rt(this, "filter", e, t, (e) => e.map((e) => $e(this, e)), arguments);
	},
	find(e, t) {
		return rt(this, "find", e, t, (e) => $e(this, e), arguments);
	},
	findIndex(e, t) {
		return rt(this, "findIndex", e, t, void 0, arguments);
	},
	findLast(e, t) {
		return rt(this, "findLast", e, t, (e) => $e(this, e), arguments);
	},
	findLastIndex(e, t) {
		return rt(this, "findLastIndex", e, t, void 0, arguments);
	},
	forEach(e, t) {
		return rt(this, "forEach", e, t, void 0, arguments);
	},
	includes(...e) {
		return at(this, "includes", e);
	},
	indexOf(...e) {
		return at(this, "indexOf", e);
	},
	join(e) {
		return Ze(this).join(e);
	},
	lastIndexOf(...e) {
		return at(this, "lastIndexOf", e);
	},
	map(e, t) {
		return rt(this, "map", e, t, void 0, arguments);
	},
	pop() {
		return ot(this, "pop");
	},
	push(...e) {
		return ot(this, "push", e);
	},
	reduce(e, ...t) {
		return it(this, "reduce", e, t);
	},
	reduceRight(e, ...t) {
		return it(this, "reduceRight", e, t);
	},
	shift() {
		return ot(this, "shift");
	},
	some(e, t) {
		return rt(this, "some", e, t, void 0, arguments);
	},
	splice(...e) {
		return ot(this, "splice", e);
	},
	toReversed() {
		return Ze(this).toReversed();
	},
	toSorted(e) {
		return Ze(this).toSorted(e);
	},
	toSpliced(...e) {
		return Ze(this).toSpliced(...e);
	},
	unshift(...e) {
		return ot(this, "unshift", e);
	},
	values() {
		return tt(this, "values", (e) => $e(this, e));
	}
};
function tt(e, t, n) {
	let r = Qe(e), i = r[t]();
	return r !== e && !/* @__PURE__ */ It(e) && (i._next = i.next, i.next = () => {
		let e = i._next();
		return e.done || (e.value = n(e.value)), e;
	}), i;
}
var nt = Array.prototype;
function rt(e, t, n, r, i, a) {
	let o = Qe(e), s = o !== e && !/* @__PURE__ */ It(e), c = o[t];
	if (c !== nt[t]) {
		let t = c.apply(e, a);
		return s ? zt(t) : t;
	}
	let l = n;
	o !== e && (s ? l = function(t, r) {
		return n.call(this, $e(e, t), r, e);
	} : n.length > 2 && (l = function(t, r) {
		return n.call(this, t, r, e);
	}));
	let u = c.call(o, l, r);
	return s && i ? i(u) : u;
}
function it(e, t, n, r) {
	let i = Qe(e), a = i !== e && !/* @__PURE__ */ It(e), o = n, s = !1;
	i !== e && (a ? (s = r.length === 0, o = function(t, r, i) {
		return s && (s = !1, t = $e(e, t)), n.call(this, t, $e(e, r), i, e);
	}) : n.length > 3 && (o = function(t, r, i) {
		return n.call(this, t, r, i, e);
	}));
	let c = i[t](o, ...r);
	return s ? $e(e, c) : c;
}
function at(e, t, n) {
	let r = /* @__PURE__ */ B(e);
	Ye(r, "iterate", Je);
	let i = r[t](...n);
	return (i === -1 || i === !1) && /* @__PURE__ */ Lt(n[0]) ? (n[0] = /* @__PURE__ */ B(n[0]), r[t](...n)) : i;
}
function ot(e, t, n = []) {
	Re(), Oe();
	let r = (/* @__PURE__ */ B(e))[t].apply(e, n);
	return ke(), ze(), r;
}
var st = /* @__PURE__ */ e("__proto__,__v_isRef,__isVue"), ct = new Set(/* @__PURE__ */ Object.getOwnPropertyNames(Symbol).filter((e) => e !== "arguments" && e !== "caller").map((e) => Symbol[e]).filter(_));
function lt(e) {
	_(e) || (e = String(e));
	let t = /* @__PURE__ */ B(this);
	return Ye(t, "has", e), t.hasOwnProperty(e);
}
var ut = class {
	constructor(e = !1, t = !1) {
		this._isReadonly = e, this._isShallow = t;
	}
	get(e, t, n) {
		if (t === "__v_skip") return e.__v_skip;
		let r = this._isReadonly, i = this._isShallow;
		if (t === "__v_isReactive") return !r;
		if (t === "__v_isReadonly") return r;
		if (t === "__v_isShallow") return i;
		if (t === "__v_raw") return n === (r ? i ? Ot : Dt : i ? Et : Tt).get(e) || Object.getPrototypeOf(e) === Object.getPrototypeOf(n) ? e : void 0;
		let a = d(e);
		if (!r) {
			let e;
			if (a && (e = et[t])) return e;
			if (t === "hasOwnProperty") return lt;
		}
		let o = Reflect.get(e, t, /* @__PURE__ */ Vt(e) ? e : n);
		if ((_(t) ? ct.has(t) : st(t)) || (r || Ye(e, "get", t), i)) return o;
		if (/* @__PURE__ */ Vt(o)) {
			let e = a && w(t) ? o : o.value;
			return r && v(e) ? /* @__PURE__ */ Mt(e) : e;
		}
		return v(o) ? r ? /* @__PURE__ */ Mt(o) : /* @__PURE__ */ At(o) : o;
	}
}, dt = class extends ut {
	constructor(e = !1) {
		super(!1, e);
	}
	set(e, t, n, r) {
		let i = e[t], a = d(e) && w(t);
		if (!this._isShallow) {
			let e = /* @__PURE__ */ Ft(i);
			if (!/* @__PURE__ */ It(n) && !/* @__PURE__ */ Ft(n) && (i = /* @__PURE__ */ B(i), n = /* @__PURE__ */ B(n)), !a && /* @__PURE__ */ Vt(i) && !/* @__PURE__ */ Vt(n)) return e || (i.value = n), !0;
		}
		let o = a ? Number(t) < e.length : u(e, t), s = Reflect.set(e, t, n, /* @__PURE__ */ Vt(e) ? e : r);
		return e === /* @__PURE__ */ B(r) && s && (o ? k(n, i) && Xe(e, "set", t, n, i) : Xe(e, "add", t, n)), s;
	}
	deleteProperty(e, t) {
		let n = u(e, t), r = e[t], i = Reflect.deleteProperty(e, t);
		return i && n && Xe(e, "delete", t, void 0, r), i;
	}
	has(e, t) {
		let n = Reflect.has(e, t);
		return (!_(t) || !ct.has(t)) && Ye(e, "has", t), n;
	}
	ownKeys(e) {
		return Ye(e, "iterate", d(e) ? "length" : Ke), Reflect.ownKeys(e);
	}
}, ft = class extends ut {
	constructor(e = !1) {
		super(!0, e);
	}
	set(e, t) {
		return !0;
	}
	deleteProperty(e, t) {
		return !0;
	}
}, pt = /* @__PURE__ */ new dt(), mt = /* @__PURE__ */ new ft(), ht = /* @__PURE__ */ new dt(!0), gt = (e) => e, _t = (e) => Reflect.getPrototypeOf(e);
function vt(e, t, n) {
	return function(...r) {
		let i = this.__v_raw, a = /* @__PURE__ */ B(i), o = f(a), c = e === "entries" || e === Symbol.iterator && o, l = e === "keys" && o, u = i[e](...r), d = n ? gt : t ? Bt : zt;
		return !t && Ye(a, "iterate", l ? qe : Ke), s(Object.create(u), { next() {
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
function yt(e) {
	return function(...t) {
		return e === "delete" ? !1 : e === "clear" ? void 0 : this;
	};
}
function bt(e, t) {
	let n = {
		get(n) {
			let r = this.__v_raw, i = /* @__PURE__ */ B(r), a = /* @__PURE__ */ B(n);
			e || (k(n, a) && Ye(i, "get", n), Ye(i, "get", a));
			let { has: o } = _t(i), s = t ? gt : e ? Bt : zt;
			if (o.call(i, n)) return s(r.get(n));
			if (o.call(i, a)) return s(r.get(a));
			r !== i && r.get(n);
		},
		get size() {
			let t = this.__v_raw;
			return !e && Ye(/* @__PURE__ */ B(t), "iterate", Ke), t.size;
		},
		has(t) {
			let n = this.__v_raw, r = /* @__PURE__ */ B(n), i = /* @__PURE__ */ B(t);
			return e || (k(t, i) && Ye(r, "has", t), Ye(r, "has", i)), t === i ? n.has(t) : n.has(t) || n.has(i);
		},
		forEach(n, r) {
			let i = this, a = i.__v_raw, o = /* @__PURE__ */ B(a), s = t ? gt : e ? Bt : zt;
			return !e && Ye(o, "iterate", Ke), a.forEach((e, t) => n.call(r, s(e), s(t), i));
		}
	};
	return s(n, e ? {
		add: yt("add"),
		set: yt("set"),
		delete: yt("delete"),
		clear: yt("clear")
	} : {
		add(e) {
			let n = /* @__PURE__ */ B(this), r = _t(n), i = /* @__PURE__ */ B(e), a = !t && !/* @__PURE__ */ It(e) && !/* @__PURE__ */ Ft(e) ? i : e;
			return r.has.call(n, a) || k(e, a) && r.has.call(n, e) || k(i, a) && r.has.call(n, i) || (n.add(a), Xe(n, "add", a, a)), this;
		},
		set(e, n) {
			!t && !/* @__PURE__ */ It(n) && !/* @__PURE__ */ Ft(n) && (n = /* @__PURE__ */ B(n));
			let r = /* @__PURE__ */ B(this), { has: i, get: a } = _t(r), o = i.call(r, e);
			o ||= (e = /* @__PURE__ */ B(e), i.call(r, e));
			let s = a.call(r, e);
			return r.set(e, n), o ? k(n, s) && Xe(r, "set", e, n, s) : Xe(r, "add", e, n), this;
		},
		delete(e) {
			let t = /* @__PURE__ */ B(this), { has: n, get: r } = _t(t), i = n.call(t, e);
			i ||= (e = /* @__PURE__ */ B(e), n.call(t, e));
			let a = r ? r.call(t, e) : void 0, o = t.delete(e);
			return i && Xe(t, "delete", e, void 0, a), o;
		},
		clear() {
			let e = /* @__PURE__ */ B(this), t = e.size !== 0, n = e.clear();
			return t && Xe(e, "clear", void 0, void 0, void 0), n;
		}
	}), [
		"keys",
		"values",
		"entries",
		Symbol.iterator
	].forEach((r) => {
		n[r] = vt(r, e, t);
	}), n;
}
function xt(e, t) {
	let n = bt(e, t);
	return (t, r, i) => r === "__v_isReactive" ? !e : r === "__v_isReadonly" ? e : r === "__v_raw" ? t : Reflect.get(u(n, r) && r in t ? n : t, r, i);
}
var St = { get: /* @__PURE__ */ xt(!1, !1) }, Ct = { get: /* @__PURE__ */ xt(!1, !0) }, wt = { get: /* @__PURE__ */ xt(!0, !1) }, Tt = /* @__PURE__ */ new WeakMap(), Et = /* @__PURE__ */ new WeakMap(), Dt = /* @__PURE__ */ new WeakMap(), Ot = /* @__PURE__ */ new WeakMap();
function kt(e) {
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
function At(e) {
	return /* @__PURE__ */ Ft(e) ? e : Nt(e, !1, pt, St, Tt);
}
// @__NO_SIDE_EFFECTS__
function jt(e) {
	return Nt(e, !1, ht, Ct, Et);
}
// @__NO_SIDE_EFFECTS__
function Mt(e) {
	return Nt(e, !0, mt, wt, Dt);
}
function Nt(e, t, n, r, i) {
	if (!v(e) || e.__v_raw && !(t && e.__v_isReactive) || e.__v_skip || !Object.isExtensible(e)) return e;
	let a = i.get(e);
	if (a) return a;
	let o = kt(S(e));
	if (o === 0) return e;
	let s = new Proxy(e, o === 2 ? r : n);
	return i.set(e, s), s;
}
// @__NO_SIDE_EFFECTS__
function Pt(e) {
	return /* @__PURE__ */ Ft(e) ? /* @__PURE__ */ Pt(e.__v_raw) : !!(e && e.__v_isReactive);
}
// @__NO_SIDE_EFFECTS__
function Ft(e) {
	return !!(e && e.__v_isReadonly);
}
// @__NO_SIDE_EFFECTS__
function It(e) {
	return !!(e && e.__v_isShallow);
}
// @__NO_SIDE_EFFECTS__
function Lt(e) {
	return e ? !!e.__v_raw : !1;
}
// @__NO_SIDE_EFFECTS__
function B(e) {
	let t = e && e.__v_raw;
	return t ? /* @__PURE__ */ B(t) : e;
}
function Rt(e) {
	return !u(e, "__v_skip") && Object.isExtensible(e) && j(e, "__v_skip", !0), e;
}
var zt = (e) => v(e) ? /* @__PURE__ */ At(e) : e, Bt = (e) => v(e) ? /* @__PURE__ */ Mt(e) : e;
// @__NO_SIDE_EFFECTS__
function Vt(e) {
	return e ? e.__v_isRef === !0 : !1;
}
// @__NO_SIDE_EFFECTS__
function V(e) {
	return Ut(e, !1);
}
// @__NO_SIDE_EFFECTS__
function Ht(e) {
	return Ut(e, !0);
}
function Ut(e, t) {
	return /* @__PURE__ */ Vt(e) ? e : new Wt(e, t);
}
var Wt = class {
	constructor(e, t) {
		this.dep = new Ue(), this.__v_isRef = !0, this.__v_isShallow = !1, this._rawValue = t ? e : /* @__PURE__ */ B(e), this._value = t ? e : zt(e), this.__v_isShallow = t;
	}
	get value() {
		return this.dep.track(), this._value;
	}
	set value(e) {
		let t = this._rawValue, n = this.__v_isShallow || /* @__PURE__ */ It(e) || /* @__PURE__ */ Ft(e);
		e = n ? e : /* @__PURE__ */ B(e), k(e, t) && (this._rawValue = e, this._value = n ? e : zt(e), this.dep.trigger());
	}
};
function H(e) {
	return /* @__PURE__ */ Vt(e) ? e.value : e;
}
var Gt = {
	get: (e, t, n) => t === "__v_raw" ? e : H(Reflect.get(e, t, n)),
	set: (e, t, n, r) => {
		let i = e[t];
		return /* @__PURE__ */ Vt(i) && !/* @__PURE__ */ Vt(n) ? (i.value = n, !0) : Reflect.set(e, t, n, r);
	}
};
function Kt(e) {
	return /* @__PURE__ */ Pt(e) ? e : new Proxy(e, Gt);
}
var qt = class {
	constructor(e, t, n) {
		this.fn = e, this.setter = t, this._value = void 0, this.dep = new Ue(this), this.__v_isRef = !0, this.deps = void 0, this.depsTail = void 0, this.flags = 16, this.globalVersion = Ve - 1, this.next = void 0, this.effect = this, this.__v_isReadonly = !t, this.isSSR = n;
	}
	notify() {
		if (this.flags |= 16, !(this.flags & 8) && z !== this) return De(this, !0), !0;
	}
	get value() {
		let e = this.dep.track();
		return Ne(this), e && (e.version = this.dep.version), this._value;
	}
	set value(e) {
		this.setter && this.setter(e);
	}
};
// @__NO_SIDE_EFFECTS__
function Jt(e, t, n = !1) {
	let r, i;
	return h(e) ? r = e : (r = e.get, i = e.set), new qt(r, i, n);
}
var Yt = {}, Xt = /* @__PURE__ */ new WeakMap(), Zt = void 0;
function Qt(e, t = !1, n = Zt) {
	if (n) {
		let t = Xt.get(n);
		t || Xt.set(n, t = []), t.push(e);
	}
}
function $t(e, n, i = t) {
	let { immediate: a, deep: o, once: s, scheduler: l, augmentJob: u, call: f } = i, p = (e) => o ? e : /* @__PURE__ */ It(e) || o === !1 || o === 0 ? en(e, 1) : en(e), m, g, _, v, y = !1, b = !1;
	if (/* @__PURE__ */ Vt(e) ? (g = () => e.value, y = /* @__PURE__ */ It(e)) : /* @__PURE__ */ Pt(e) ? (g = () => p(e), y = !0) : d(e) ? (b = !0, y = e.some((e) => /* @__PURE__ */ Pt(e) || /* @__PURE__ */ It(e)), g = () => e.map((e) => {
		if (/* @__PURE__ */ Vt(e)) return e.value;
		if (/* @__PURE__ */ Pt(e)) return p(e);
		if (h(e)) return f ? f(e, 2) : e();
	})) : g = h(e) ? n ? f ? () => f(e, 2) : e : () => {
		if (_) {
			Re();
			try {
				_();
			} finally {
				ze();
			}
		}
		let t = Zt;
		Zt = m;
		try {
			return f ? f(e, 3, [v]) : e(v);
		} finally {
			Zt = t;
		}
	} : r, n && o) {
		let e = g, t = o === !0 ? Infinity : o;
		g = () => en(e(), t);
	}
	let x = be(), S = () => {
		m.stop(), x && x.active && c(x.effects, m);
	};
	if (s && n) {
		let e = n;
		n = (...t) => {
			let n = e(...t);
			return S(), n;
		};
	}
	let C = b ? Array(e.length).fill(Yt) : Yt, w = (e) => {
		if (m.flags & 1 && (m.dirty || e)) {
			if (n) {
				let t = m.run();
				if (e || o || y || (b ? t.some((e, t) => k(e, C[t])) : k(t, C))) {
					_ && _();
					let e = Zt;
					Zt = m;
					try {
						let e = [
							t,
							C === Yt ? void 0 : b && C[0] === Yt ? [] : C,
							v
						];
						C = t, f ? f(n, 3, e) : n(...e);
					} finally {
						Zt = e;
					}
				}
			} else m.run();
		}
	};
	return u && u(w), m = new Ce(g), m.scheduler = l ? () => l(w, !1) : w, v = (e) => Qt(e, !1, m), _ = m.onStop = () => {
		let e = Xt.get(m);
		if (e) {
			if (f) f(e, 4);
			else for (let t of e) t();
			Xt.delete(m);
		}
	}, n ? a ? w(!0) : C = m.run() : l ? l(w.bind(null, !0), !0) : m.run(), S.pause = m.pause.bind(m), S.resume = m.resume.bind(m), S.stop = S, S;
}
function en(e, t = Infinity, n) {
	if (t <= 0 || !v(e) || e.__v_skip || (n ||= /* @__PURE__ */ new Map(), (n.get(e) || 0) >= t)) return e;
	if (n.set(e, t), t--, /* @__PURE__ */ Vt(e)) en(e.value, t, n);
	else if (d(e)) for (let r = 0; r < e.length; r++) en(e[r], t, n);
	else if (p(e) || f(e)) e.forEach((e) => {
		en(e, t, n);
	});
	else if (C(e)) {
		for (let r in e) en(e[r], t, n);
		for (let r of Object.getOwnPropertySymbols(e)) Object.prototype.propertyIsEnumerable.call(e, r) && en(e[r], t, n);
	}
	return e;
}
//#endregion
//#region node_modules/@vue/runtime-core/dist/runtime-core.esm-bundler.js
function tn(e, t, n, r) {
	try {
		return r ? e(...r) : e();
	} catch (e) {
		rn(e, t, n);
	}
}
function nn(e, t, n, r) {
	if (h(e)) {
		let i = tn(e, t, n, r);
		return i && y(i) && i.catch((e) => {
			rn(e, t, n);
		}), i;
	}
	if (d(e)) {
		let i = [];
		for (let a = 0; a < e.length; a++) i.push(nn(e[a], t, n, r));
		return i;
	}
}
function rn(e, n, r, i = !0) {
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
			Re(), tn(o, null, 10, [
				e,
				i,
				a
			]), ze();
			return;
		}
	}
	an(e, r, a, i, s);
}
function an(e, t, n, r = !0, i = !1) {
	if (i) throw e;
	console.error(e);
}
var on = [], sn = -1, cn = [], ln = null, un = 0, dn = /* @__PURE__ */ Promise.resolve(), fn = null;
function pn(e) {
	let t = fn || dn;
	return e ? t.then(this ? e.bind(this) : e) : t;
}
function mn(e) {
	let t = sn + 1, n = on.length;
	for (; t < n;) {
		let r = t + n >>> 1, i = on[r], a = bn(i);
		a < e || a === e && i.flags & 2 ? t = r + 1 : n = r;
	}
	return t;
}
function hn(e) {
	if (!(e.flags & 1)) {
		let t = bn(e), n = on[on.length - 1];
		!n || !(e.flags & 2) && t >= bn(n) ? on.push(e) : on.splice(mn(t), 0, e), e.flags |= 1, gn();
	}
}
function gn() {
	fn ||= dn.then(xn);
}
function _n(e) {
	if (!d(e)) ln && e.id === -1 ? ln.splice(un + 1, 0, e) : e.flags & 1 || (cn.push(e), e.flags |= 1);
	else for (let t = 0; t < e.length; t++) cn.push(e[t]);
	gn();
}
function vn(e, t, n = sn + 1) {
	for (; n < on.length; n++) {
		let t = on[n];
		if (t && t.flags & 2) {
			if (e && t.id !== e.uid) continue;
			on.splice(n, 1), n--, t.flags & 4 && (t.flags &= -2), t(), t.flags & 4 || (t.flags &= -2);
		}
	}
}
function yn(e) {
	if (cn.length) {
		let e = [...new Set(cn)].sort((e, t) => bn(e) - bn(t));
		if (cn.length = 0, ln) {
			for (let t = 0; t < e.length; t++) ln.push(e[t]);
			return;
		}
		for (ln = e, un = 0; un < ln.length; un++) {
			let e = ln[un];
			e.flags & 4 && (e.flags &= -2), e.flags & 8 || e(), e.flags &= -2;
		}
		ln = null, un = 0;
	}
}
var bn = (e) => e.id == null ? e.flags & 2 ? -1 : Infinity : e.id;
function xn(e) {
	try {
		for (sn = 0; sn < on.length; sn++) {
			let e = on[sn];
			e && !(e.flags & 8) && (e.flags & 4 && (e.flags &= -2), tn(e, e.i, e.i ? 15 : 14), e.flags & 4 || (e.flags &= -2));
		}
	} finally {
		for (; sn < on.length; sn++) {
			let e = on[sn];
			e && (e.flags &= -2);
		}
		sn = -1, on.length = 0, yn(e), fn = null, (on.length || cn.length) && xn(e);
	}
}
var Sn = null, Cn = null;
function wn(e) {
	let t = Sn;
	return Sn = e, Cn = e && e.type.__scopeId || null, t;
}
function Tn(e, t = Sn, n) {
	if (!t || e._n) return e;
	let r = (...n) => {
		r._d && ri(-1);
		let i = wn(t), a = $r.length, o;
		try {
			o = e(...n);
		} finally {
			for (let e = $r.length; e > a; e--) ti();
			wn(i), r._d && ri(1);
		}
		return o;
	};
	return r._n = !0, r._c = !0, r._d = !0, r;
}
function En(e, n) {
	if (Sn === null) return e;
	let r = Fi(Sn), i = e.dirs ||= [];
	for (let e = 0; e < n.length; e++) {
		let [a, o, s, c = t] = n[e];
		a && (h(a) && (a = {
			mounted: a,
			updated: a
		}), a.deep && en(o), i.push({
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
function Dn(e, t, n, r) {
	let i = e.dirs, a = t && t.dirs;
	for (let o = 0; o < i.length; o++) {
		let s = i[o];
		a && (s.oldValue = a[o].value);
		let c = s.dir[r];
		c && (Re(), nn(c, n, 8, [
			e.el,
			s,
			e,
			t
		]), ze());
	}
}
function On(e, t) {
	if (xi) {
		let n = xi.provides, r = xi.parent && xi.parent.provides;
		r === n && (n = xi.provides = Object.create(r)), n[e] = t;
	}
}
function kn(e, t, n = !1) {
	let r = Si();
	if (r || cr) {
		let i = cr ? cr._context.provides : r ? r.parent == null || r.ce ? r.vnode.appContext && r.vnode.appContext.provides : r.parent.provides : void 0;
		if (i && e in i) return i[e];
		if (arguments.length > 1) return n && h(t) ? t.call(r && r.proxy) : t;
	}
}
var An = /* @__PURE__ */ Symbol.for("v-scx"), jn = () => kn(An);
function U(e, t, n) {
	return Mn(e, t, n);
}
function Mn(e, n, i = t) {
	let { immediate: a, deep: o, flush: c, once: l } = i, u = s({}, i), d = n && a || !n && c !== "post", f;
	if (Oi) {
		if (c === "sync") {
			let e = jn();
			f = e.__watcherHandles ||= [];
		} else if (!d) {
			let e = () => {};
			return e.stop = r, e.resume = r, e.pause = r, e;
		}
	}
	let p = xi;
	u.call = (e, t, n) => nn(e, p, t, n);
	let m = !1;
	c === "post" ? u.scheduler = (e) => {
		Lr(e, p && p.suspense);
	} : c !== "sync" && (m = !0, u.scheduler = (e, t) => {
		t ? e() : hn(e);
	}), u.augmentJob = (e) => {
		n && (e.flags |= 4), m && (e.flags |= 2, p && (e.id = p.uid, e.i = p));
	};
	let h = $t(e, n, u);
	return Oi && (f ? f.push(h) : d && h()), h;
}
var Nn = /* @__PURE__ */ Symbol("_vte"), Pn = (e) => e.__isTeleport, Fn = /* @__PURE__ */ Symbol("_leaveCb");
function In(e) {
	let t = e[0];
	if (e.length > 1) {
		for (let n of e) if (n.type !== Zr) {
			t = n;
			break;
		}
	}
	return t;
}
function Ln(e) {
	if (!qn(e)) return Pn(e.type) && e.children ? In(e.children) : e;
	if (e.component) return e.component.subTree;
	let { shapeFlag: t, children: n } = e;
	if (n) {
		if (t & 16) return n[0];
		if (t & 32 && h(n.default)) return n.default();
	}
}
function Rn(e, t) {
	if (e.shapeFlag & 6 && e.component) {
		e.transition = t;
		let n = e.component.subTree;
		Rn(Pn(n.type) && Ln(n) || n, t);
	} else e.shapeFlag & 128 ? (e.ssContent.transition = t.clone(e.ssContent), e.ssFallback.transition = t.clone(e.ssFallback)) : e.transition = t;
}
// @__NO_SIDE_EFFECTS__
function zn(e, t) {
	return h(e) ? /* @__PURE__ */ s({ name: e.name }, t, { setup: e }) : e;
}
function Bn() {
	let e = Si();
	return e ? (e.appContext.config.idPrefix || "v") + "-" + e.ids[0] + e.ids[1]++ : "";
}
function Vn(e) {
	e.ids = [
		e.ids[0] + e.ids[2]++ + "-",
		0,
		0
	];
}
function Hn(e, t) {
	let n;
	return !!((n = Object.getOwnPropertyDescriptor(e, t)) && !n.configurable);
}
var Un = /* @__PURE__ */ new WeakMap();
function Wn(e, n, r, a, o = !1) {
	if (d(e)) {
		e.forEach((e, t) => Wn(e, n && (d(n) ? n[t] : n), r, a, o));
		return;
	}
	if (Kn(a) && !o) {
		a.shapeFlag & 512 && a.type.__asyncResolved && a.component.subTree.component && Wn(e, n, r, a.component.subTree);
		return;
	}
	let s = a.shapeFlag & 4 ? Fi(a.component) : a.el, l = o ? null : s, { i: f, r: p } = e, m = n && n.r, _ = f.refs === t ? f.refs = {} : f.refs, v = f.setupState, y = /* @__PURE__ */ B(v), b = v === t ? i : (e) => !Hn(_, e) && u(y, e), x = (e, t) => !(t && Hn(_, t));
	if (m != null && m !== p) {
		if (Gn(n), g(m)) _[m] = null, b(m) && (v[m] = null);
		else if (/* @__PURE__ */ Vt(m)) {
			let e = n;
			x(m, e.k) && (m.value = null), e.k && (_[e.k] = null);
		}
	}
	if (h(p)) tn(p, f, 12, [l, _]);
	else {
		let t = g(p), n = /* @__PURE__ */ Vt(p);
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
					i(), Un.delete(e);
				};
				t.id = -1, Un.set(e, t), Lr(t, r);
			} else Gn(e), i();
		}
	}
}
function Gn(e) {
	let t = Un.get(e);
	t && (t.flags |= 8, Un.delete(e));
}
se().requestIdleCallback, se().cancelIdleCallback;
var Kn = (e) => !!e.type.__asyncLoader, qn = (e) => e.type.__isKeepAlive;
function Jn(e, t, n = xi, r = !1) {
	if (n) {
		let i = n[e] || (n[e] = []), a = t.__weh ||= (...r) => {
			Re();
			let i = Ti(n), a = nn(t, n, e, r);
			return i(), ze(), a;
		};
		return r ? i.unshift(a) : i.push(a), a;
	}
}
var Yn = (e) => (t, n = xi) => {
	(!Oi || e === "sp") && Jn(e, (...e) => t(...e), n);
}, Xn = Yn("m"), Zn = Yn("bum"), Qn = /* @__PURE__ */ Symbol.for("v-ndc");
function W(e, t, n, r) {
	let i, a = n && n[r], o = d(e);
	if (o || g(e)) {
		let n = o && /* @__PURE__ */ Pt(e), r = !1, s = !1;
		n && (r = !/* @__PURE__ */ It(e), s = /* @__PURE__ */ Ft(e), e = Qe(e)), i = Array(e.length);
		for (let n = 0, o = e.length; n < o; n++) i[n] = t(r ? s ? Bt(zt(e[n])) : zt(e[n]) : e[n], n, void 0, a && a[n]);
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
function $n(e, t, n, r, i, a) {
	if (n ??= {}, Sn.ce || Sn.parent && Kn(Sn.parent) && Sn.parent.ce) {
		let e = a != null && n.key == null ? s({}, n, { key: a }) : n, i = Object.keys(e).length > 0;
		return t !== "default" && (e.name = t), K(), ai(G, null, [Y("slot", e, r && r())], i ? -2 : 64);
	}
	let o = e[t];
	o && o._c && (o._d = !1);
	let c = $r.length;
	K();
	let l;
	try {
		let i = o && er(o(n)), s = n.key || a || i && i.key;
		l = ai(G, { key: (s && !_(s) ? s : `_${t}`) + (!i && r ? "_fb" : "") }, i || (r ? r() : []), i && e._ === 1 ? 64 : -2);
	} catch (e) {
		for (let e = $r.length; e > c; e--) ti();
		throw e;
	} finally {
		o && o._c && (o._d = !0);
	}
	return !i && l.scopeId && (l.slotScopeIds = [l.scopeId + "-s"]), l;
}
function er(e) {
	return e.some((e) => !oi(e) || !(e.type === Zr || e.type === G && !er(e.children))) ? e : null;
}
var tr = (e) => e ? Di(e) ? Fi(e) : tr(e.parent) : null, nr = /* @__PURE__ */ s(/* @__PURE__ */ Object.create(null), {
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
		hn(e.update);
	},
	$nextTick: (e) => e.n ||= pn.bind(e.proxy),
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
		if (d) return n === "$attrs" && Ye(e.attrs, "get", ""), d(e);
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
			version: Li,
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
					return u.appContext = i, s === !0 ? s = "svg" : s === !1 && (s = void 0), o && t ? t(u, a) : e(u, a, s), c = !0, l._container = a, a.__vue_app__ = l, Fi(u.component);
				}
			},
			onUnmount(e) {
				o.push(e);
			},
			unmount() {
				c && (nn(o, l._instance, 16), e(null, l._container), delete l._container.__vue_app__);
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
var cr = null, lr = (e, t) => t === "modelValue" || t === "model-value" ? e.modelModifiers : e[`${t}Modifiers`] || e[`${D(t)}Modifiers`] || e[`${O(t)}Modifiers`];
function ur(e, n, ...r) {
	if (e.isUnmounted) return;
	let i = e.vnode.props || t, a = r, o = n.startsWith("update:"), s = o && lr(i, n.slice(7));
	s && (s.trim && (a = r.map((e) => g(e) ? e.trim() : e)), s.number && (a = a.map(ie)));
	let c, l = i[c = re(n)] || i[c = re(D(n))];
	!l && o && (l = i[c = re(O(n))]), l && nn(l, e, 6, a);
	let u = i[c + "Once"];
	if (u) {
		if (!e.emitted) e.emitted = {};
		else if (e.emitted[c]) return;
		e.emitted[c] = !0, nn(u, e, 6, a);
	}
}
function dr(e, t, n = !1) {
	let r = t.emitsCache, i = r.get(e);
	if (i !== void 0) return i;
	let a = e.emits, o = {};
	return a ? (d(a) ? a.forEach((e) => o[e] = null) : s(o, a), v(e) && r.set(e, o), o) : (v(e) && r.set(e, null), null);
}
function fr(e, t) {
	return !e || !a(t) ? !1 : (t = t.slice(2), t = t === "Once" ? t : t.replace(/Once$/, ""), u(e, t[0].toLowerCase() + t.slice(1)) || u(e, O(t)) || u(e, t));
}
function pr(e) {
	let { type: t, vnode: n, proxy: r, withProxy: i, propsOptions: [a], slots: s, attrs: c, emit: l, render: u, renderCache: d, props: f, data: p, setupState: m, ctx: h, inheritAttrs: g } = e, _ = wn(e), v, y;
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
			}) : e(f, null)), y = t.props ? c : mr(c);
		}
	} catch (t) {
		$r.length = 0, rn(t, e, 1), v = Y(Zr);
	}
	let b = v;
	if (y && g !== !1) {
		let e = Object.keys(y), { shapeFlag: t } = b;
		e.length && t & 7 && (a && e.some(o) && (y = hr(y, a)), b = fi(b, y, !1, !0));
	}
	return n.dirs && (b = fi(b, null, !1, !0), b.dirs = b.dirs ? b.dirs.concat(n.dirs) : n.dirs), n.transition && Rn(Pn(b.type) && Ln(b) || b, n.transition), v = b, wn(_), v;
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
	return n === "style" && v(r) && v(i) ? !I(r, i) : r !== i;
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
	e.props = n ? r ? i : /* @__PURE__ */ jt(i) : e.type.props ? i : a, e.attrs = a;
}
function wr(e, t, n, r) {
	let { props: i, attrs: a, vnode: { patchFlag: o } } = e, s = /* @__PURE__ */ B(i), [c] = e.propsOptions, l = !1;
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
		for (let a in s) (!t || !u(t, a) && ((r = O(a)) === a || !u(t, r))) && (c ? n && (n[a] !== void 0 || n[r] !== void 0) && (i[a] = Er(c, s, a, void 0, e, !0)) : delete i[a]);
		if (a !== s) for (let e in a) (!t || !u(t, e)) && (delete a[e], l = !0);
	}
	l && Xe(e.attrs, "set", "");
}
function Tr(e, n, r, i) {
	let [a, o] = e.propsOptions, s = !1, c;
	if (n) for (let t in n) {
		if (T(t)) continue;
		let l = n[t], d;
		a && u(a, d = D(t)) ? !o || !o.includes(d) ? r[d] = l : (c ||= {})[d] = l : fr(e.emitsOptions, t) || (!(t in i) || l !== i[t]) && (i[t] = l, s = !0);
	}
	if (o) {
		let n = /* @__PURE__ */ B(r), i = c || t;
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
					let o = Ti(i);
					r = a[n] = e.call(null, t), o();
				}
			} else r = e;
			i.ce && i.ce._setProp(n, r);
		}
		o[0] && (a && !e ? r = !1 : o[1] && (r === "" || r === O(n)) && (r = !0));
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
	return e[0] !== "$" && !T(e);
}
var kr = (e) => e === "_" || e === "_ctx" || e === "$stable", Ar = (e) => d(e) ? e.map(pi) : [pi(e)], jr = (e, t, n) => {
	if (t._n) return t;
	let r = Tn((...e) => Ar(t(...e)), n);
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
		e ? (Pr(r, t, n), n && j(r, "_", e, !0)) : Mr(t, r);
	} else t && Nr(e, t);
}, Ir = (e, n, r) => {
	let { vnode: i, slots: a } = e, o = !0, s = t;
	if (i.shapeFlag & 32) {
		let e = n._;
		e ? r && e === 1 ? o = !1 : Pr(a, n, r) : (o = !n.$stable, Mr(n, a)), s = n;
	} else n && (Nr(e, n), s = { default: 1 });
	if (o) for (let e in a) !kr(e) && s[e] == null && delete a[e];
}, Lr = Yr;
function Rr(e) {
	return zr(e);
}
function zr(e, i) {
	let a = se();
	a.__VUE__ = !0;
	let { insert: o, remove: s, patchProp: c, createElement: l, createText: u, createComment: d, setText: f, setElementText: p, parentNode: m, nextSibling: h, setScopeId: g = r, insertStaticContent: _ } = e, v = (e, t, n, r = null, i = null, a = null, o = void 0, s = null, c = !!t.dynamicChildren) => {
		if (e === t) return;
		e && !si(e, t) && (r = pe(e), N(e, i, a, !0), e = null), t.patchFlag === -2 && (c = !1, t.dynamicChildren = null);
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
			case G:
				re(e, t, n, r, i, a, o, s, c);
				break;
			default: d & 1 ? w(e, t, n, r, i, a, o, s, c) : d & 6 ? k(e, t, n, r, i, a, o, s, c) : (d & 64 || d & 128) && l.process(e, t, n, r, i, a, o, s, c, he);
		}
		u != null && i ? Wn(u, e && e.ref, a, t || e, !t) : u == null && e && e.ref != null && Wn(e.ref, null, a, e, !0);
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
		if (d = e.el = l(e.type, a, m && m.is, m), h & 8 ? p(d, e.children) : h & 16 && D(e.children, d, null, r, i, Br(e, a), s, u), _ && Dn(e, null, r, "created"), E(d, e, e.scopeId, s, r), m) {
			for (let e in m) e !== "value" && !T(e) && c(d, e, null, m[e], a, r);
			"value" in m && c(d, "value", null, m.value, a), (f = m.onVnodeBeforeMount) && _i(f, r, e);
		}
		_ && Dn(e, null, r, "beforeMount");
		let v = Hr(i, g);
		v && g.beforeEnter(d), o(d, t, n), ((f = m && m.onVnodeMounted) || v || _) && Lr(() => {
			try {
				f && _i(f, r, e), v && g.enter(d), _ && Dn(e, null, r, "mounted");
			} finally {}
		}, i);
	}, E = (e, t, n, r, i) => {
		if (n && g(e, n), r) for (let t = 0; t < r.length; t++) g(e, r[t]);
		if (i) {
			let n = i.subTree;
			if (t === n || Jr(n.type) && (n.ssContent === t || n.ssFallback === t)) {
				let t = i.vnode;
				E(e, t, t.scopeId, t.slotScopeIds, i.parent);
			}
		}
	}, D = (e, t, n, r, i, a, o, s, c = 0) => {
		for (let l = c; l < e.length; l++) {
			let c = e[l] = s ? mi(e[l]) : pi(e[l]);
			v(null, c, t, n, r, i, a, o, s);
		}
	}, te = (e, n, r, i, a, o, s) => {
		let l = n.el = e.el, { patchFlag: u, dynamicChildren: d, dirs: f } = n;
		u |= e.patchFlag & 16;
		let m = e.props || t, h = n.props || t, g;
		if (r && Vr(r, !1), (g = h.onVnodeBeforeUpdate) && _i(g, r, n, e), f && Dn(n, e, r, "beforeUpdate"), r && Vr(r, !0), d && (!e.dynamicChildren || e.dynamicChildren.length !== d.length) && (u = 0, s = !1, d = null), (m.innerHTML && h.innerHTML == null || m.textContent && h.textContent == null) && p(l, ""), d ? O(e.dynamicChildren, d, l, r, i, Br(n, a), o) : s || M(e, n, l, null, r, i, Br(n, a), o, !1), u > 0) {
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
		((g = h.onVnodeUpdated) || f) && Lr(() => {
			g && _i(g, r, n, e), f && Dn(n, e, r, "updated");
		}, i);
	}, O = (e, t, n, r, i, a, o) => {
		for (let s = 0; s < t.length; s++) {
			let c = e[s], l = t[s], u = c.el && (c.type === G || !si(c, l) || c.shapeFlag & 198) ? m(c.el) : n;
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
		h && (c = c ? c.concat(h) : h), e == null ? (o(d, n, r), o(f, n, r), D(t.children || [], n, f, i, a, s, c, l)) : p > 0 && p & 64 && m && e.dynamicChildren && e.dynamicChildren.length === m.length ? (O(e.dynamicChildren, m, n, i, a, s, c), (t.key != null || i && t === i.subTree) && Ur(e, t, !0)) : M(e, t, n, f, i, a, s, c, l);
	}, k = (e, t, n, r, i, a, o, s, c) => {
		t.slotScopeIds = s, e == null ? t.shapeFlag & 512 ? i.ctx.activate(t, n, r, o, c) : j(t, n, r, i, a, o, c) : ie(e, t, c);
	}, j = (e, t, n, r, i, a, o) => {
		let s = e.component = bi(e, r, i);
		if (qn(e) && (s.ctx.renderer = he), ki(s, !1, o), s.asyncDep) {
			if (i && i.registerDep(s, ae, o), !e.el) {
				let r = s.subTree = Y(Zr);
				b(null, r, t, n), e.placeholder = r.el;
			}
		} else ae(s, e, t, n, i, a, o);
	}, ie = (e, t, n) => {
		let r = t.component = e.component;
		if (gr(e, t, n)) {
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
					let n = Gr(e);
					if (n) {
						t && (t.el = c.el, oe(e, t, o)), n.asyncDep.then(() => {
							Lr(() => {
								e.isUnmounted || l();
							}, i);
						});
						return;
					}
				}
				let u = t, d;
				Vr(e, !1), t ? (t.el = c.el, oe(e, t, o)) : t = c, n && A(n), (d = t.props && t.props.onVnodeBeforeUpdate) && _i(d, s, t, c), Vr(e, !0);
				let f = pr(e), p = e.subTree;
				e.subTree = f, v(p, f, m(p.el), pe(p), e, i, a), t.el = f.el, u === null && yr(e, f.el), r && Lr(r, i), (d = t.props && t.props.onVnodeUpdated) && Lr(() => _i(d, s, t, c), i);
			} else {
				let o, { el: s, props: c } = t, { bm: l, m: u, parent: d, root: f, type: p } = e, m = Kn(t);
				if (Vr(e, !1), l && A(l), !m && (o = c && c.onVnodeBeforeMount) && _i(o, d, t), Vr(e, !0), s && L) {
					let t = () => {
						e.subTree = pr(e), L(s, e.subTree, e, i, null);
					};
					m && p.__asyncHydrate ? p.__asyncHydrate(s, e, t) : t();
				} else {
					f.ce && f.ce._hasShadowRoot() && f.ce._injectChildStyle(p, e.parent ? e.parent.type : void 0);
					let o = e.subTree = pr(e);
					v(null, o, n, r, e, i, a), t.el = o.el;
				}
				if (u && Lr(u, i), !m && (o = c && c.onVnodeMounted)) {
					let e = t;
					Lr(() => _i(o, d, e), i);
				}
				(t.shapeFlag & 256 || d && Kn(d.vnode) && d.vnode.shapeFlag & 256) && e.a && Lr(e.a, i), e.isMounted = !0, t = n = r = null;
			}
		};
		e.scope.on();
		let c = e.effect = new Ce(s);
		e.scope.off();
		let l = e.update = c.run.bind(c), u = e.job = c.runIfDirty.bind(c);
		u.i = e, u.id = e.uid, c.scheduler = () => hn(u), Vr(e, !0), l();
	}, oe = (e, t, n) => {
		t.component = e;
		let r = e.vnode.props;
		e.vnode = t, e.next = null, wr(e, t.props, r, n), Ir(e, t.children, n), Re(), vn(e), ze();
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
		m & 8 ? (u & 16 && F(l, i, a), d !== l && p(n, d)) : u & 16 ? m & 16 ? le(l, d, n, r, i, a, o, s, c) : F(l, i, a, !0) : (u & 8 && p(n, ""), m & 16 && D(d, n, r, i, a, o, s, c));
	}, ce = (e, t, r, i, a, o, s, c, l) => {
		e ||= n, t ||= n;
		let u = e.length, d = t.length, f = Math.min(u, d), p = 0;
		for (; p < f; p++) {
			let n = t[p] = l ? mi(t[p]) : pi(t[p]);
			v(e[p], n, r, null, a, o, s, c, l);
		}
		u > d ? F(e, a, o, !0, !1, f) : D(t, r, i, a, o, s, c, l, f);
	}, le = (e, t, r, i, a, o, s, c, l) => {
		let u = 0, d = t.length, f = e.length - 1, p = d - 1;
		for (; u <= f && u <= p;) {
			let n = e[u], i = t[u] = l ? mi(t[u]) : pi(t[u]);
			if (si(n, i)) v(n, i, r, null, a, o, s, c, l);
			else break;
			u++;
		}
		for (; u <= f && u <= p;) {
			let n = e[f], i = t[p] = l ? mi(t[p]) : pi(t[p]);
			if (si(n, i)) v(n, i, r, null, a, o, s, c, l);
			else break;
			f--, p--;
		}
		if (u > f) {
			if (u <= p) {
				let e = p + 1, n = e < d ? t[e].el : i;
				for (; u <= p;) v(null, t[u] = l ? mi(t[u]) : pi(t[u]), r, n, a, o, s, c, l), u++;
			}
		} else if (u > p) for (; u <= f;) N(e[u], a, o, !0), u++;
		else {
			let m = u, h = u, g = /* @__PURE__ */ new Map();
			for (u = h; u <= p; u++) {
				let e = t[u] = l ? mi(t[u]) : pi(t[u]);
				e.key != null && g.set(e.key, u);
			}
			let _, y = 0, b = p - h + 1, x = !1, S = 0, C = Array(b);
			for (u = 0; u < b; u++) C[u] = 0;
			for (u = m; u <= f; u++) {
				let n = e[u];
				if (y >= b) {
					N(n, a, o, !0);
					continue;
				}
				let i;
				if (n.key != null) i = g.get(n.key);
				else for (_ = h; _ <= p; _++) if (C[_ - h] === 0 && si(n, t[_])) {
					i = _;
					break;
				}
				i === void 0 ? N(n, a, o, !0) : (C[i - h] = u + 1, i >= S ? S = i : x = !0, v(n, t[i], r, null, a, o, s, c, l), y++);
			}
			let w = x ? Wr(C) : n;
			for (_ = w.length - 1, u = b - 1; u >= 0; u--) {
				let e = h + u, n = t[e], f = t[e + 1], p = e + 1 < d ? f.el || qr(f) : i;
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
			c.move(e, t, n, he);
			return;
		}
		if (c === G) {
			o(a, t, n);
			for (let e = 0; e < u.length; e++) ue(u[e], t, n, r);
			o(e.anchor, t, n);
			return;
		}
		if (c === Qr) {
			S(e, t, n);
			return;
		}
		if (r !== 2 && d & 1 && l) {
			if (r === 0) l.persisted && !a[Fn] ? o(a, t, n) : (l.beforeEnter(a), o(a, t, n), Lr(() => l.enter(a), i));
			else {
				let { leave: r, delayLeave: i, afterLeave: c } = l, u = () => {
					e.ctx.isUnmounted ? s(a) : o(a, t, n);
				}, d = () => {
					let e = a._isLeaving || !!a[Fn];
					a._isLeaving && a[Fn](!0), l.persisted && !e ? u() : r(a, () => {
						u(), c && c();
					});
				};
				i ? i(a, u, d) : d();
			}
		} else o(a, t, n);
	}, N = (e, t, n, r = !1, i = !1) => {
		let { type: a, props: o, ref: s, children: c, dynamicChildren: l, shapeFlag: u, patchFlag: d, dirs: f, cacheIndex: p, memo: m } = e;
		if (d === -2 && (i = !1), s != null && (Re(), Wn(s, null, n, e, !0), ze()), p != null && (t.renderCache[p] = void 0), u & 256) {
			t.ctx.deactivate(e);
			return;
		}
		let h = u & 1 && f, g = !Kn(e), _;
		if (g && (_ = o && o.onVnodeBeforeUnmount) && _i(_, t, e), u & 6) P(e.component, n, r);
		else {
			if (u & 128) {
				e.suspense.unmount(n, r);
				return;
			}
			h && Dn(e, null, t, "beforeUnmount"), u & 64 ? e.type.remove(e, t, n, he, r) : l && !l.hasOnce && (a !== G || d > 0 && d & 64) ? F(l, t, n, !1, !0) : (a === G && d & 384 || !i && u & 16) && F(c, t, n), r && de(e);
		}
		let v = m != null && p == null;
		(g && (_ = o && o.onVnodeUnmounted) || h || v) && Lr(() => {
			_ && _i(_, t, e), h && Dn(e, null, t, "unmounted"), v && (e.el = null);
		}, n);
	}, de = (e) => {
		let { type: t, el: n, anchor: r, transition: i } = e;
		if (t === G) {
			fe(n, r);
			return;
		}
		if (t === Qr) {
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
	}, P = (e, t, n) => {
		let { bum: r, scope: i, job: a, subTree: o, um: s, m: c, a: l } = e;
		Kr(c), Kr(l), r && A(r), i.stop(), a && (a.flags |= 8, N(o, e, t, n)), s && Lr(s, t), Lr(() => {
			e.isUnmounted = !0;
		}, t);
	}, F = (e, t, n, r = !1, i = !1, a = 0) => {
		for (let o = a; o < e.length; o++) N(e[o], t, n, r, i);
	}, pe = (e) => {
		if (e.shapeFlag & 6) return pe(e.component.subTree);
		if (e.shapeFlag & 128) return e.suspense.next();
		let t = h(e.anchor || e.el), n = t && t[Nn];
		return n ? h(n) : t;
	}, me = !1, I = (e, t, n) => {
		let r;
		e == null ? t._vnode && (N(t._vnode, null, null, !0), r = t._vnode.component) : v(t._vnode || null, e, t, null, null, null, n), t._vnode = e, me ||= (me = !0, vn(r), yn(), !1);
	}, he = {
		p: v,
		um: N,
		m: ue,
		r: de,
		mt: j,
		mc: D,
		pc: M,
		pbc: O,
		n: pe,
		o: e
	}, ge, L;
	return i && ([ge, L] = i(he)), {
		render: I,
		hydrate: ge,
		createApp: sr(I, ge)
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
	t && t.pendingBranch ? d(e) ? t.effects.push(...e) : t.effects.push(e) : _n(e);
}
var G = /* @__PURE__ */ Symbol.for("v-fgt"), Xr = /* @__PURE__ */ Symbol.for("v-txt"), Zr = /* @__PURE__ */ Symbol.for("v-cmt"), Qr = /* @__PURE__ */ Symbol.for("v-stc"), $r = [], ei = null;
function K(e = !1) {
	$r.push(ei = e ? null : []);
}
function ti() {
	$r.pop(), ei = $r[$r.length - 1] || null;
}
var ni = 1;
function ri(e, t = !1) {
	ni += e, e < 0 && ei && t && (ei.hasOnce = !0);
}
function ii(e) {
	return e.dynamicChildren = ni > 0 ? ei || n : null, ti(), ni > 0 && ei && ei.push(e), e;
}
function q(e, t, n, r, i, a) {
	return ii(J(e, t, n, r, i, a, !0));
}
function ai(e, t, n, r, i) {
	return ii(Y(e, t, n, r, i, !0));
}
function oi(e) {
	return e ? e.__v_isVNode === !0 : !1;
}
function si(e, t) {
	return e.type === t.type && e.key === t.key;
}
var ci = ({ key: e }) => e ?? null, li = ({ ref: e, ref_key: t, ref_for: n }) => (typeof e == "number" && (e = "" + e), e == null ? null : g(e) || /* @__PURE__ */ Vt(e) || h(e) ? {
	i: Sn,
	r: e,
	k: t,
	f: !!n
} : e);
function J(e, t = null, n = null, r = 0, i = null, a = e === G ? 0 : 1, o = !1, s = !1) {
	let c = {
		__v_isVNode: !0,
		__v_skip: !0,
		type: e,
		props: t,
		key: t && ci(t),
		ref: t && li(t),
		scopeId: Cn,
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
		ctx: Sn
	};
	return s ? (hi(c, n), a & 128 && e.normalize(c)) : n && (c.shapeFlag |= g(n) ? 8 : 16), ni > 0 && !o && ei && (c.patchFlag > 0 || a & 6) && c.patchFlag !== 32 && ei.push(c), c;
}
var Y = ui;
function ui(e, t = null, n = null, r = 0, i = null, a = !1) {
	if ((!e || e === Qn) && (e = Zr), oi(e)) {
		let r = fi(e, t, !0);
		return n && hi(r, n), ni > 0 && !a && ei && (r.shapeFlag & 6 ? ei[ei.indexOf(e)] = r : ei.push(r)), r.patchFlag = -2, r;
	}
	if (Ii(e) && (e = e.__vccOpts), t) {
		t = di(t);
		let { class: e, style: n } = t;
		e && !g(e) && (t.class = de(e)), v(n) && (/* @__PURE__ */ Lt(n) && !d(n) && (n = s({}, n)), t.style = M(n));
	}
	let o = g(e) ? 1 : Jr(e) ? 128 : Pn(e) ? 64 : v(e) ? 4 : h(e) ? 2 : 0;
	return J(e, t, n, r, i, o, a, !0);
}
function di(e) {
	return e ? /* @__PURE__ */ Lt(e) || Sr(e) ? s({}, e) : e : null;
}
function fi(e, t, n = !1, r = !1) {
	let { props: i, ref: a, patchFlag: o, children: s, transition: c } = e, l = t ? gi(i || {}, t) : i, u = {
		__v_isVNode: !0,
		__v_skip: !0,
		type: e.type,
		props: l,
		key: l && ci(l),
		ref: t && t.ref ? n && a ? d(a) ? a.concat(li(t)) : [a, li(t)] : li(t) : a,
		scopeId: e.scopeId,
		slotScopeIds: e.slotScopeIds,
		children: s,
		target: e.target,
		targetStart: e.targetStart,
		targetAnchor: e.targetAnchor,
		staticCount: e.staticCount,
		shapeFlag: e.shapeFlag,
		patchFlag: t && e.type !== G ? o === -1 ? 16 : o | 16 : o,
		dynamicProps: e.dynamicProps,
		dynamicChildren: e.dynamicChildren,
		appContext: e.appContext,
		dirs: e.dirs,
		transition: c,
		component: e.component,
		suspense: e.suspense,
		ssContent: e.ssContent && fi(e.ssContent),
		ssFallback: e.ssFallback && fi(e.ssFallback),
		placeholder: e.placeholder,
		el: e.el,
		anchor: e.anchor,
		ctx: e.ctx,
		ce: e.ce
	};
	return c && r && Rn(u, c.clone(u)), u;
}
function X(e = " ", t = 0) {
	return Y(Xr, null, e, t);
}
function Z(e = "", t = !1) {
	return t ? (K(), ai(Zr, null, e)) : Y(Zr, null, e);
}
function pi(e) {
	return e == null || typeof e == "boolean" ? Y(Zr) : d(e) ? Y(G, null, e.slice()) : oi(e) ? mi(e) : Y(Xr, null, String(e));
}
function mi(e) {
	return e.el === null && e.patchFlag !== -1 || e.memo ? e : fi(e);
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
			!r && !Sr(t) ? t._ctx = Sn : r === 3 && Sn && (Sn.slots._ === 1 ? t._ = 1 : (t._ = 2, e.patchFlag |= 1024));
		}
	} else if (h(t)) {
		if (r & 65) {
			hi(e, { default: t });
			return;
		}
		t = {
			default: t,
			_ctx: Sn
		}, n = 32;
	} else t = String(t), r & 64 ? (n = 16, t = [X(t)]) : n = 8;
	e.children = t, e.shapeFlag |= n;
}
function gi(...e) {
	let t = {};
	for (let n = 0; n < e.length; n++) {
		let r = e[n];
		for (let e in r) if (e === "class") t.class !== r.class && (t.class = de([t.class, r.class]));
		else if (e === "style") t.style = M([t.style, r.style]);
		else if (a(e)) {
			let n = t[e], i = r[e];
			i && n !== i && !(d(n) && n.includes(i)) ? t[e] = n ? [].concat(n, i) : i : i == null && n == null && !o(e) && (t[e] = i);
		} else e !== "" && (t[e] = r[e]);
	}
	return t;
}
function _i(e, t, n, r = null) {
	nn(e, t, 7, [n, r]);
}
var vi = ar(), yi = 0;
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
		scope: new ye(!0),
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
var xi = null, Si = () => xi || Sn, Ci, wi;
{
	let e = se(), t = (t, n) => {
		let r;
		return (r = e[t]) || (r = e[t] = []), r.push(n), (e) => {
			r.length > 1 ? r.forEach((t) => t(e)) : r[0](e);
		};
	};
	Ci = t("__VUE_INSTANCE_SETTERS__", (e) => xi = e), wi = t("__VUE_SSR_SETTERS__", (e) => Oi = e);
}
var Ti = (e) => {
	let t = xi;
	return Ci(e), e.scope.on(), () => {
		e.scope.off(), Ci(t);
	};
}, Ei = () => {
	xi && xi.scope.off(), Ci(null);
};
function Di(e) {
	return e.vnode.shapeFlag & 4;
}
var Oi = !1;
function ki(e, t = !1, n = !1) {
	t && wi(t);
	let { props: r, children: i } = e.vnode, a = Di(e);
	Cr(e, r, a, t), Fr(e, i, n || t);
	let o = a ? Ai(e, t) : void 0;
	return t && wi(!1), o;
}
function Ai(e, t) {
	let n = e.type;
	e.accessCache = /* @__PURE__ */ Object.create(null), e.proxy = new Proxy(e.ctx, ir);
	let { setup: r } = n;
	if (r) {
		Re();
		let n = e.setupContext = r.length > 1 ? Pi(e) : null, i = Ti(e), a = tn(r, e, 0, [e.props, n]), o = y(a);
		if (ze(), i(), (o || e.sp) && !Kn(e) && Vn(e), o) {
			if (a.then(Ei, Ei), t) return a.then((n) => {
				wi(!0);
				try {
					ji(e, n, t);
				} finally {
					wi(!1);
				}
			}).catch((t) => {
				rn(t, e, 0);
			});
			e.asyncDep = a;
		} else ji(e, a, t);
	} else Mi(e, t);
}
function ji(e, t, n) {
	h(t) ? e.type.__ssrInlineRender ? e.ssrRender = t : e.render = t : v(t) && (e.setupState = Kt(t)), Mi(e, n);
}
function Mi(e, t, n) {
	let i = e.type;
	e.render ||= i.render || r;
}
var Ni = { get(e, t) {
	return Ye(e, "get", ""), e[t];
} };
function Pi(e) {
	return {
		attrs: new Proxy(e.attrs, Ni),
		slots: e.slots,
		emit: e.emit,
		expose: (t) => {
			e.exposed = t || {};
		}
	};
}
function Fi(e) {
	return e.exposed ? e.exposeProxy ||= new Proxy(Kt(Rt(e.exposed)), {
		get(t, n) {
			if (n in t) return t[n];
			if (n in nr) return nr[n](e);
		},
		has(e, t) {
			return t in e || t in nr;
		}
	}) : e.proxy;
}
function Ii(e) {
	return h(e) && "__vccOpts" in e;
}
var Q = (e, t) => /* @__PURE__ */ Jt(e, t, Oi), Li = "3.5.42", Ri = void 0, zi = typeof window < "u" && window.trustedTypes;
if (zi) try {
	Ri = /* @__PURE__ */ zi.createPolicy("vue", { createHTML: (e) => e });
} catch {}
var Bi = Ri ? (e) => Ri.createHTML(e) : (e) => e, Vi = "http://www.w3.org/2000/svg", Hi = "http://www.w3.org/1998/Math/MathML", Ui = typeof document < "u" ? document : null, Wi = Ui && /* @__PURE__ */ Ui.createElement("template"), Gi = {
	insert: (e, t, n) => {
		t.insertBefore(e, n || null);
	},
	remove: (e) => {
		let t = e.parentNode;
		t && t.removeChild(e);
	},
	createElement: (e, t, n, r) => {
		let i = t === "svg" ? Ui.createElementNS(Vi, e) : t === "mathml" ? Ui.createElementNS(Hi, e) : n ? Ui.createElement(e, { is: n }) : Ui.createElement(e);
		return e === "select" && r && r.multiple != null && i.setAttribute("multiple", r.multiple), i;
	},
	createText: (e) => Ui.createTextNode(e),
	createComment: (e) => Ui.createComment(e),
	setText: (e, t) => {
		e.nodeValue = t;
	},
	setElementText: (e, t) => {
		e.textContent = t;
	},
	parentNode: (e) => e.parentNode,
	nextSibling: (e) => e.nextSibling,
	querySelector: (e) => Ui.querySelector(e),
	setScopeId(e, t) {
		e.setAttribute(t, "");
	},
	insertStaticContent(e, t, n, r, i, a) {
		let o = n ? n.previousSibling : t.lastChild;
		if (i && (i === a || i.nextSibling)) for (; t.insertBefore(i.cloneNode(!0), n), i !== a && (i = i.nextSibling););
		else {
			Wi.innerHTML = Bi(r === "svg" ? `<svg>${e}</svg>` : r === "mathml" ? `<math>${e}</math>` : e);
			let i = Wi.content;
			if (r === "svg" || r === "mathml") {
				let e = i.firstChild;
				for (; e.firstChild;) i.appendChild(e.firstChild);
				i.removeChild(e);
			}
			t.insertBefore(i, n);
		}
		return [o ? o.nextSibling : t.firstChild, n ? n.previousSibling : t.lastChild];
	}
}, Ki = /* @__PURE__ */ Symbol("_vtc");
function qi(e, t, n) {
	let r = e[Ki];
	r && (t = (t ? [t, ...r] : [...r]).join(" ")), t == null ? e.removeAttribute("class") : n ? e.setAttribute("class", t) : e.className = t;
}
var Ji = /* @__PURE__ */ Symbol("_vod"), Yi = /* @__PURE__ */ Symbol("_vsh"), Xi = {
	name: "show",
	beforeMount(e, { value: t }, { transition: n }) {
		e[Ji] = e.style.display === "none" ? "" : e.style.display, n && t ? n.beforeEnter(e) : Zi(e, t);
	},
	mounted(e, { value: t }, { transition: n }) {
		n && t && n.enter(e);
	},
	updated(e, { value: t, oldValue: n }, { transition: r }) {
		!t != !n && (r ? t ? (r.beforeEnter(e), Zi(e, !0), r.enter(e)) : r.leave(e, () => {
			Zi(e, !1);
		}) : Zi(e, t));
	},
	beforeUnmount(e, { value: t }) {
		Zi(e, t);
	}
};
function Zi(e, t) {
	e.style.display = t ? e[Ji] : "none", e[Yi] = !t;
}
var Qi = /* @__PURE__ */ Symbol(""), $i = /(?:^|;)\s*display\s*:/;
function ea(e, t, n) {
	let r = e.style, i = g(n), a = !1;
	if (n && !i) {
		if (t) {
			if (g(t)) for (let e of t.split(";")) {
				let t = e.slice(0, e.indexOf(":")).trim();
				n[t] ?? na(r, t, "");
			}
			else for (let e in t) n[e] ?? na(r, e, "");
		}
		for (let i in n) {
			i === "display" && (a = !0);
			let o = n[i];
			o == null ? na(r, i, "") : oa(e, i, !g(t) && t ? t[i] : void 0, o) || na(r, i, o);
		}
	} else if (i) {
		if (t !== n) {
			let e = r[Qi];
			e && (n += ";" + e), r.cssText = n, a = $i.test(n);
		}
	} else t && e.removeAttribute("style");
	Ji in e && (e[Ji] = a ? r.display : "", e[Yi] && (r.display = "none"));
}
var ta = /\s*!important$/;
function na(e, t, n) {
	if (d(n)) n.forEach((n) => na(e, t, n));
	else if (n ??= "", t.startsWith("--")) ta.test(n) ? e.setProperty(t, n.replace(ta, ""), "important") : e.setProperty(t, n);
	else {
		let r = aa(e, t);
		ta.test(n) ? e.setProperty(O(r), n.replace(ta, ""), "important") : e[r] = n;
	}
}
var ra = [
	"Webkit",
	"Moz",
	"ms"
], ia = {};
function aa(e, t) {
	let n = ia[t];
	if (n) return n;
	let r = D(t);
	if (r !== "filter" && r in e) return ia[t] = r;
	r = ne(r);
	for (let n = 0; n < ra.length; n++) {
		let i = ra[n] + r;
		if (i in e) return ia[t] = i;
	}
	return t;
}
function oa(e, t, n, r) {
	return e.tagName === "TEXTAREA" && (t === "width" || t === "height") && g(r) && n === r;
}
var sa = "http://www.w3.org/1999/xlink";
function ca(e, t, n, r, i, a = P(t)) {
	r && t.startsWith("xlink:") ? n == null ? e.removeAttributeNS(sa, t.slice(6, t.length)) : e.setAttributeNS(sa, t, n) : n == null || a && !F(n) ? e.removeAttribute(t) : e.setAttribute(t, a ? "" : _(n) ? String(n) : n);
}
function la(e, t, n, r, i) {
	if (t === "innerHTML" || t === "textContent") {
		n != null && (e[t] = t === "innerHTML" ? Bi(n) : n);
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
		r === "boolean" ? n = F(n) : n == null && r === "string" ? (n = "", o = !0) : r === "number" && (n = 0, o = !0);
	}
	try {
		e[t] = n;
	} catch {}
	o && e.removeAttribute(i || t);
}
function ua(e, t, n, r) {
	e.addEventListener(t, n, r);
}
function da(e, t, n, r) {
	e.removeEventListener(t, n, r);
}
var fa = /* @__PURE__ */ Symbol("_vei");
function pa(e, t, n, r, i = null) {
	let a = e[fa] || (e[fa] = {}), o = a[t];
	if (r && o) o.value = r;
	else {
		let [n, s] = ga(t);
		r ? ua(e, n, a[t] = ba(r, i), s) : o && (da(e, n, o, s), a[t] = void 0);
	}
}
var ma = /(Once|Passive|Capture)$/, ha = /^on:?(?:Once|Passive|Capture)$/;
function ga(e) {
	let t, n;
	for (; (n = e.match(ma)) && !ha.test(e);) t ||= {}, e = e.slice(0, e.length - n[1].length), t[n[1].toLowerCase()] = !0;
	return [e[2] === ":" ? e.slice(3) : O(e.slice(2)), t];
}
var _a = 0, va = /* @__PURE__ */ Promise.resolve(), ya = () => _a ||= (va.then(() => _a = 0), Date.now());
function ba(e, t) {
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
				e && nn(e, t, 5, a);
			}
		} else nn(r, t, 5, [e]);
	};
	return n.value = e, n.attached = ya(), n;
}
var xa = (e) => e.charCodeAt(0) === 111 && e.charCodeAt(1) === 110 && e.charCodeAt(2) > 96 && e.charCodeAt(2) < 123, Sa = (e, t, n, r, i, s) => {
	let c = i === "svg";
	t === "class" ? qi(e, r, c) : t === "style" ? ea(e, n, r) : a(t) ? o(t) || pa(e, t, n, r, s) : (t[0] === "." ? (t = t.slice(1), 1) : t[0] === "^" ? (t = t.slice(1), 0) : Ca(e, t, r, c)) ? (la(e, t, r), !e.tagName.includes("-") && (t === "value" || t === "checked" || t === "selected") && ca(e, t, r, c, s, t !== "value")) : e._isVueCE && (wa(e, t) || e._def.__asyncLoader && (/[A-Z]/.test(t) || !g(r))) ? la(e, D(t), r, s, t) : (t === "true-value" ? e._trueValue = r : t === "false-value" && (e._falseValue = r), ca(e, t, r, c));
};
function Ca(e, t, n, r) {
	if (r) return !!(t === "innerHTML" || t === "textContent" || t in e && xa(t) && h(n));
	if (t === "spellcheck" || t === "draggable" || t === "translate" || t === "autocorrect" || t === "sandbox" && e.tagName === "IFRAME" || t === "form" || t === "list" && e.tagName === "INPUT" || t === "type" && e.tagName === "TEXTAREA") return !1;
	if (t === "width" || t === "height") {
		let t = e.tagName;
		if (t === "IMG" || t === "VIDEO" || t === "CANVAS" || t === "SOURCE") return !1;
	}
	return xa(t) && g(n) ? !1 : t in e;
}
function wa(e, t) {
	let n = e._def.props;
	if (!n) return !1;
	let r = D(t);
	return Array.isArray(n) ? n.some((e) => D(e) === r) : Object.keys(n).some((e) => D(e) === r);
}
var Ta = {};
// @__NO_SIDE_EFFECTS__
function Ea(e, t, n) {
	let r = /* @__PURE__ */ zn(e, t);
	C(r) && (r = s({}, r, t));
	class i extends Oa {
		constructor(e) {
			super(r, e, n);
		}
	}
	return i.def = r, i;
}
var Da = typeof HTMLElement < "u" ? HTMLElement : class {}, Oa = class e extends Da {
	constructor(e, t = {}, n = Ya) {
		super(), this._def = e, this._props = t, this._createApp = n, this._isVueCE = !0, this._instance = null, this._app = null, this._nonce = this._def.nonce, this._connected = !1, this._resolved = !1, this._patching = !1, this._dirty = !1, this._numberProps = null, this._styleChildren = /* @__PURE__ */ new WeakSet(), this._styleAnchors = /* @__PURE__ */ new WeakMap(), this._ob = null, this.shadowRoot && n !== Ya ? this._root = this.shadowRoot : e.shadowRoot === !1 ? this._root = this : (this.attachShadow(s({}, e.shadowRootOptions, { mode: "open" })), this._root = this.shadowRoot);
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
		this._connected = !1, pn(() => {
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
		if (t) for (let e in t) u(this, e) || Object.defineProperty(this, e, { get: () => H(t[e]) });
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
		let t = this.hasAttribute(e), n = t ? this.getAttribute(e) : Ta, r = D(e);
		t && this._numberProps && this._numberProps[r] && (n = ae(n)), this._setProp(r, n, !1, !0);
	}
	_getProp(e) {
		return this._props[e];
	}
	_setProp(e, t, n = !0, r = !1) {
		if (t !== this._props[e] && (this._dirty = !0, t === Ta ? delete this._props[e] : (this._props[e] = t, e === "key" && this._app && (this._app._ceVNode.key = t)), r && this._instance && this._update(), n)) {
			let n = this._ob;
			n && (this._processMutations(n.takeRecords()), n.disconnect()), t === !0 ? this.setAttribute(O(e), "") : typeof t == "string" || typeof t == "number" ? this.setAttribute(O(e), t + "") : t || this.removeAttribute(O(e)), n && n.observe(this, { attributes: !0 });
		}
	}
	_update() {
		let e = this._createVNode();
		this._app && (e.appContext = this._app._context), Ja(e, this._root);
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
function ka(e) {
	let t = Si();
	return t && t.ce || null;
}
var Aa = (e) => {
	let t = e.props["onUpdate:modelValue"] || !1;
	return d(t) ? (e) => A(t, e) : t;
};
function ja(e) {
	e.target.composing = !0;
}
function Ma(e) {
	let t = e.target;
	t.composing && (t.composing = !1, t.dispatchEvent(new Event("input")));
}
var Na = /* @__PURE__ */ Symbol("_assign"), Pa = /* @__PURE__ */ Symbol("_initialValue");
function Fa(e, t, n) {
	return t && (e = e.trim()), n && (e = ie(e)), e;
}
var Ia = {
	created(e, { modifiers: { lazy: t, trim: n, number: r } }, i) {
		e.parentNode && (e.type === "text" ? e[Pa] = e.defaultValue.replace(/[\r\n]/g, "") : e.type === "textarea" && (e[Pa] = e.defaultValue.replace(/\r\n?/g, "\n"))), e[Na] = Aa(i);
		let a = r || i.props && i.props.type === "number";
		ua(e, t ? "change" : "input", (t) => {
			t.target.composing || e[Na](Fa(e.value, n, a));
		}), (n || a) && ua(e, "change", () => {
			e.value = Fa(e.value, n, a);
		}), t || (ua(e, "compositionstart", ja), ua(e, "compositionend", Ma), ua(e, "change", Ma));
	},
	mounted(e, { value: t, modifiers: { trim: n, number: r } }) {
		let i = t ?? "", a = e[Pa];
		delete e[Pa], a !== void 0 && (e.type === "text" || e.type === "textarea") && e.value !== a ? e[Na](Fa(e.value, n, r)) : e.value = i;
	},
	beforeUpdate(e, { value: t, oldValue: n, modifiers: { lazy: r, trim: i, number: a } }, o) {
		if (e[Na] = Aa(o), e.composing) return;
		let s = (a || e.type === "number") && !/^0\d/.test(e.value) ? ie(e.value) : e.value, c = t ?? "";
		if (s === c) return;
		let l = e.getRootNode();
		(l instanceof Document || l instanceof ShadowRoot) && l.activeElement === e && e.type !== "range" && (r && t === n || i && e.value.trim() === c) || (e.value = c);
	}
}, La = {
	created(e, { value: t }, n) {
		e.checked = I(t, n.props.value), e[Na] = Aa(n), ua(e, "change", () => {
			e[Na](Va(e));
		});
	},
	beforeUpdate(e, { value: t, oldValue: n }, r) {
		e[Na] = Aa(r), t !== n && (e.checked = I(t, r.props.value));
	}
}, Ra = {
	deep: !0,
	created(e, { value: t, modifiers: { number: n } }, r) {
		e._modelValue = t, ua(e, "change", () => {
			let t = Array.prototype.filter.call(e.options, (e) => e.selected).map((e) => n ? ie(Va(e)) : Va(e)), r = e.multiple, i = r ? p(e._modelValue) ? new Set(t) : t : t[0], a = e._pendingValue = [r, r ? d(i) ? t.slice() : t : i];
			try {
				e[Na](i);
			} finally {
				pn(() => {
					e._pendingValue === a && (e._pendingValue = void 0);
				});
			}
		}), e[Na] = Aa(r);
	},
	mounted(e, { value: t }) {
		Ba(e, t);
	},
	beforeUpdate(e, { value: t }, n) {
		e._modelValue = t, e[Na] = Aa(n);
	},
	updated(e, { value: t }) {
		let n = e._pendingValue;
		e._pendingValue = void 0, (!n || n[0] !== e.multiple || !za(t, n[1], n[0])) && Ba(e, t);
	}
};
function za(e, t, n) {
	if (!n || d(e)) return I(e, t);
	if (p(e)) {
		if (e.size !== t.length) return !1;
		for (let n of t) if (!e.has(n)) return !1;
		return !0;
	}
	return !1;
}
function Ba(e, t) {
	let n = e.multiple, r = d(t);
	if (!n || r || p(t)) {
		for (let i = 0, a = e.options.length; i < a; i++) {
			let a = e.options[i], o = Va(a);
			if (n) {
				if (r) {
					let e = typeof o;
					a.selected = e === "string" || e === "number" ? t.some((e) => String(e) === String(o)) : he(t, o) > -1;
				} else a.selected = t.has(o);
			} else if (I(Va(a), t)) {
				e.selectedIndex !== i && (e.selectedIndex = i);
				return;
			}
		}
		!n && e.selectedIndex !== -1 && (e.selectedIndex = -1);
	}
}
function Va(e) {
	return "_value" in e ? e._value : e.value;
}
var Ha = [
	"ctrl",
	"shift",
	"alt",
	"meta"
], Ua = {
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
	exact: (e, t) => Ha.some((n) => e[`${n}Key`] && !t.includes(n))
}, Wa = (e, t) => {
	if (!e) return e;
	let n = e._withMods ||= {}, r = t.join(".");
	return n[r] || (n[r] = ((n, ...r) => {
		for (let e = 0; e < t.length; e++) {
			let r = Ua[t[e]];
			if (r && r(n, t)) return;
		}
		return e(n, ...r);
	}));
}, Ga = /* @__PURE__ */ s({ patchProp: Sa }, Gi), Ka;
function qa() {
	return Ka ||= Rr(Ga);
}
var Ja = ((...e) => {
	qa().render(...e);
}), Ya = ((...e) => {
	let t = qa().createApp(...e), { mount: n } = t;
	return t.mount = (e) => {
		let r = Za(e);
		if (!r) return;
		let i = t._component;
		!h(i) && !i.render && !i.template && (i.template = r.innerHTML), r.nodeType === 1 && (r.textContent = "");
		let a = n(r, !1, Xa(r));
		return r instanceof Element && (r.removeAttribute("v-cloak"), r.setAttribute("data-v-app", "")), a;
	}, t;
});
function Xa(e) {
	if (e instanceof SVGElement) return "svg";
	if (typeof MathMLElement == "function" && e instanceof MathMLElement) return "mathml";
}
function Za(e) {
	return g(e) ? document.querySelector(e) : e;
}
//#endregion
//#region src/tabs.ts
var Qa = [
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
function $a(e, t) {
	let n = e.split(/[?#]/, 1)[0].replace(/\/+$/, "");
	return (n.startsWith(`${t}/`) ? n.slice(t.length) : n === t ? "" : n).replace(/^\//, "") || Qa[0].path;
}
var eo = {
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
}, to = {
	de: {
		unavailable: "Nicht verfügbar",
		unknown: "Unbekannt",
		disconnected: "Keine Verbindung zu Home Assistant.",
		loadFailed: "Die SAX Power Entitäten konnten nicht geladen werden.",
		forbidden: "Diese Entität kann derzeit nicht bedient werden.",
		invalid: "Bitte einen gültigen Wert im erlaubten Bereich eingeben.",
		failed: "Die Änderung ist fehlgeschlagen. Bitte den aktuellen Zustand prüfen und erneut versuchen.",
		bridgePvRequired: "Öffne in Schritt 1 „Bearbeiten“ und ergänze die Solarprognose. Die bisherige Ladeweise bleibt erhalten.",
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
		failed: "The change failed. Please check the current state and try again.",
		bridgePvRequired: "Open Edit in step 1 and add the solar forecast. The previous charging method is preserved.",
		bridgeTariffRequired: "First set up a time-of-use tariff with valid prices. The previous charging method is preserved.",
		on: "On",
		off: "Off"
	}
}, no = Symbol("sax-dashboard");
function ro(e) {
	return typeof e != "string" || e.length !== 5 && e.length !== 8 || !/^([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(e) ? null : e.length === 5 ? `${e}:00` : e;
}
function io(e, t, n, r, i) {
	let a = to[r];
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
function ao(e, t) {
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
			let e = ro(t);
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
function oo(e, t) {
	let n = Q(() => e()?.language.toLowerCase().startsWith("de") ? "de" : "en"), r = /* @__PURE__ */ Ht(null), i = /* @__PURE__ */ V(!1), a = /* @__PURE__ */ V(!1), o = /* @__PURE__ */ V(null), s = Q(() => o.value ? to[n.value][o.value] : null), c = /* @__PURE__ */ Ht([]), l = /* @__PURE__ */ At(/* @__PURE__ */ new Map()), u = /* @__PURE__ */ At(/* @__PURE__ */ new Map()), d = (e, n) => JSON.stringify([
		t(),
		e,
		n
	]), f = 0;
	function p(e = !0) {
		e && (f += 1), i.value = !1, r.value = null, c.value = [];
		for (let [e, t] of l) t.pending ? t.error = null : l.delete(e);
	}
	let m = U([
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
	xe(() => {
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
			displayValue: io(o, i, s, n.value, a.value),
			canControl: f && i.can_control && !!o?.callService,
			pending: p?.pending ?? !1,
			error: p?.error ? to[n.value][p.error] : null
		};
	}
	async function g(t, n, r) {
		let a = h(t, n);
		if (!a || a.pending) return !1;
		let o = /* @__PURE__ */ At({
			pending: !1,
			error: null
		});
		l.set(a.metadata.entity_id, o);
		let s = e();
		if (!a.canControl || !s?.callService || !i.value) return o.error = "forbidden", !1;
		let c = ao(a, r);
		if (!c) return o.error = "invalid", !1;
		o.pending = !0;
		let p = d(t, n);
		u.set(p, o);
		let m = f, g = () => m === f && l.get(a.metadata.entity_id) === o && h(t, n)?.metadata.entity_id === a.metadata.entity_id;
		try {
			return await s.callService(t, c.service, c.data, { entity_id: a.metadata.entity_id }, !1), g();
		} catch (e) {
			return g() && (o.error = "failed", t === "switch" && n === "bridge_charge_enabled" && e && typeof e == "object" && "translation_domain" in e && e.translation_domain === "sax_power" && "translation_key" in e && (e.translation_key === "bridge_pv_start_required" ? o.error = "bridgePvRequired" : e.translation_key === "bridge_tariff_required" && (o.error = "bridgeTariffRequired"))), !1;
		} finally {
			o.pending = !1, u.get(p) === o && u.delete(p);
		}
	}
	async function _(t, n, r) {
		let a = [`${t}_start`, `${t}_end`], o = a.map((e) => h("time", e));
		if (o.some((e) => e?.pending)) return !1;
		let s = /* @__PURE__ */ At({
			pending: !1,
			error: null
		});
		for (let e of o) e && l.set(e.metadata.entity_id, s);
		let c = o[0]?.metadata.device_id, p = e();
		if (!i.value || !p?.callService || !c || o.some((e) => !e?.canControl || e.metadata.device_id !== c)) return s.error = "forbidden", !1;
		let m = ro(n), g = ro(r);
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
	let v = 0, y = null, b = null;
	async function x(n) {
		let o = e(), s = t();
		if (!a.value) throw { code: "disconnected" };
		if (!i.value || !o?.callWS || !s) throw { code: "forbidden" };
		let c = f;
		if (!n && y?.generation === c) return y.promise;
		let l = ++v, u = o.callWS({
			type: `sax_power/dashboard/tariff/${n ? "tariff_type" in n ? "configure" : "save" : "get"}`,
			entry_id: s,
			...n
		}), d = (async () => {
			let e = await u;
			if (c !== f || !a.value) throw { code: "disconnected" };
			if (!e || typeof e.revision != "string") throw { code: "failed" };
			return !n && l !== v ? y?.generation === c ? y.promise : b?.generation === c && b.sequence !== l ? b.promise : r.value ?? e : (n && v++, r.value = e, e);
		})();
		n ? y = {
			generation: c,
			promise: d
		} : b = {
			generation: c,
			sequence: l,
			promise: d
		};
		try {
			return await d;
		} finally {
			y?.promise === d && (y = null), b?.promise === d && (b = null);
		}
	}
	async function S(n) {
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
	async function C(n) {
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
		ready: /* @__PURE__ */ Mt(i),
		connected: /* @__PURE__ */ Mt(a),
		error: s,
		entity: h,
		perform: g,
		performTimeWindow: _,
		tariff: Q(() => r.value),
		loadTariff: () => x(),
		saveTariff: (e) => x(e),
		configureTariff: (e) => x(e),
		loadTariffSeries: S,
		loadGridServingForecast: () => C(),
		saveGridServingForecast: (e) => C(e)
	};
}
//#endregion
//#region src/components/EntityControl.vue?vue&type=script&setup=true&lang.ts
var so = ["aria-busy"], co = { class: "entity-control__name" }, lo = [
	"checked",
	"indeterminate",
	"disabled"
], uo = { class: "entity-control__description" }, fo = { key: 0 }, po = { class: "entity-control__input" }, mo = [
	"checked",
	"disabled",
	"aria-describedby"
], ho = [
	"value",
	"disabled",
	"aria-describedby"
], go = {
	key: 0,
	value: "",
	disabled: ""
}, _o = ["value"], vo = [
	"value",
	"type",
	"min",
	"max",
	"step",
	"disabled",
	"aria-describedby",
	"aria-invalid"
], yo = ["disabled"], bo = {
	key: 0,
	class: "entity-control__error",
	role: "alert"
}, xo = {
	key: 1,
	role: "status"
}, So = ["aria-labelledby", "aria-describedby"], Co = ["id"], wo = ["id"], To = { class: "entity-control__confirmation-actions" }, Eo = ["disabled"], Do = /*@__PURE__*/ zn({
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
		let t = e, n = kn(no), r = Q(() => n?.entity(t.domain, t.entityKey)), i = Bn(), a = `sax-control-${i}`, o = `sax-status-${i}`, s = `sax-value-${i}`, c = /* @__PURE__ */ V(""), l = /* @__PURE__ */ V(), u = /* @__PURE__ */ Ht(null), d = Q(() => r.value?.state?.state ?? ""), f = Q(() => r.value?.state?.attributes ?? {}), p = Q(() => {
			let e = f.value.options;
			return Array.isArray(e) ? e.filter((e) => typeof e == "string") : [];
		}), m = Q(() => n?.language.value ?? "en"), h = Q(() => t.domain === "switch" ? o : `${s} ${o}`), g = Q(() => {
			let e = r.value?.displayValue;
			return t.timeUnit && t.domain === "time" && m.value === "de" && r.value?.available && /^(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(d.value) ? `${e} Uhr` : e;
		}), _ = Q(() => m.value === "de" ? {
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
		}), v = Q(() => !r.value?.canControl || r.value.pending || t.monthTile && d.value !== "on" && d.value !== "off"), y = Q(() => n?.connected.value ? !r.value?.available || t.monthTile && d.value !== "on" && d.value !== "off" ? _.value.unavailable : r.value.metadata.can_control ? r.value.pending ? _.value.pending : "" : _.value.readOnly : _.value.disconnected);
		function b(e) {
			return r.value?.available ? t.domain === "time" ? x(e) : e : "";
		}
		function x(e) {
			return /^(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(e) ? e.slice(0, 5) : "";
		}
		function S(e) {
			let n = e.target;
			c.value = t.domain === "time" ? x(n.value) : n.value, t.domain === "time" && (n.value = c.value);
		}
		U([() => r.value?.metadata.entity_id, () => d.value], ([, e]) => {
			c.value = b(e);
		}, { immediate: !0 });
		function C(e) {
			let t = f.value[e];
			return typeof t == "number" && Number.isFinite(t) ? t : void 0;
		}
		function w(e) {
			return r.value?.metadata.states[e] ?? e;
		}
		async function T() {
			v.value || !n || t.domain !== "number" && t.domain !== "time" || await n.perform(t.domain, t.entityKey, t.domain === "time" && c.value ? `${c.value}:00` : c.value);
		}
		function ee() {
			u.value = null, l.value?.open && l.value.close();
		}
		function E() {
			l.value?.open || (u.value = null);
		}
		U([
			() => r.value?.metadata.entity_id,
			d,
			v,
			() => t.domain,
			() => t.entityKey,
			() => t.confirmSwitch
		], ee, { flush: "sync" }), Zn(ee);
		async function D() {
			let e = u.value;
			ee(), e && !v.value && n && e.entityId === r.value?.metadata.entity_id && e.sourceState === d.value && e.domain === t.domain && e.key === t.entityKey && await n.perform(t.domain, t.entityKey, e.desired);
		}
		async function te(e) {
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
					u.value = e, await pn(), u.value === e && !v.value && l.value?.showModal();
					return;
				}
				await n.perform(t.domain, t.entityKey, a);
			}
		}
		async function O(e) {
			let r = e.target, i = r.value;
			r.value = d.value, !v.value && n && await n.perform(t.domain, t.entityKey, i);
		}
		return (t, n) => r.value ? (K(), q("form", {
			key: 0,
			class: de(["entity-control", {
				"entity-control--month": e.monthTile,
				"entity-control--selected": e.monthTile && r.value.available && d.value === "on"
			}]),
			"aria-busy": r.value.pending,
			onSubmit: Wa(T, ["prevent"])
		}, [
			e.monthTile && e.domain === "switch" ? (K(), q("label", {
				key: 0,
				for: a,
				class: "entity-control__switch-target entity-control__month-target"
			}, [J("span", co, L(e.label ?? r.value.name), 1), J("input", {
				id: a,
				type: "checkbox",
				role: "switch",
				checked: r.value.available && d.value === "on",
				indeterminate: !r.value.available || d.value !== "on" && d.value !== "off",
				disabled: v.value,
				"aria-describedby": o,
				onChange: te
			}, null, 40, lo)])) : (K(), q(G, { key: 1 }, [J("div", uo, [J("label", {
				for: a,
				class: "entity-control__name"
			}, L(e.label ?? r.value.name), 1), e.domain === "switch" ? Z("", !0) : (K(), q("p", {
				key: 0,
				id: s,
				class: "entity-control__value"
			}, [e.hideConfirmedLabel ? Z("", !0) : (K(), q("span", fo, L(_.value.confirmed) + ":", 1)), X(" " + L(g.value), 1)]))]), J("div", po, [e.domain === "switch" ? (K(), q("label", {
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
				onChange: te
			}, null, 40, mo)])) : e.domain === "select" ? (K(), q("select", {
				key: 1,
				id: a,
				value: r.value.available ? d.value : "",
				disabled: v.value,
				"aria-describedby": h.value,
				onChange: O
			}, [r.value.available ? Z("", !0) : (K(), q("option", go, L(_.value.unavailable), 1)), (K(!0), q(G, null, W(p.value, (e) => (K(), q("option", {
				key: e,
				value: e
			}, L(w(e)), 9, _o))), 128))], 40, ho)) : (K(), q(G, { key: 2 }, [J("input", {
				id: a,
				value: c.value,
				type: e.domain === "number" ? "number" : "time",
				min: e.domain === "number" ? C("min") : void 0,
				max: e.domain === "number" ? C("max") : void 0,
				step: e.domain === "number" ? C("step") : 60,
				disabled: v.value,
				"aria-describedby": h.value,
				"aria-invalid": !!r.value.error,
				required: "",
				onInput: S,
				onInvalid: Wa(T, ["prevent"])
			}, null, 40, vo), J("button", {
				type: "submit",
				disabled: v.value || e.domain === "time" && c.value === ""
			}, L(_.value.apply), 9, yo)], 64))])], 64)),
			J("div", {
				id: o,
				class: "entity-control__feedback"
			}, [r.value.error ? (K(), q("p", bo, L(r.value.error), 1)) : y.value ? (K(), q("p", xo, L(y.value), 1)) : Z("", !0)]),
			e.confirmSwitch ? (K(), q("dialog", {
				key: 2,
				ref_key: "dialog",
				ref: l,
				class: "entity-control__confirmation",
				"aria-labelledby": `${H(i)}-confirmation-title`,
				"aria-describedby": `${H(i)}-confirmation-question`,
				onCancel: Wa(ee, ["prevent"]),
				onClose: E
			}, [
				J("h3", { id: `${H(i)}-confirmation-title` }, L(_.value.confirmationTitle), 9, Co),
				J("p", { id: `${H(i)}-confirmation-question` }, L(_.value.confirmationQuestion), 9, wo),
				J("div", To, [J("button", {
					type: "button",
					autofocus: "",
					onClick: ee
				}, L(_.value.cancel), 1), J("button", {
					type: "button",
					disabled: v.value || !u.value,
					onClick: D
				}, L(u.value?.desired ? _.value.turnOn : _.value.turnOff), 9, Eo)])
			], 40, So)) : Z("", !0)
		], 42, so)) : Z("", !0);
	}
}), Oo = ".entity-control{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));color:var(--primary-text-color,#212121);box-shadow:var(--ha-card-box-shadow,none);flex-wrap:wrap;align-items:center;gap:12px 24px;padding:20px;display:flex}.entity-control__description{overflow-wrap:anywhere;flex:200px;min-width:0}.entity-control__name{font-weight:500;line-height:1.5;display:block}.entity-control__value{color:var(--secondary-text-color,#666);margin:4px 0 0;font-size:.9em;line-height:1.5}.entity-control__input{flex-wrap:wrap;align-items:center;gap:8px;max-width:100%;display:flex}.entity-control__switch-target{cursor:pointer;justify-content:center;align-items:center;min-width:44px;min-height:44px;display:flex}.entity-control__switch-target:has(:disabled){cursor:not-allowed}.entity-control input,.entity-control select,.entity-control button{border:1px solid var(--divider-color,#767676);max-width:100%;min-height:44px;color:inherit;background:var(--card-background-color,#fff);font:inherit;border-radius:6px;padding:8px 12px}.entity-control input[type=number]{width:120px}.entity-control input[type=checkbox]{width:22px;height:22px;min-height:22px;accent-color:var(--primary-color,#03a9f4);cursor:pointer;flex-shrink:0;margin:0;padding:0}.entity-control button{border-color:var(--primary-color,#03a9f4);color:var(--primary-text-color,#212121);cursor:pointer}.entity-control :disabled{cursor:not-allowed;opacity:.6}.entity-control input:focus-visible,.entity-control select:focus-visible,.entity-control button:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.entity-control__feedback{color:var(--secondary-text-color,#666);flex-basis:100%;line-height:1.5}.entity-control__feedback:empty{display:none}.entity-control__feedback p{margin:0}.entity-control__error{color:var(--error-color,#b71c1c)}.entity-control__confirmation{border:1px solid var(--divider-color,#767676);background:var(--card-background-color,#fff);width:min(440px,100vw - 32px);max-height:calc(100vh - 32px);color:var(--primary-text-color,#212121);border-radius:12px;padding:24px;overflow:auto}.entity-control__confirmation::backdrop{background:#0000008c}.entity-control__confirmation h3{margin:0;font-size:20px;line-height:1.4}.entity-control__confirmation p{margin:16px 0 24px;line-height:1.6}.entity-control__confirmation-actions{flex-wrap:wrap;justify-content:flex-end;gap:12px;display:flex}@container sax-content (width>=860px){.entity-control{gap:8px 12px;padding:14px}.entity-control__description{flex-basis:140px}.entity-control__value{margin-top:2px;font-size:14px}.entity-control input[type=number]{width:104px}}", ko = (e, t) => {
	let n = e.__vccOpts || e;
	for (let [e, r] of t) n[e] = r;
	return n;
}, Ao = /*#__PURE__*/ ko(Do, [["styles", [Oo]]]), jo = [
	"role",
	"aria-labelledby",
	"aria-valuemin",
	"aria-valuemax",
	"aria-valuenow",
	"aria-valuetext"
], Mo = {
	viewBox: "0 0 240 124",
	"aria-hidden": "true"
}, No = ["stroke-dasharray", "stroke-dashoffset"], Po = ["transform"], Fo = {
	class: "entity-gauge__scale",
	"aria-hidden": "true"
}, Io = { class: "entity-gauge__value" }, Lo = {
	key: 0,
	class: "entity-gauge__range"
}, Ro = /*#__PURE__*/ ko(/* @__PURE__ */ zn({
	__name: "EntityGauge",
	props: {
		entityKey: { type: String },
		maximum: { type: Number },
		segments: { type: Array }
	},
	setup(e) {
		let t = e, n = kn(no), r = Q(() => n?.entity("sensor", t.entityKey)), i = `sax-gauge-${Bn()}`, a = Q(() => {
			let e = r.value?.state?.state.trim();
			if (!r.value?.available || !e) return null;
			let t = Number(e);
			return Number.isFinite(t) ? t : null;
		}), o = Q(() => a.value === null ? null : Math.max(0, Math.min(t.maximum, a.value))), s = Q(() => a.value === null ? null : [...t.segments].reverse().find((e) => a.value >= e.from)?.label ?? t.segments[0]?.label), c = Q(() => r.value?.available && a.value === null ? n?.language.value === "de" ? "Unbekannt" : "Unknown" : r.value?.displayValue), l = Q(() => t.segments.map((e, n) => ({
			...e,
			offset: -(e.from / t.maximum) * 100,
			length: ((t.segments[n + 1]?.from ?? t.maximum) - e.from) / t.maximum * 100
		})));
		return (t, n) => r.value ? (K(), q("section", {
			key: 0,
			class: "entity-gauge",
			"aria-labelledby": i
		}, [J("h2", { id: i }, L(r.value.name), 1), J("div", {
			class: "entity-gauge__meter",
			role: o.value === null ? void 0 : "meter",
			"aria-labelledby": o.value === null ? void 0 : i,
			"aria-valuemin": o.value === null ? void 0 : 0,
			"aria-valuemax": o.value === null ? void 0 : e.maximum,
			"aria-valuenow": o.value ?? void 0,
			"aria-valuetext": o.value === null ? void 0 : `${c.value} · ${s.value}`
		}, [
			(K(), q("svg", Mo, [n[1] ||= J("path", {
				class: "entity-gauge__track",
				d: "M20 110 A100 100 0 0 1 220 110"
			}, null, -1), o.value === null ? Z("", !0) : (K(), q(G, { key: 0 }, [
				(K(!0), q(G, null, W(l.value, (e) => (K(), q("path", {
					key: e.from,
					class: de(["entity-gauge__segment", `entity-gauge__segment--${e.color}`]),
					d: "M20 110 A100 100 0 0 1 220 110",
					pathLength: "100",
					"stroke-dasharray": `${e.length} 100`,
					"stroke-dashoffset": e.offset
				}, null, 10, No))), 128)),
				J("line", {
					class: "entity-gauge__needle",
					x1: "120",
					y1: "110",
					x2: "120",
					y2: "33",
					transform: `rotate(${o.value / e.maximum * 180 - 90} 120 110)`
				}, null, 8, Po),
				n[0] ||= J("circle", {
					class: "entity-gauge__pivot",
					cx: "120",
					cy: "110",
					r: "5"
				}, null, -1)
			], 64))])),
			J("div", Fo, [n[2] ||= J("span", null, "0", -1), J("span", null, L(e.maximum), 1)]),
			J("p", Io, L(c.value), 1),
			s.value ? (K(), q("p", Lo, L(s.value), 1)) : Z("", !0)
		], 8, jo)])) : Z("", !0);
	}
}), [["styles", [".entity-gauge{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);text-align:center;padding:24px}.entity-gauge h2{overflow-wrap:anywhere;margin:0 0 20px;font-size:16px;font-weight:500;line-height:1.5}.entity-gauge__meter{max-width:260px;margin:0 auto}.entity-gauge svg{fill:none;width:100%;display:block}.entity-gauge__track,.entity-gauge__segment{stroke-width:15px;stroke-linecap:butt}.entity-gauge__track{stroke:var(--divider-color,#e0e0e0)}.entity-gauge__segment--red{stroke:var(--error-color,#db4437)}.entity-gauge__segment--yellow{stroke:var(--warning-color,#f4b400)}.entity-gauge__segment--green{stroke:var(--success-color,#0f9d58)}.entity-gauge__needle{stroke:var(--primary-text-color,#212121);stroke-width:3px;stroke-linecap:round}.entity-gauge__pivot{stroke:none;fill:var(--primary-text-color,#212121)}.entity-gauge__scale{color:var(--secondary-text-color,#666);justify-content:space-between;padding:2px 7px;font-size:12px;display:flex}.entity-gauge__value{overflow-wrap:anywhere;margin:10px 0 0;font-size:28px;font-weight:500;line-height:1.4}.entity-gauge__range{color:var(--secondary-text-color,#666);margin:4px 0 0;font-size:14px;line-height:1.5}@container sax-content (width>=860px){.entity-gauge{padding:16px}.entity-gauge h2{margin-bottom:8px}.entity-gauge__meter{max-width:180px}.entity-gauge__value{margin-top:6px;font-size:24px}.entity-gauge__range{margin-top:2px}}"]]]), zo = {
	key: 0,
	class: "entity-value"
}, Bo = { class: "entity-value__name" }, Vo = { class: "entity-value__state" }, Ho = /*#__PURE__*/ ko(/* @__PURE__ */ zn({
	__name: "EntityValue",
	props: {
		domain: { type: null },
		entityKey: { type: String }
	},
	setup(e) {
		let t = e, n = kn(no), r = Q(() => n?.entity(t.domain, t.entityKey));
		return (e, t) => r.value ? (K(), q("div", zo, [J("span", Bo, L(r.value.name), 1), J("span", Vo, L(r.value.displayValue), 1)])) : Z("", !0);
	}
}), [["styles", [".entity-value{color:var(--primary-text-color,#212121);overflow-wrap:anywhere;flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:8px 20px;line-height:1.5;display:flex}.entity-value__name{color:var(--secondary-text-color,#666)}.entity-value__state{font-weight:500}"]]]), Uo = { class: "general-view" }, Wo = {
	key: 0,
	class: "general-view__status",
	role: "status"
}, Go = {
	key: 1,
	class: "general-view__status",
	role: "status"
}, Ko = {
	key: 2,
	class: "general-view__gauges"
}, qo = ["aria-labelledby"], Jo = ["id"], Yo = { class: "general-view__rows" }, Xo = /*#__PURE__*/ ko(/* @__PURE__ */ zn({
	__name: "GeneralView",
	setup(e) {
		let t = kn(no), n = Bn(), r = Q(() => t?.language.value === "de" ? {
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
		}], a = Q(() => i.map((e) => ({
			...e,
			entities: e.entities.filter(([e, n]) => t?.entity(e, n))
		})).filter((e) => e.entities.length)), o = Q(() => !!(t?.entity("sensor", "soc") || t?.entity("sensor", "storage_max_cell_temp"))), s = Q(() => o.value || a.value.length > 0);
		return (e, i) => (K(), q("div", Uo, [
			!H(t)?.ready.value && !H(t)?.error.value ? (K(), q("p", Wo, L(r.value.loading), 1)) : H(t)?.ready.value && !s.value ? (K(), q("p", Go, L(r.value.empty), 1)) : Z("", !0),
			o.value ? (K(), q("div", Ko, [Y(Ro, {
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
			}, null, 8, ["segments"]), Y(Ro, {
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
			(K(!0), q(G, null, W(a.value, (e) => (K(), q("section", {
				key: e.title,
				class: de(["general-view__card", `general-view__card--${e.title}`]),
				"aria-labelledby": `${H(n)}-${e.title}`
			}, [J("h2", { id: `${H(n)}-${e.title}` }, L(r.value[e.title]), 9, Jo), J("div", Yo, [(K(!0), q(G, null, W(e.entities, ([e, t]) => (K(), q(G, { key: `${e}.${t}` }, [e === "number" || e === "switch" ? (K(), ai(Ao, {
				key: 0,
				domain: e,
				"entity-key": t,
				"confirm-switch": e === "switch" && t === "storage_switch"
			}, null, 8, [
				"domain",
				"entity-key",
				"confirm-switch"
			])) : (K(), ai(Ho, {
				key: 1,
				domain: e,
				"entity-key": t
			}, null, 8, ["domain", "entity-key"]))], 64))), 128))])], 10, qo))), 128))
		]));
	}
}), [["styles", [".general-view{gap:20px;min-width:0;margin-top:24px;display:grid}.general-view__gauges{grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr));gap:20px;display:grid}.general-view__card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.general-view__card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.general-view__rows{gap:16px;display:grid}.general-view__rows .entity-control{border:0;border-bottom:1px solid var(--divider-color,#e0e0e0);box-shadow:none;border-radius:0;padding:0 0 16px}.general-view__rows .entity-control:last-child{border-bottom:0;padding-bottom:0}.general-view__status{color:var(--secondary-text-color,#666);margin:0;line-height:1.6}@container sax-content (width>=860px){.general-view{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;gap:16px;margin-top:16px}.general-view__gauges{grid-column:1;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.general-view__gauges:has(>:only-child){grid-template-columns:minmax(0,1fr)}.general-view__card{padding:18px}.general-view__card--power{grid-column:1}.general-view__card--device{grid-area:1/2/span 2}:is(.general-view:not(:has(.general-view__gauges)) .general-view__card--device,.general-view:not(:has(.general-view__card--power)) .general-view__card--device){grid-row:1}:is(.general-view:has(>:only-child),.general-view:not(:has(.general-view__card--device))){grid-template-columns:minmax(0,1fr)}.general-view__card:only-child{grid-area:auto}.general-view__card h2{margin-bottom:12px;font-size:16px}.general-view__rows{gap:10px}.general-view__rows .entity-control{padding:0 0 10px}.general-view__rows .entity-control:last-child{padding-bottom:0}.general-view__status{grid-column:1/-1}}@media (max-width:600px){.general-view,.general-view__gauges{gap:16px}.general-view__card{padding:20px}}"]]]), Zo = ["aria-busy"], Qo = { class: "month-selection__header" }, $o = {
	class: "month-selection__overview",
	"aria-live": "polite",
	"aria-atomic": "true"
}, es = { class: "month-selection__summary" }, ts = { class: "month-selection__count" }, ns = ["aria-expanded"], rs = { class: "month-selection__feedback" }, is = {
	key: 0,
	role: "status"
}, as = {
	key: 1,
	role: "status"
}, os = {
	key: 2,
	role: "status"
}, ss = {
	key: 3,
	role: "status"
}, cs = { class: "month-selection__hint" }, ls = { class: "month-selection__quarters" }, us = { class: "month-selection__options" }, ds = {
	key: 1,
	class: "month-selection__missing"
}, fs = { class: "month-selection__missing-target" }, ps = ["aria-describedby"], ms = ["id"], hs = /*#__PURE__*/ ko(/* @__PURE__ */ zn({
	__name: "MonthSelection",
	props: { entityKeys: { type: Array } },
	setup(e) {
		let t = e, n = kn(no), r = /* @__PURE__ */ V(!1), i = `sax-months-${Bn()}`, a = Q(() => n?.language.value ?? "en"), o = Q(() => a.value === "de" ? {
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
		}), s = Q(() => {
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
		}), c = Q(() => Array.from({ length: 4 }, (e, t) => ({
			index: t,
			name: a.value === "de" ? `${t + 1}. Quartal` : `Q${t + 1}`,
			months: s.value.slice(t * 3, t * 3 + 3)
		}))), l = Q(() => s.value.filter((e) => e.selected).length), u = Q(() => s.value.filter((e) => !e.known)), d = Q(() => {
			if (l.value === 12) return o.value.allYear;
			if (!l.value) return u.value.length ? o.value.incomplete : o.value.none;
			let e = [], t, n;
			function r() {
				t && n && e.push(t.index === n.index ? t.name : `${t.name}–${n.name}`), t = void 0, n = void 0;
			}
			for (let e of s.value) e.selected ? (t ??= e, n = e) : r();
			return r(), e.join(", ");
		}), f = Q(() => {
			let e = l.value, t = u.value.length;
			return t ? a.value === "de" ? `${e} ausgewählt · ${t} unklar` : `${e} selected · ${t} unknown` : a.value === "de" ? `${e} von 12 Monaten ausgewählt` : `${e} of 12 months selected`;
		}), p = Q(() => s.value.some((e) => e.entity?.pending)), m = Q(() => s.value.flatMap((e) => e.entity?.error ? [`${e.name}: ${e.entity.error}`] : [])), h = Q(() => s.value.filter((e) => e.known && !e.entity?.metadata.can_control));
		return (e, t) => (K(), q("div", {
			class: "month-selection",
			"aria-busy": p.value
		}, [
			J("div", Qo, [J("div", $o, [J("p", es, L(d.value), 1), J("p", ts, L(f.value), 1)]), J("button", {
				type: "button",
				class: "month-selection__toggle",
				"aria-expanded": r.value,
				"aria-controls": i,
				onClick: t[0] ||= (e) => r.value = !r.value
			}, [X(L(r.value ? o.value.close : o.value.edit) + " ", 1), (K(), q("svg", {
				viewBox: "0 0 24 24",
				width: "18",
				height: "18",
				"aria-hidden": "true",
				class: de({ "month-selection__chevron--expanded": r.value })
			}, [...t[1] ||= [J("path", { d: "m6 9 6 6 6-6" }, null, -1)]], 2))], 8, ns)]),
			J("div", rs, [
				r.value ? Z("", !0) : (K(), q(G, { key: 0 }, [(K(!0), q(G, null, W(m.value, (e) => (K(), q("p", {
					key: e,
					class: "month-selection__error",
					role: "alert"
				}, L(e), 1))), 128)), p.value ? (K(), q("p", is, L(o.value.pending), 1)) : Z("", !0)], 64)),
				H(n)?.connected.value ? Z("", !0) : (K(), q("p", as, L(o.value.disconnected), 1)),
				u.value.length ? (K(), q("p", os, L(o.value.unknown) + ": " + L(u.value.map((e) => e.name).join(", ")), 1)) : Z("", !0),
				h.value.length ? (K(), q("p", ss, L(o.value.readOnly) + ": " + L(h.value.map((e) => e.name).join(", ")), 1)) : Z("", !0)
			]),
			En(J("div", {
				id: i,
				class: "month-selection__details"
			}, [J("p", cs, L(o.value.hint), 1), J("div", ls, [(K(!0), q(G, null, W(c.value, (e) => (K(), q("fieldset", {
				key: e.index,
				class: "month-selection__quarter"
			}, [J("legend", null, L(e.name), 1), J("div", us, [(K(!0), q(G, null, W(e.months, (e) => (K(), q(G, { key: e.index }, [e.entity && e.key ? (K(), ai(Ao, {
				key: 0,
				domain: "switch",
				"entity-key": e.key,
				"month-tile": ""
			}, null, 8, ["entity-key"])) : (K(), q("div", ds, [J("label", fs, [J("span", null, L(e.name), 1), J("input", {
				type: "checkbox",
				role: "switch",
				disabled: "",
				indeterminate: !0,
				"aria-describedby": `${i}-${e.index}-missing`
			}, null, 8, ps)]), J("p", { id: `${i}-${e.index}-missing` }, L(o.value.unavailable), 9, ms)]))], 64))), 128))])]))), 128))])], 512), [[Xi, r.value]])
		], 8, Zo));
	}
}), [["styles", [".month-selection{min-width:0}.month-selection__header{flex-wrap:wrap;justify-content:space-between;align-items:center;gap:16px;display:flex}.month-selection__overview{overflow-wrap:anywhere;flex:180px;min-width:0}.month-selection__summary{margin:0;font-size:16px;font-weight:500;line-height:1.5}.month-selection__count,.month-selection__hint{color:var(--secondary-text-color,#666);margin:4px 0 0;font-size:14px;line-height:1.5}.month-selection__toggle{border:1px solid var(--divider-color,#e0e0e0);background:var(--card-background-color,#fff);min-height:44px;color:var(--primary-text-color,#212121);font:inherit;cursor:pointer;border-radius:8px;flex-shrink:0;justify-content:center;align-items:center;gap:8px;padding:8px 12px;font-size:14px;display:inline-flex}.month-selection__toggle:hover{background:var(--secondary-background-color,#f5f5f5)}:is(.month-selection__toggle:focus-visible,.month-selection .entity-control__month-target:has(input:focus-visible)){outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.month-selection__toggle svg{fill:none;stroke:currentColor;stroke-width:2px;stroke-linecap:round;stroke-linejoin:round}.month-selection__chevron--expanded{transform:rotate(180deg)}.month-selection__details{border-top:1px solid var(--divider-color,#e0e0e0);margin-top:16px;padding-top:16px}.month-selection__hint{margin:0 0 16px}.month-selection__quarters{grid-template-columns:minmax(0,1fr);gap:16px;display:grid}.month-selection__quarter{border:0;min-width:0;margin:0;padding:0}.month-selection__quarter legend{color:var(--secondary-text-color,#666);margin-bottom:8px;padding:0;font-size:13px;font-weight:500}.month-selection__options{grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;display:grid}.month-selection .entity-control.entity-control--month,.month-selection__missing{border:1px solid var(--divider-color,#e0e0e0);background:var(--card-background-color,#fff);border-radius:8px;flex-flow:column;align-items:stretch;gap:0;min-width:0;padding:0;display:flex}.month-selection .entity-control.entity-control--selected{border-color:color-mix(in srgb, var(--primary-color,#03a9f4) 55%, var(--divider-color,#e0e0e0));background:color-mix(in srgb, var(--primary-color,#03a9f4) 12%, var(--card-background-color,#fff))}.month-selection .entity-control__month-target,.month-selection__missing-target{cursor:pointer;border-radius:7px;flex-direction:column-reverse;flex:auto;justify-content:center;align-items:center;gap:8px;min-height:44px;padding:10px 6px;display:flex}.month-selection__missing-target{cursor:not-allowed}.month-selection .entity-control__month-target:has(:disabled){cursor:not-allowed}.month-selection .entity-control__name,.month-selection__missing-target span{text-align:center;overflow-wrap:anywhere;min-width:0;max-width:100%;font-size:14px;font-weight:500;line-height:1.4}.month-selection__missing input[type=checkbox]{width:22px;height:22px;min-height:22px;accent-color:var(--primary-color,#03a9f4);flex-shrink:0;margin:0;padding:0}.month-selection .entity-control__feedback,.month-selection__missing p{overflow-wrap:anywhere;min-width:0;color:var(--secondary-text-color,#666);flex:none;margin:0;padding:0 12px 10px;font-size:13px;line-height:1.5}.month-selection__feedback{color:var(--secondary-text-color,#666);overflow-wrap:anywhere;gap:8px;margin-top:12px;font-size:14px;line-height:1.5;display:grid}.month-selection__feedback:empty{display:none}.month-selection__feedback p{margin:0}.month-selection__error{color:var(--error-color,#b71c1c)}@container sax-content (width>=600px){.month-selection__quarters{grid-template-columns:repeat(2,minmax(0,1fr))}}"]]]);
//#endregion
//#region src/time.ts
function gs(e) {
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
var _s = ["aria-busy"], vs = { class: "time-window-control__inputs" }, ys = ["for"], bs = [
	"id",
	"name",
	"value",
	"disabled",
	"aria-invalid",
	"aria-describedby",
	"onInput",
	"onChange",
	"onBlur"
], xs = ["disabled"], Ss = ["id"], Cs = ["id"], ws = ["aria-label"], Ts = [
	"disabled",
	"aria-label",
	"aria-valuenow",
	"aria-valuetext",
	"aria-describedby",
	"onKeydown",
	"onPointerdown"
], Es = {
	class: "time-window-control__marker-label",
	"aria-hidden": "true"
}, Ds = { class: "time-window-control__duration" }, Os = ["id"], ks = ["id"], As = {
	key: 0,
	class: "time-window-control__error",
	role: "alert"
}, js = {
	key: 1,
	role: "status"
}, Ms = /*#__PURE__*/ ko(/* @__PURE__ */ zn({
	__name: "TimeWindowControl",
	props: { kind: { type: String } },
	setup(e) {
		let t = e, n = kn(no), r = Q(() => n?.entity("time", `${t.kind}_start`)), i = Q(() => n?.entity("time", `${t.kind}_end`)), a = `sax-window-${Bn()}`, o = Q(() => n?.language.value ?? "en"), s = Q(() => o.value === "de" ? {
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
		}), c = /* @__PURE__ */ V(""), l = /* @__PURE__ */ V(""), u = /* @__PURE__ */ V(!1), d = /* @__PURE__ */ V(), f = /* @__PURE__ */ V(), p = /* @__PURE__ */ V(null), m = /* @__PURE__ */ V(!1), h = /* @__PURE__ */ V(!1), g = /* @__PURE__ */ V(!1), _ = 0, v = null;
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
		let S = Q(() => r.value?.state?.state ?? ""), C = Q(() => i.value?.state?.state ?? ""), w = Q(() => !!r.value?.available && !!i.value?.available && $(S.value) !== null && $(C.value) !== null), T = Q(() => typeof r.value?.metadata.device_id == "string" && r.value.metadata.device_id.length > 0 && r.value.metadata.device_id === i.value?.metadata.device_id), ee = Q(() => w.value ? `${b(S.value)} – ${b(C.value)}${s.value.unit ? ` ${s.value.unit}` : ""}` : [r.value, i.value].map((e) => e?.available && $(e.state?.state ?? "") !== null ? `${b(e.state.state)}${s.value.unit ? ` ${s.value.unit}` : ""}` : s.value.missingValue).join(" – ")), E = Q(() => $(c.value) !== null && $(l.value) !== null), D = Q(() => u.value && ($(c.value) !== $(S.value) || $(l.value) !== $(C.value))), te = Q(() => m.value || !!r.value?.pending || !!i.value?.pending), O = Q(() => !n?.ready.value || !n.connected.value || !w.value || !T.value || !r.value?.canControl || !i.value?.canControl || te.value), ne = Q(() => p.value ? `${ae.value.find((e) => e.key === p.value).name}: ${s.value.invalid}` : r.value?.error || i.value?.error), re = Q(() => n?.connected.value ? w.value ? T.value ? !r.value?.canControl || !i.value?.canControl ? s.value.readOnly : te.value ? s.value.pending : h.value ? s.value.awaiting : g.value ? s.value.changed : "" : s.value.incompatible : s.value.unavailable : s.value.disconnected), k = Q(() => u.value || !w.value ? c.value : S.value), A = Q(() => u.value || !w.value ? l.value : C.value), j = Q(() => {
			let e = $(k.value), t = $(A.value);
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
		}), ie = Q(() => {
			let e = $(k.value), t = $(A.value);
			return e === null || t === null || e === t ? [] : (t > e ? [[e, t]] : [[e, 86400], [0, t]]).filter(([e, t]) => e !== t).map(([e, t]) => ({
				left: `${e / 864}%`,
				width: `${(t - e) / 864}%`
			}));
		}), ae = Q(() => [{
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
		U([
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
		}), U(O, (e) => {
			e && oe();
		}, { flush: "sync" }), Zn(oe);
		function se(e, t) {
			O.value || (e === "start" ? c.value = t : l.value = t, p.value === e && (p.value = null), u.value = !0, h.value = !1, g.value = !1);
		}
		function ce(e, t) {
			let n = t.target;
			se(e, n.value);
		}
		function le(e) {
			let t = gs(e);
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
		function N(e) {
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
		function P(e) {
			if (!v || v.pointerId !== e.pointerId || O.value || !d.value) return;
			let t = d.value.getBoundingClientRect();
			if (t.width <= 0 || !v.moved && e.clientX === v.originX) return;
			let n = Math.max(0, Math.min(1439, Math.round(v.originSeconds / 60 + (e.clientX - v.originX) / t.width * 1440)));
			v.moved = !0, se(v.boundary, y(n * 60).slice(0, 5));
		}
		function F(e, t) {
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
		function pe(e) {
			v?.pointerId === e.pointerId && (v.moved && P(e), oe());
		}
		async function me() {
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
		return (e, t) => r.value || i.value ? (K(), q("form", {
			key: 0,
			ref_key: "form",
			ref: f,
			class: "time-window-control",
			"aria-busy": te.value,
			onSubmit: Wa(me, ["prevent"])
		}, [
			J("div", vs, [(K(!0), q(G, null, W(ae.value, (e) => (K(), q("label", {
				key: e.key,
				for: `${a}-${e.key}`,
				class: "time-window-control__field"
			}, [J("span", null, [X(L(e.name), 1), s.value.unit ? (K(), q(G, { key: 0 }, [X(" (" + L(s.value.unit) + ")", 1)], 64)) : Z("", !0)]), J("input", {
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
				onChange: (t) => N(e.key),
				onBlur: (t) => N(e.key)
			}, null, 40, bs)], 8, ys))), 128)), J("button", {
				class: "time-window-control__apply",
				type: "submit",
				disabled: O.value
			}, L(s.value.apply), 9, xs)]),
			J("p", {
				id: `${a}-time-hint`,
				class: "time-window-control__hint"
			}, L(s.value.timeHint), 9, Ss),
			J("p", {
				id: `${a}-confirmed`,
				class: "time-window-control__confirmed"
			}, L(s.value.confirmed) + ": " + L(ee.value), 9, Cs),
			J("div", {
				class: "time-window-control__timeline",
				"aria-label": s.value.timeline,
				role: "group"
			}, [J("div", {
				ref_key: "rail",
				ref: d,
				class: de(["time-window-control__rail", { "time-window-control__rail--draft": D.value }])
			}, [(K(!0), q(G, null, W(ie.value, (e, t) => (K(), q("span", {
				key: t,
				class: "time-window-control__segment",
				style: M(e)
			}, null, 4))), 128))], 2), (K(!0), q(G, null, W(ae.value, (e) => (K(), q("button", {
				key: e.key,
				type: "button",
				role: "slider",
				class: de(["time-window-control__handle", `time-window-control__handle--${e.key}`]),
				style: M({ left: `${(H($)(e.value) ?? 0) / 864}%` }),
				disabled: O.value || !E.value,
				"aria-label": e.marker,
				"aria-valuemin": "0",
				"aria-valuemax": "86340",
				"aria-valuenow": H($)(e.value) ?? 0,
				"aria-valuetext": `${b(e.value)}${s.value.unit ? ` ${s.value.unit}` : ""}`,
				"aria-describedby": `${a}-help ${a}-confirmed`,
				"aria-orientation": "horizontal",
				onKeydown: (t) => fe(e.key, t),
				onPointerdown: (t) => F(e.key, t),
				onPointermove: P,
				onPointerup: pe,
				onPointercancel: oe,
				onLostpointercapture: oe
			}, [J("span", Es, L(e.shortName), 1), t[0] ||= J("span", {
				class: "time-window-control__marker-dot",
				"aria-hidden": "true"
			}, null, -1)], 46, Ts))), 128))], 8, ws),
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
			J("p", Ds, [J("span", null, L(D.value ? s.value.draft : s.value.duration) + ":", 1), X(" " + L(j.value), 1)]),
			J("p", {
				id: `${a}-help`,
				class: "time-window-control__sr-only"
			}, L(s.value.help), 9, Os),
			J("div", {
				id: `${a}-status`,
				class: "time-window-control__feedback"
			}, [ne.value ? (K(), q("p", As, L(ne.value), 1)) : re.value ? (K(), q("p", js, L(re.value), 1)) : Z("", !0)], 8, ks)
		], 40, _s)) : Z("", !0);
	}
}), [["styles", [".time-window-control{min-width:0;color:var(--primary-text-color,#212121)}.time-window-control__inputs{flex-wrap:wrap;align-items:end;gap:10px;display:flex}.time-window-control__field{flex:136px;gap:5px;min-width:0;font-size:14px;display:grid}.time-window-control__field input,.time-window-control__apply{box-sizing:border-box;border:1px solid var(--divider-color,#767676);min-width:0;max-width:100%;min-height:44px;color:inherit;background:var(--card-background-color,#fff);font:inherit;border-radius:6px;padding:8px 10px;font-size:16px}.time-window-control__field input{width:100%}.time-window-control__field input[aria-invalid=true]{border-color:var(--error-color,#db4437)}.time-window-control__apply{border-color:var(--primary-color,#03a9f4);cursor:pointer;flex:none}.time-window-control__hint,.time-window-control__confirmed,.time-window-control__duration{color:var(--secondary-text-color,#666);overflow-wrap:anywhere;margin:9px 0 0;font-size:14px;line-height:1.5}.time-window-control__timeline{height:94px;margin:6px 22px 0;position:relative}.time-window-control__rail{background:var(--divider-color,#ddd);border-radius:3px;height:6px;position:absolute;top:44px;left:0;right:0;overflow:hidden}.time-window-control__segment{background:var(--primary-color,#03a9f4);height:100%;position:absolute}.time-window-control__rail--draft .time-window-control__segment{background-image:repeating-linear-gradient(135deg,#0000 0 5px,#ffffff3d 5px 8px)}.time-window-control__handle{width:44px;height:44px;min-height:0;color:inherit;font:inherit;cursor:ew-resize;touch-action:none;background:0 0;border:0;border-radius:6px;padding:0;display:block;position:absolute;transform:translate(-50%)}.time-window-control__handle--start{top:0}.time-window-control__handle--end{top:50px}.time-window-control__marker-label{white-space:nowrap;width:max-content;font-size:12px;line-height:16px;position:absolute;left:50%;transform:translate(-50%)}.time-window-control__handle--start .time-window-control__marker-label{top:0}.time-window-control__handle--end .time-window-control__marker-label{bottom:0}.time-window-control__marker-dot{box-sizing:border-box;border:2px solid var(--primary-color,#03a9f4);background:var(--card-background-color,#fff);border-radius:50%;width:18px;height:18px;position:absolute;left:13px}.time-window-control__handle--start .time-window-control__marker-dot{bottom:3px}.time-window-control__handle--end .time-window-control__marker-dot{top:3px}.time-window-control__marker-dot:after{content:\"\";background:var(--primary-color,#03a9f4);width:2px;height:6px;position:absolute;left:6px}.time-window-control__handle--start .time-window-control__marker-dot:after{top:14px}.time-window-control__handle--end .time-window-control__marker-dot:after{bottom:14px}.time-window-control__ticks{height:18px;color:var(--secondary-text-color,#666);margin:0 22px;font-size:12px;position:relative}.time-window-control__ticks span{white-space:nowrap;position:absolute;left:0}.time-window-control__ticks span:nth-child(2){left:25%;transform:translate(-50%)}.time-window-control__ticks span:nth-child(3){left:50%;transform:translate(-50%)}.time-window-control__ticks span:nth-child(4){left:75%;transform:translate(-50%)}.time-window-control__ticks span:last-child{left:auto;right:0}.time-window-control :disabled{opacity:.6;cursor:not-allowed}.time-window-control input:focus-visible,.time-window-control button:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.time-window-control__feedback{color:var(--secondary-text-color,#666);overflow-wrap:anywhere;margin-top:6px;font-size:14px;line-height:1.5}.time-window-control__feedback:empty{display:none}.time-window-control__feedback p{margin:0}.time-window-control__error{color:var(--error-color,#b71c1c)}.time-window-control__sr-only{clip-path:inset(50%);white-space:nowrap;border:0;width:1px;height:1px;margin:-1px;padding:0;position:absolute;overflow:hidden}"]]]), Ns = { class: "charging-view" }, Ps = {
	key: 0,
	class: "charging-view__status",
	role: "status"
}, Fs = {
	key: 1,
	class: "charging-view__status",
	role: "status"
}, Is = {
	key: 3,
	class: "charging-view__cards"
}, Ls = ["aria-labelledby"], Rs = ["id"], zs = /*#__PURE__*/ ko(/* @__PURE__ */ zn({
	__name: "ChargingLayout",
	props: {
		switchKey: { type: String },
		cards: { type: Array }
	},
	setup(e) {
		let t = e, n = kn(no), r = Bn(), i = Q(() => n?.language.value ?? "en"), a = Q(() => t.cards.map((e) => {
			let r = e.entities.filter(([e, t]) => n?.entity(e, t)), i = e.layout === "months" && (r.length || n?.entity("switch", t.switchKey)) ? e.entities : r;
			return {
				...e,
				showTimeWindow: !!(e.timeWindow && i.some(([e]) => e === "time")),
				entities: i.filter(([t]) => !e.timeWindow || t !== "time")
			};
		}).filter((e) => e.entities.length || e.showTimeWindow)), o = Q(() => !!n?.entity("switch", t.switchKey)), s = Q(() => i.value === "de" ? {
			loading: "Die Entitäten werden geladen …",
			empty: "Für diese Ansicht sind keine Entitäten verfügbar."
		} : {
			loading: "Loading entities …",
			empty: "No entities are available for this view."
		});
		return (t, c) => (K(), q("div", Ns, [
			!H(n)?.ready.value && !H(n)?.error.value ? (K(), q("p", Ps, L(s.value.loading), 1)) : H(n)?.ready.value && !o.value && !a.value.length ? (K(), q("p", Fs, L(s.value.empty), 1)) : Z("", !0),
			o.value ? (K(), ai(Ao, {
				key: 2,
				domain: "switch",
				"entity-key": e.switchKey
			}, null, 8, ["entity-key"])) : Z("", !0),
			a.value.length ? (K(), q("div", Is, [(K(!0), q(G, null, W(a.value, (e) => (K(), q("section", {
				key: e.key,
				class: "charging-view__card",
				"aria-labelledby": `${H(r)}-${e.key}`
			}, [
				J("h2", { id: `${H(r)}-${e.key}` }, L(e.title[i.value]), 9, Rs),
				e.showTimeWindow && e.timeWindow ? (K(), ai(Ms, {
					key: 0,
					kind: e.timeWindow
				}, null, 8, ["kind"])) : Z("", !0),
				$n(t.$slots, `${e.key}-settings`),
				e.entities.length ? (K(), q("div", {
					key: 1,
					class: de(["charging-view__rows", {
						"charging-view__rows--columns": e.layout === "columns",
						"charging-view__rows--months": e.layout === "months"
					}])
				}, [e.layout === "months" ? (K(), ai(hs, {
					key: 0,
					"entity-keys": e.entities.map(([, e]) => e)
				}, null, 8, ["entity-keys"])) : (K(!0), q(G, { key: 1 }, W(e.entities, ([e, t]) => (K(), q(G, { key: `${e}.${t}` }, [e === "switch" || e === "number" || e === "time" || e === "select" ? (K(), ai(Ao, {
					key: 0,
					domain: e,
					"entity-key": t
				}, null, 8, ["domain", "entity-key"])) : (K(), ai(Ho, {
					key: 1,
					domain: e,
					"entity-key": t
				}, null, 8, ["domain", "entity-key"]))], 64))), 128))], 2)) : Z("", !0)
			], 8, Ls))), 128))])) : Z("", !0)
		]));
	}
}), [["styles", [".charging-view{gap:20px;min-width:0;margin-top:24px;display:grid}.charging-view__cards{align-content:start;gap:20px;min-width:0;display:grid}.charging-view__card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.charging-view__card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.charging-view__rows{gap:16px;display:grid}.charging-view__card>.time-window-control+.charging-view__rows{border-top:1px solid var(--divider-color,#e0e0e0);margin-top:20px;padding-top:16px}.charging-view__rows>.entity-control{border:0;border-bottom:1px solid var(--divider-color,#e0e0e0);box-shadow:none;border-radius:0;padding:0 0 16px}.charging-view__rows>.entity-control:last-child{border-bottom:0;padding-bottom:0}.charging-view__status{color:var(--secondary-text-color,#666);margin:0;line-height:1.6}@media (max-width:600px){.charging-view,.charging-view__cards{gap:16px}.charging-view__card{padding:20px}}@container sax-content (width>=860px){.charging-view{gap:14px;margin-top:16px}.charging-view__cards{align-items:start;gap:16px}.charging-view__card{padding:18px}.charging-view__card h2{margin-bottom:12px;font-size:16px}.charging-view__rows{gap:12px}.charging-view__rows>.entity-control{gap:8px 12px;padding-bottom:12px}.charging-view__rows>.entity-control:last-child{padding-bottom:0}.charging-view__rows>.entity-control .entity-control__description{flex-basis:120px}.charging-view__rows--columns{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;column-gap:24px}.charging-view__rows--columns>:last-child:nth-child(odd){grid-column:1/-1}.charging-view__rows--columns .entity-value{min-height:44px;padding-block:8px}}"]]]), Bs = { class: "sensor-picker" }, Vs = [
	"value",
	"disabled",
	"name",
	"aria-invalid",
	"aria-describedby"
], Hs = { value: "" }, Us = ["value"], Ws = /*#__PURE__*/ ko(/* @__PURE__ */ zn({
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
		let n = e, r = t, i = Q(() => {
			let e = Object.values(n.hass?.states ?? {}).filter((e) => e.entity_id.startsWith("sensor.")).map((e) => ({
				id: e.entity_id,
				name: typeof e.attributes.friendly_name == "string" ? e.attributes.friendly_name : e.entity_id
			}));
			return n.modelValue && !e.some((e) => e.id === n.modelValue) && e.push({
				id: n.modelValue,
				name: n.modelValue
			}), e.sort((e, t) => e.name.localeCompare(t.name));
		});
		return (t, n) => (K(), q("label", Bs, [X(L(e.label), 1), J("select", {
			value: e.modelValue ?? "",
			disabled: e.disabled,
			name: e.name,
			"aria-invalid": e.invalid || void 0,
			"aria-describedby": e.describedBy,
			onChange: n[0] ||= (e) => r("update:modelValue", e.target.value || null)
		}, [J("option", Hs, L(e.hass?.language?.startsWith("de") ? "Nicht konfiguriert" : "Not configured"), 1), (K(!0), q(G, null, W(i.value, (e) => (K(), q("option", {
			key: e.id,
			value: e.id
		}, L(e.name), 9, Us))), 128))], 40, Vs)]));
	}
}), [["styles", [".sensor-picker{flex-direction:column;gap:6px;min-width:0;font-size:14px;display:flex}.sensor-picker select{width:100%;min-width:0;max-width:100%;min-height:44px;font:inherit;color:var(--primary-text-color,#222);background:var(--card-background-color,#fff);border:1px solid var(--divider-color,#ccc);border-radius:6px;padding:10px}"]]]), Gs = ["aria-labelledby", "aria-busy"], Ks = { class: "grid-serving-source__header" }, qs = ["id"], Js = {
	key: 0,
	class: "grid-serving-source__confirmed"
}, Ys = ["disabled"], Xs = ["id"], Zs = { key: 0 }, Qs = { key: 1 }, $s = {
	key: 2,
	role: "status"
}, ec = {
	key: 3,
	role: "status"
}, tc = ["id"], nc = ["disabled"], rc = { class: "grid-serving-source__actions" }, ic = ["disabled"], ac = ["disabled"], oc = /*#__PURE__*/ ko(/* @__PURE__ */ zn({
	__name: "GridServingForecastSource",
	props: { hass: { type: Object } },
	setup(e) {
		let t = e, n = kn(no), r = `grid-serving-source-${Bn()}`, i = /* @__PURE__ */ V(), a = /* @__PURE__ */ V(), o = /* @__PURE__ */ V(null), s = /* @__PURE__ */ V(null), c = /* @__PURE__ */ V(""), l = /* @__PURE__ */ V(!1), u = /* @__PURE__ */ V(null), d = /* @__PURE__ */ V(null), f = /* @__PURE__ */ V(!1), p = !1, m = !1;
		Zn(() => {
			p = !0;
		});
		let h = Q(() => n?.connected.value ?? !1), g = Q(() => n?.language.value === "de" ? {
			title: "Solarprognose für die Ladepause",
			hint: "Wähle einen Energiesensor für den heute noch erwarteten Solarertrag (Wh, kWh oder MWh). Liegt der Wert unter der Mindest-PV-Prognose, greift die Ladepause nicht. Bei einer Mindest-PV-Prognose von 0 kWh wird diese Bedingung nicht geprüft.",
			source: "PV-Sensor (heute verbleibend)",
			none: "Keine Quelle ausgewählt",
			missing: "Ohne Quelle greift die Ladepause bei einer Mindest-PV-Prognose über 0 kWh nicht.",
			readonly: "Nur Administratoren können die Quelle ändern.",
			edit: "Bearbeiten",
			save: "Speichern",
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
			save: "Save",
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
		}), _ = Q(() => d.value ? g.value[d.value] ?? g.value.failed : null), v = Q(() => {
			let e = o.value?.pv_sensor;
			if (!e) return g.value.none;
			let n = t.hass?.states[e]?.attributes.friendly_name;
			return typeof n == "string" ? n : e;
		}), y = Q(() => t.hass ? {
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
					p || (u.value = null, m ? (m = !1, x(e)) : e && l.value ? (await pn(), i.value?.querySelector("select")?.focus()) : f.value && !l.value && (await pn(), a.value?.focus()));
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
					p || (u.value = null, m ? (m = !1, x()) : f.value && (await pn(), a.value?.focus()));
				}
			}
		}
		async function C() {
			u.value || (l.value = !1, d.value = null, await pn(), a.value?.focus());
		}
		function w() {
			u.value ? m = !0 : x();
		}
		return U([h, () => n?.ready.value], ([e, t]) => {
			e && t && (!l.value || u.value) && w();
		}, { immediate: !0 }), U(() => n?.entity("sensor", "grid_serving_forecast")?.state?.attributes.source_entity_id, (e, t) => {
			e !== t && n?.ready.value && w();
		}), (e, t) => (K(), q("section", {
			ref_key: "section",
			ref: i,
			class: "grid-serving-source",
			"aria-labelledby": `${r}-title`,
			"aria-busy": !!u.value
		}, [
			J("div", Ks, [J("div", null, [J("h3", { id: `${r}-title` }, L(g.value.title), 9, qs), o.value ? (K(), q("p", Js, L(v.value), 1)) : Z("", !0)]), o.value?.can_edit && !l.value ? (K(), q("button", {
				key: 0,
				ref_key: "editButton",
				ref: a,
				type: "button",
				disabled: !!u.value || !h.value,
				onClick: t[0] ||= (e) => x(!0)
			}, L(g.value.edit), 9, Ys)) : Z("", !0)]),
			J("p", { id: `${r}-hint` }, L(g.value.hint), 9, Xs),
			o.value && !o.value.pv_sensor && !l.value ? (K(), q("p", Zs, L(g.value.missing), 1)) : Z("", !0),
			o.value && !o.value.can_edit ? (K(), q("p", Qs, L(g.value.readonly), 1)) : Z("", !0),
			u.value ? (K(), q("p", $s, L(u.value === "loading" ? g.value.loading : g.value.saving), 1)) : Z("", !0),
			f.value ? (K(), q("p", ec, L(g.value.saved), 1)) : Z("", !0),
			_.value ? (K(), q("p", {
				key: 4,
				id: `${r}-error`,
				class: "grid-serving-source__error",
				role: "alert"
			}, L(_.value), 9, tc)) : Z("", !0),
			d.value === "conflict" || !o.value && _.value ? (K(), q("button", {
				key: 5,
				type: "button",
				disabled: !!u.value || !h.value,
				onClick: t[1] ||= (e) => x(l.value)
			}, L(g.value.reload), 9, nc)) : Z("", !0),
			l.value ? (K(), q("form", {
				key: 6,
				onSubmit: Wa(S, ["prevent"])
			}, [Y(Ws, {
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
			]), J("div", rc, [J("button", {
				type: "submit",
				disabled: !!u.value || !h.value || !o.value?.can_edit || d.value === "conflict"
			}, L(g.value.save), 9, ic), J("button", {
				type: "button",
				disabled: !!u.value,
				onClick: C
			}, L(g.value.cancel), 9, ac)])], 32)) : Z("", !0)
		], 8, Gs));
	}
}), [["styles", [".grid-serving-source{border-block:1px solid var(--divider-color,#ddd);gap:12px;min-width:0;margin-block:20px;padding-block:16px;display:grid}.grid-serving-source__header{justify-content:space-between;align-items:start;gap:12px;display:flex}.grid-serving-source__header>div{min-width:0}.grid-serving-source h3{margin:0 0 6px;font-size:16px;font-weight:500}.grid-serving-source p{color:var(--secondary-text-color,#666);overflow-wrap:anywhere;margin:0;font-size:14px;line-height:1.6}.grid-serving-source .grid-serving-source__confirmed{color:var(--primary-text-color,#222)}.grid-serving-source .grid-serving-source__error{color:var(--error-color,#b00020)}.grid-serving-source form{gap:12px;display:grid}.grid-serving-source__actions{flex-wrap:wrap;gap:8px;display:flex}.grid-serving-source button{border:1px solid var(--divider-color,#ccc);min-height:44px;color:var(--primary-color,#0077a3);background:var(--card-background-color,#fff);font:inherit;cursor:pointer;border-radius:6px;padding:8px 16px}.grid-serving-source button:disabled{opacity:.5;cursor:default}.grid-serving-source button:focus-visible{outline:2px solid var(--primary-color,#0077a3);outline-offset:2px}"]]]), sc = /* @__PURE__ */ zn({
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
		return (n, r) => (K(), ai(zs, {
			"switch-key": "grid_serving_enabled",
			cards: t
		}, {
			"pause-settings": Tn(() => [Y(oc, { hass: e.hass }, null, 8, ["hass"])]),
			_: 1
		}));
	}
});
//#endregion
//#region src/savings.ts
function cc(e) {
	if (typeof e != "number" && typeof e != "string" || typeof e == "string" && !e.trim()) return null;
	let t = Number(e);
	return Number.isFinite(t) ? t : null;
}
function lc(e) {
	return {
		comma_decimal: "en-US",
		decimal_comma: "de-DE",
		space_comma: "fr-FR"
	}[e?.locale?.number_format ?? ""] ?? e?.locale?.language ?? e?.language ?? "en";
}
function uc(e, t, n = 2) {
	let r = cc(e);
	return r === null ? null : new Intl.NumberFormat(lc(t), {
		minimumFractionDigits: n,
		maximumFractionDigits: n,
		useGrouping: t?.locale?.number_format !== "none"
	}).format(r);
}
function dc(e, t, n = {
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
function fc(e, t) {
	let n = (e) => /^\d{4}-\d{2}-\d{2}$/.test(e) && Number(e.slice(0, 4)) > 0 && Number.isFinite(Date.parse(`${e}T00:00:00Z`)) && (/* @__PURE__ */ new Date(`${e}T00:00:00Z`)).toISOString().slice(0, 10) === e;
	return n(e) && n(t) && e <= t;
}
function pc(e) {
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
function mc(e, t, n) {
	let r = /* @__PURE__ */ Ht(null), i = /* @__PURE__ */ V(!1), a = /* @__PURE__ */ V(null), o, s = 0, c = !1;
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
					first_weekday: pc(u),
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
		if (!fc(e, t)) {
			a.value = "invalid";
			return;
		}
		o = {
			start_date: e,
			end_date: t
		}, l();
	}
	return U([
		() => e()?.connection,
		t,
		n,
		() => pc(e()),
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
	}, { immediate: !0 }), xe(() => {
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
//#region src/components/ChargePlan.vue?vue&type=script&setup=true&lang.ts
var hc = ["aria-labelledby"], gc = ["id"], _c = {
	key: 0,
	class: "charge-plan__forecast"
}, vc = { class: "charge-plan__forecast-hint" }, yc = { key: 1 }, bc = { key: 2 }, xc = { key: 0 }, Sc = { key: 3 }, Cc = { key: 4 }, wc = {
	key: 5,
	class: "charge-plan__target"
}, Tc = /*#__PURE__*/ ko(/* @__PURE__ */ zn({
	__name: "ChargePlan",
	props: { hass: { type: Object } },
	setup(e) {
		let t = e, n = kn(no), r = Bn(), i = Q(() => n?.language.value === "de"), a = Q(() => n?.entity("sensor", "bridge_charge_plan")), o = Q(() => n?.entity("switch", "bridge_charge_enabled")), s = Q(() => a.value?.state?.attributes ?? {}), c = Q(() => n?.entity("sensor", "discharge_forecast")), l = Q(() => {
			switch (o.value?.state?.attributes.configuration_error) {
				case "bridge_pv_start_required": return i.value ? "Zum Einschalten in Schritt 1 eine PV-Prognosequelle auswählen." : "To enable planning, select a PV forecast source in step 1.";
				case "bridge_tariff_required": return i.value ? "Zum Einschalten in Schritt 1 einen zeitvariablen Tarif einrichten." : "To enable planning, configure a time-of-use tariff in step 1.";
				default: return null;
			}
		}), u = Q(() => i.value ? {
			title: "Ladeplanung",
			currentForecast: "Aktuelle Entladeprognose",
			calculatedPlan: "Berechneter Ladeplan",
			forecastHint: "Schätzung aus dem gemessenen Verbrauch bis zur unteren Ladegrenze. Änderungen beim Verbrauch oder neue Ladung verändern die Prognose.",
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
			currentForecast: "Current discharge forecast",
			calculatedPlan: "Calculated charging plan",
			forecastHint: "An estimate based on measured consumption until the lower charge limit is reached. Changes in consumption or additional charging change the forecast.",
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
		}), d = Q(() => a.value?.available ? a.value.state?.state : "unavailable"), f = Q(() => i.value ? {
			pv_start_missing: "Die gewählte PV-Prognose liefert noch keinen Zeitraum, der den Verbrauch mindestens 30 Minuten lang deckt. Bitte die PV-Prognosequelle in Schritt 1 prüfen.",
			consumption_missing: "Für die Verbrauchsprognose wird mindestens eine Minute Entlademessung benötigt.",
			measurements_missing: "Aktuelle Batteriemesswerte fehlen.",
			calibration: "Die Batteriekalibrierung hat Vorrang.",
			pv_surplus: "PV-Überschuss pausiert die geplante Netzladung.",
			manual_charge: "Die manuelle Ladung hat Vorrang.",
			disabled: "In Schritt 2 „Nur Bedarf bis Solarstrom“ wählen und in Schritt 3 die automatische Netzladung einschalten."
		} : {
			pv_start_missing: "The selected PV forecast does not yet provide a period covering consumption for at least 30 minutes. Check the PV forecast source in step 1.",
			consumption_missing: "The consumption forecast needs at least one minute of discharge measurements.",
			measurements_missing: "Current battery measurements are missing.",
			calibration: "Battery calibration takes priority.",
			pv_surplus: "PV surplus pauses planned grid charging.",
			manual_charge: "Manual charging takes priority.",
			disabled: "Choose “Only what is needed until solar power” in step 2 and turn on automatic grid charging in step 3."
		}), p = Q(() => typeof s.value.reason == "string" ? f.value[s.value.reason] : void 0);
		function m(e, n, r, i = 1) {
			let a = cc(e);
			return a !== null && a >= n && a <= r ? uc(a, t.hass, i) : null;
		}
		function h(e) {
			return typeof e == "string" && /^\d{4}-\d{2}-\d{2}T.+(?:Z|[+-]\d{2}:\d{2})$/.test(e) ? dc(e, t.hass) : null;
		}
		let g = Q(() => {
			if (!c.value?.available) return null;
			let e = c.value.state, t = h(e?.state), n = m(e?.attributes.observation_minutes, 1, 60), r = m(e?.attributes.average_discharge_w, Number.MIN_VALUE, Infinity, 0);
			return !t || !n || !r ? null : i.value ? `Bei durchschnittlich ${r} W Verbrauch in den letzten ${n} Minuten reicht der Speicher voraussichtlich bis ${t} Uhr.` : `With average consumption of ${r} W over the last ${n} minutes, the battery is expected to last until ${t}.`;
		}), _ = Q(() => ({
			discharge: h(s.value.discharge_at),
			start: h(s.value.charge_start),
			end: h(s.value.charge_end),
			pv: h(s.value.pv_start)
		})), v = Q(() => [
			"waiting_for_data",
			"complete",
			"insufficient"
		].includes(d.value ?? "") && h(s.value.completed_at) !== null), y = Q(() => {
			if (!v.value) return null;
			switch (s.value.data_gap_reason) {
				case "pv_start_missing": return i.value ? "Während der Ladung war die PV-Prognose zeitweise nicht verfügbar." : "The PV forecast was temporarily unavailable during charging.";
				case "measurements_missing": return i.value ? "Während der Ladung waren Batteriemesswerte zeitweise nicht verfügbar." : "Battery measurements were temporarily unavailable during charging.";
				default: return null;
			}
		}), b = Q(() => {
			let e = h(s.value.completion_evaluated_at);
			return !v.value || !e ? null : i.value ? `Bewertet am ${e} Uhr anhand aktueller Batteriemesswerte.` : `Assessed at ${e} using current battery measurements.`;
		}), x = Q(() => {
			let e = m(s.value.observation_minutes, 1, 60);
			if (!e || !_.value.discharge) return null;
			let t = m(s.value.average_discharge_w, 0, Infinity, 0);
			return i.value ? `Aufgrund des Verbrauchs der letzten ${e} Minuten${t ? ` (durchschnittlich ${t} W)` : ""} wird der Speicher voraussichtlich bis ${_.value.discharge} Uhr entleert sein.` : `Based on consumption over the last ${e} minutes${t ? ` (an average of ${t} W)` : ""}, the battery is expected to be depleted by ${_.value.discharge}.`;
		}), S = Q(() => {
			let { start: e, end: t, pv: n } = _.value, r = d.value === "charging" && (cc(s.value.shortfall_kwh) ?? 0) > 0;
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
		}), C = Q(() => {
			if (v.value || ![
				"planned",
				"charging",
				"insufficient"
			].includes(d.value ?? "")) return null;
			let e = m(s.value.target_soc, 0, 100);
			return e ? i.value ? `Geplantes Ladeziel: ${e} %.` : `Planned charge target: ${e} %.` : null;
		});
		return (e, t) => a.value || o.value || g.value ? (K(), q("section", {
			key: 0,
			class: "charge-plan",
			"aria-labelledby": `${H(r)}-charge-plan`
		}, [
			J("h2", { id: `${H(r)}-charge-plan` }, L(u.value.title), 9, gc),
			g.value ? (K(), q("section", _c, [
				J("h3", null, L(u.value.currentForecast), 1),
				J("p", null, L(g.value), 1),
				J("p", vc, L(u.value.forecastHint), 1)
			])) : Z("", !0),
			g.value && a.value ? (K(), q("h3", yc, L(u.value.calculatedPlan), 1)) : Z("", !0),
			l.value ? (K(), q("p", bc, L(l.value), 1)) : Z("", !0),
			(K(!0), q(G, null, W(S.value, (e, t) => (K(), q(G, { key: t }, [e ? (K(), q("p", xc, L(e), 1)) : Z("", !0)], 64))), 128)),
			y.value ? (K(), q("p", Sc, L(y.value), 1)) : Z("", !0),
			b.value ? (K(), q("p", Cc, L(b.value), 1)) : Z("", !0),
			C.value ? (K(), q("p", wc, L(C.value), 1)) : Z("", !0)
		], 8, hc)) : Z("", !0);
	}
}), [["styles", [".charge-plan{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.charge-plan h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.charge-plan p{overflow-wrap:anywhere;line-height:1.6}.charge-plan p:last-child{margin-bottom:0}.charge-plan__forecast{margin-bottom:20px}.charge-plan__forecast h3{margin-top:0;font-size:16px}.charge-plan__forecast-hint,.charge-plan__target{color:var(--secondary-text-color,#666)}@media (max-width:600px){.charge-plan{padding:20px}}@container sax-content (width>=860px){.charge-plan{padding:18px}.charge-plan h2{margin-bottom:12px;font-size:16px}}"]]]), Ec = ["aria-labelledby"], Dc = { class: "tariff-plan__header" }, Oc = ["id"], kc = [
	"disabled",
	"aria-expanded",
	"aria-controls"
], Ac = {
	key: 0,
	role: "status"
}, jc = {
	key: 1,
	class: "tariff-plan__introduction"
}, Mc = {
	key: 2,
	class: "tariff-plan__compact-summary"
}, Nc = {
	key: 0,
	class: "tariff-plan__badge"
}, Pc = {
	key: 0,
	class: "tariff-plan__periods"
}, Fc = { key: 0 }, Ic = { class: "tariff-plan__period-price" }, Lc = {
	key: 0,
	class: "tariff-plan__badge"
}, Rc = { key: 1 }, zc = {
	key: 2,
	class: "tariff-plan__low-status"
}, Bc = {
	key: 3,
	class: "tariff-plan__pending-status"
}, Vc = {
	key: 4,
	class: "tariff-plan__low-unavailable"
}, Hc = { class: "tariff-plan__impact" }, Uc = {
	key: 3,
	role: "status"
}, Wc = ["id"], Gc = ["id", "aria-busy"], Kc = { key: 0 }, qc = ["disabled"], Jc = { class: "tariff-plan__hint" }, Yc = { class: "tariff-plan__step" }, Xc = ["aria-describedby"], Zc = ["id"], Qc = { class: "tariff-plan__step" }, $c = { class: "tariff-plan__hint" }, el = ["id"], tl = {
	key: 0,
	class: "tariff-plan__empty"
}, nl = { class: "tariff-plan__window-name" }, rl = [
	"onUpdate:modelValue",
	"name",
	"aria-invalid",
	"aria-describedby",
	"onInput",
	"onChange",
	"aria-label"
], il = [
	"onUpdate:modelValue",
	"name",
	"aria-invalid",
	"aria-describedby",
	"onInput",
	"onChange",
	"aria-label"
], al = ["onUpdate:modelValue", "aria-label"], ol = ["aria-label", "onClick"], sl = {
	key: 2,
	class: "tariff-plan__hint"
}, cl = { class: "tariff-plan__step" }, ll = ["aria-describedby"], ul = ["id"], dl = ["open"], fl = { class: "tariff-plan__hint" }, pl = { class: "tariff-plan__impact" }, ml = { class: "tariff-plan__actions" }, hl = ["disabled"], gl = ["disabled"], _l = ["disabled"], vl = {
	key: 6,
	class: "tariff-plan__overview"
}, yl = { class: "tariff-plan__current-price" }, bl = {
	key: 0,
	class: "tariff-plan__low-status"
}, xl = {
	key: 1,
	class: "tariff-plan__low-unavailable"
}, Sl = { key: 7 }, Cl = {
	key: 8,
	class: "tariff-plan__details tariff-plan__all-prices"
}, wl = ["aria-label"], Tl = { class: "tariff-plan__table" }, El = { scope: "col" }, Dl = { scope: "col" }, Ol = { scope: "col" }, kl = { scope: "col" }, Al = { colspan: "2" }, jl = { key: 0 }, Ml = { key: 0 }, Nl = { class: "tariff-plan__details" }, Pl = /*#__PURE__*/ ko(/* @__PURE__ */ zn({
	__name: "TariffPlan",
	props: {
		hass: { type: Object },
		compact: { type: Boolean }
	},
	emits: ["saved", "editing"],
	setup(e, { emit: t }) {
		let n = e, r = t, i = kn(no), a = Bn(), o = Q(() => i?.language.value === "de" ? {
			tariff: n.compact ? "1. Wann ist dein Strom günstig?" : "Dein Stromtarif",
			introduction: "Trage die Preise aus deinem Stromvertrag ein. Sie gelten jeden Tag zu denselben Zeiten.",
			currentPrice: "Strompreis jetzt",
			baseSection: "Normaler Strompreis",
			windowsSection: "Zeiten mit anderem Preis",
			windowsHint: "Zum Beispiel ein günstiger Nachtpreis von 22:00 bis 06:00 Uhr. Nur die Zeiten eintragen, in denen ein anderer Preis als der Standardpreis gilt.",
			noWindows: "Noch keine anderen Preiszeiten: Der Standardpreis gilt den ganzen Tag.",
			feedSection: "Vergütung für Solarstrom",
			feedHint: "Wie viel erhältst du für eine eingespeiste kWh? Dieser Wert wird für die Ersparnisberechnung verwendet. Ohne Vergütung 0 eintragen.",
			impact: "Das bewirkt dein Tarif",
			impactHint: "Die Automatik nutzt die günstigsten Zeiten für die feste und verbrauchsbasierte Netzladung. Ladestand, Ladeziel und aktive Monate gelten zusätzlich.",
			saveHint: "Speichern übernimmt Preise und mögliche Ladezeiten. Es schaltet die Netzladung nicht ein.",
			pvDetails: "Zusätzlich: Solarprognose für die Ladeplanung",
			pvHint: "Nur für verbrauchsbasierte Ladeplanung erforderlich. Wähle die eingerichtete PV-Prognosequelle, damit die Planung den Bedarf bis zum Solarstart berechnen kann.",
			allPrices: "Alle Preise ansehen",
			everyDay: "Täglich",
			remaining: "zu allen übrigen Zeiten",
			overnightLabel: "über Nacht",
			technicalReason: "Technischer Hinweis",
			awaitingTariff: "Die aktuellen Ladezeiten werden aktualisiert.",
			pv: "PV-Start-Sensor (optional)",
			pvRequired: "PV-Start-Sensor (erforderlich)",
			gross: "Alle Preise in ct/kWh inklusive Steuern, ohne monatliche Grundgebühr. Beispiel: 30 eingeben für 30 ct/kWh.",
			edit: "Bearbeiten",
			save: "Speichern",
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
			tariff: n.compact ? "1. When is your electricity cheaper?" : "Your electricity tariff",
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
			saveHint: "Saving applies the prices and possible charging times. It does not turn on grid charging.",
			pvDetails: "Additional setup: solar forecast for charging planning",
			pvHint: "Only required for consumption-based charging planning. Select your configured PV forecast source so planning can calculate the energy needed until solar production starts.",
			allPrices: "View all prices",
			everyDay: "Every day",
			remaining: "at all remaining times",
			overnightLabel: "overnight",
			technicalReason: "Technical details",
			awaitingTariff: "Current charging times are being updated.",
			pv: "PV start sensor (optional)",
			pvRequired: "PV start sensor (required)",
			gross: "All prices in ct/kWh including tax, excluding the monthly standing charge. Example: enter 30 for 30 ct/kWh.",
			edit: "Edit",
			save: "Save",
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
		}), s = Q(() => i?.entity("sensor", "economics_current_import_price")), c = (e) => {
			let t = cc(e), r = uc(t === null ? null : t * 100, n.hass, 2);
			return r === null ? o.value.unavailable : `${r} ct/kWh`;
		}, l = Q(() => {
			let e = uc(s.value?.state?.state, n.hass, 2);
			return e === null ? o.value.unavailable : `${e} ct/kWh`;
		}), u = (e) => dc(e, n.hass) ?? o.value.unavailable, d = /* @__PURE__ */ V(null), f = /* @__PURE__ */ V({});
		U(() => s.value?.state?.attributes, (e) => {
			e && (f.value = e);
		}, { immediate: !0 });
		let p = Q(() => s.value?.state?.attributes ?? (i?.connected.value ? {} : f.value)), m = /* @__PURE__ */ V(null);
		function h(e) {
			if (!e.tariff_type) return null;
			let t = (e) => {
				let t = cc(e);
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
		U(p, g);
		let _ = !1;
		Zn(() => {
			_ = !0;
		}), U([() => i?.ready.value, () => p.value.tariff_type], ([e, t]) => {
			e && !t && !i?.tariff.value && i?.loadTariff().catch(() => {});
		}, { immediate: !0 });
		let v = Q(() => {
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
		}), y = Q(() => h(v.value) === h(p.value)), b = Q(() => v.value.tariff_type === "time_of_use"), x = Q(() => Array.isArray(v.value.windows) ? v.value.windows.filter((e) => !!e && typeof e == "object" && typeof e.start == "string" && typeof e.end == "string") : []), S = Q(() => v.value.unavailable_reason), C = Q(() => s.value?.available === !0 && cc(s.value.state?.state) !== null && S.value == null && !d.value), w = Q(() => C.value && cc(v.value.low_tariff_price_eur_kwh) !== null && typeof v.value.low_tariff_active == "boolean" && (v.value.low_tariff_active === !1 || T.value !== null) && typeof v.value.base_price_is_low_tariff == "boolean" && Array.isArray(v.value.windows) && x.value.length === v.value.windows.length && x.value.every((e) => typeof e.low_tariff == "boolean" && cc(e.price_eur_kwh) !== null)), T = Q(() => dc(v.value.low_tariff_valid_until, n.hass)), ee = Q(() => w.value && v.value.low_tariff_active === !0 && T.value !== null), E = (e) => w.value && e.low_tariff === !0, D = Q(() => w.value && v.value.base_price_is_low_tariff === !0), te = (e, t) => [e ? o.value.now : "", t ? o.value.low : ""].filter(Boolean).join(" · "), O = Q(() => {
			let e = v.value.active_window;
			return e && typeof e == "object" ? e : null;
		}), ne = (e) => C.value && cc(e.price_eur_kwh) !== null && O.value?.start === e.start && O.value?.end === e.end, re = Q(() => C.value && O.value === null && cc(v.value.base_price_eur_kwh) !== null), k = (e) => dc(`2000-01-01T${e.length === 5 ? `${e}:00` : e}Z`, n.hass, {
			timeStyle: "short",
			timeZone: "UTC"
		}) ?? e.slice(0, 5), A = /* @__PURE__ */ V(!1);
		U(A, (e) => r("editing", e));
		let j = /* @__PURE__ */ V(!1), ie = /* @__PURE__ */ V("loading"), ae = /* @__PURE__ */ V(), oe = /* @__PURE__ */ V(), se = /* @__PURE__ */ V(null), M = /* @__PURE__ */ V(""), ce = /* @__PURE__ */ V(""), le = /* @__PURE__ */ V(null), ue = Q(() => i?.entity("switch", "bridge_charge_enabled")?.state?.state === "on"), N = /* @__PURE__ */ V([]), fe = 0, P = /* @__PURE__ */ V(null), F = /* @__PURE__ */ V(null), pe = /* @__PURE__ */ V(!1), me = /* @__PURE__ */ V(!1), I = Q(() => i?.connected.value === !0 && i.ready.value), he = Q(() => {
			if (P.value === "timeError" && F.value) {
				let e = N.value.findIndex((e) => e.key === F.value.key);
				return `${o.value.window} ${e + 1}: ${o.value[F.value.reason]}`;
			}
			return P.value ? o.value[P.value] : null;
		});
		function ge(e, t) {
			return ae.value?.querySelector(`[name="window_${e}_${t}"]`);
		}
		function _e(e, t, n) {
			let r = N.value.find((t) => t.key === e), i = n.target;
			r && (i.value = r[t] = gs(i.value)), ve(e);
		}
		function ve(e) {
			(e === void 0 || F.value?.key === e) && (F.value = null, P.value === "timeError" && (P.value = null));
		}
		function R(e) {
			if (_) return;
			let t = e && typeof e == "object" && "code" in e ? e.code : "failed";
			pe.value = t === "conflict", P.value = t === "bridge_pv_start_required" ? "bridgePvRequired" : t === "pv_sensor_missing" ? "pvMissing" : t === "invalid_tariff" || t === "invalid_format" ? "invalid" : [
				"conflict",
				"disconnected",
				"forbidden"
			].includes(String(t)) ? String(t) : "failed";
		}
		function ye(e) {
			return e === null ? "" : e.toFixed(2).replace(".", i?.language.value === "de" ? "," : ".");
		}
		async function be() {
			if (i && !j.value) {
				ie.value = "loading", j.value = !0, P.value = null, ve(), me.value = !1;
				try {
					let e = await i.loadTariff();
					if (_) return;
					if (!e.can_edit || e.tariff_type !== "time_of_use") throw { code: "forbidden" };
					se.value = e, M.value = ye(e.base_price_ct_kwh), ce.value = ye(e.feed_in_price_ct_kwh), le.value = e.profiles?.time_of_use.pv_sensor ?? null, N.value = e.windows.map((e) => ({
						key: fe++,
						start: we(e.start),
						end: we(e.end),
						price: ye(e.price_ct_kwh)
					})), pe.value = !1, A.value = !0;
				} catch (e) {
					R(e);
				} finally {
					j.value = !1, await pn(), A.value && ae.value?.querySelector("input")?.focus();
				}
			}
		}
		function xe() {
			A.value = !1, P.value = null, ve(), pe.value = !1, N.value = [], pn(() => oe.value?.focus());
		}
		async function z() {
			N.value.push({
				key: fe++,
				start: "",
				end: "",
				price: ""
			}), await pn(), ae.value?.querySelector(".tariff-plan__window:last-of-type input")?.focus();
		}
		async function Se(e) {
			ve(N.value[e]?.key), N.value.splice(e, 1), await pn();
			let t = ae.value?.querySelectorAll(".tariff-plan__window");
			(t?.[Math.min(e, t.length - 1)]?.querySelector("input") ?? ae.value?.querySelector(".tariff-plan__add"))?.focus();
		}
		function Ce(e, t, n) {
			if (!/^-?\d+(?:[.,]\d{1,2})?$/.test(e.trim())) return null;
			let r = Number(e.trim().replace(",", "."));
			return Number.isFinite(r) && r >= t && r <= n ? r : null;
		}
		function we(e) {
			return e.length === 8 && e.endsWith(":00") ? e.slice(0, 5) : e;
		}
		async function Te() {
			if (!i || !se.value || j.value || pe.value) return;
			P.value = null, ve();
			for (let e of N.value) for (let t of ["start", "end"]) {
				let n = ge(e.key, t);
				n && (e[t] = gs(n.value));
			}
			let e = Ce(M.value, -200, 500), t = Ce(ce.value, 0, 200), a = N.value.map((e) => ({
				...e,
				value: Ce(e.price, -200, 500)
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
					}, P.value = "timeError", await pn(), ge(e.key, r)?.focus();
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
			ie.value = "saving", j.value = !0;
			let c = h(p.value);
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
						pv_sensor: le.value
					}
				}) : await i.saveTariff(o);
				if (_) return;
				d.value = s, m.value = c, g(), xe(), me.value = !0, r("saved");
			} catch (e) {
				R(e);
			} finally {
				j.value = !1;
			}
		}
		return U(I, (e) => {
			!e && A.value ? P.value = "disconnected" : e && P.value === "disconnected" && (P.value = null);
		}), U(b, (e) => {
			!e && i?.ready.value && xe();
		}), (t, n) => b.value ? (K(), q("section", {
			key: 0,
			class: "tariff-plan",
			"aria-labelledby": `${H(a)}-tariff`
		}, [
			J("header", Dc, [J("h2", { id: `${H(a)}-tariff` }, L(o.value.tariff), 9, Oc), A.value ? Z("", !0) : (K(), q("button", {
				key: 0,
				ref_key: "editButton",
				ref: oe,
				type: "button",
				disabled: j.value || !I.value,
				"aria-expanded": A.value,
				"aria-controls": `${H(a)}-editor`,
				onClick: be
			}, L(j.value ? o.value.loading : o.value.edit), 9, kc))]),
			j.value ? (K(), q("p", Ac, L(o.value[ie.value]), 1)) : Z("", !0),
			A.value ? Z("", !0) : (K(), q("p", jc, L(o.value.introduction), 1)),
			e.compact && !A.value ? (K(), q("div", Mc, [
				J("p", null, [
					J("strong", null, L(o.value.base) + ": " + L(c(v.value.base_price_eur_kwh)), 1),
					D.value ? (K(), q("span", Nc, L(o.value.low), 1)) : Z("", !0),
					n[3] ||= J("br", null, null, -1),
					X(L(o.value.remaining), 1)
				]),
				x.value.length ? (K(), q("ul", Pc, [(K(!0), q(G, null, W(x.value, (e, t) => (K(), q("li", { key: t }, [J("span", null, [X(L(o.value.everyDay) + " " + L(k(e.start)) + " – " + L(k(e.end)), 1), e.end < e.start ? (K(), q("span", Fc, " (" + L(o.value.overnightLabel) + ")", 1)) : Z("", !0)]), J("span", Ic, [E(e) ? (K(), q("span", Lc, L(o.value.low), 1)) : Z("", !0), J("strong", null, L(c(e.price_eur_kwh)), 1)])]))), 128))])) : (K(), q("p", Rc, L(o.value.noWindows), 1)),
				w.value ? (K(), q("p", zc, [
					J("strong", null, L(o.value.lowTariffPrice) + ":", 1),
					X(" " + L(c(v.value.low_tariff_price_eur_kwh)) + ". ", 1),
					ee.value ? (K(), q(G, { key: 0 }, [X(L(o.value.lowUntil) + " " + L(T.value) + ".", 1)], 64)) : (K(), q(G, { key: 1 }, [X(L(o.value.notLow), 1)], 64))
				])) : d.value || !y.value ? (K(), q("p", Bc, L(o.value.awaitingTariff), 1)) : (K(), q("p", Vc, L(o.value.noLowTariff), 1)),
				J("p", Hc, L(o.value.impactHint), 1)
			])) : Z("", !0),
			me.value ? (K(), q("p", Uc, L(o.value.saved), 1)) : Z("", !0),
			he.value ? (K(), q("p", {
				key: 4,
				id: `${H(a)}-error`,
				role: "alert",
				class: "tariff-plan__error"
			}, L(he.value), 9, Wc)) : Z("", !0),
			A.value ? (K(), q("form", {
				key: 5,
				id: `${H(a)}-editor`,
				ref_key: "editor",
				ref: ae,
				class: "tariff-plan__editor",
				"aria-busy": j.value,
				novalidate: "",
				onSubmit: Wa(Te, ["prevent"])
			}, [
				se.value?.base_price_ct_kwh === null ? (K(), q("p", Kc, L(o.value.first), 1)) : Z("", !0),
				J("fieldset", { disabled: j.value || !I.value }, [
					J("p", Jc, L(o.value.gross), 1),
					J("div", Yc, [J("h3", null, L(o.value.baseSection), 1), J("label", null, [
						X(L(o.value.base) + " (ct/kWh)", 1),
						En(J("input", {
							"onUpdate:modelValue": n[0] ||= (e) => M.value = e,
							name: "base_price",
							type: "text",
							inputmode: "decimal",
							autocomplete: "off",
							"aria-describedby": `${H(a)}-base-hint`
						}, null, 8, Xc), [[Ia, M.value]]),
						J("small", { id: `${H(a)}-base-hint` }, L(o.value.baseHint), 9, Zc)
					])]),
					J("div", Qc, [
						J("h3", null, L(o.value.windowsSection), 1),
						J("p", $c, L(o.value.windowsHint), 1),
						J("p", {
							id: `${H(a)}-time-hint`,
							class: "tariff-plan__hint"
						}, L(o.value.timeHint), 9, el),
						N.value.length ? Z("", !0) : (K(), q("p", tl, L(o.value.noWindows), 1)),
						(K(!0), q(G, null, W(N.value, (e, t) => (K(), q("div", {
							key: e.key,
							class: "tariff-plan__window"
						}, [
							J("span", nl, L(o.value.window) + " " + L(t + 1), 1),
							J("label", null, [X(L(o.value.from), 1), En(J("input", {
								"onUpdate:modelValue": (t) => e.start = t,
								name: `window_${e.key}_start`,
								type: "text",
								class: "tariff-plan__time",
								inputmode: "numeric",
								autocomplete: "off",
								placeholder: "HH:MM",
								"aria-invalid": F.value?.key === e.key && F.value.field === "start",
								"aria-describedby": F.value?.key === e.key && F.value.field === "start" ? `${H(a)}-time-hint ${H(a)}-error` : `${H(a)}-time-hint`,
								onInput: (t) => ve(e.key),
								onChange: (t) => _e(e.key, "start", t),
								"aria-label": `${o.value.window} ${t + 1}: ${o.value.from}`
							}, null, 40, rl), [[Ia, e.start]])]),
							J("label", null, [X(L(o.value.to), 1), En(J("input", {
								"onUpdate:modelValue": (t) => e.end = t,
								name: `window_${e.key}_end`,
								type: "text",
								class: "tariff-plan__time",
								inputmode: "numeric",
								autocomplete: "off",
								placeholder: "HH:MM",
								"aria-invalid": F.value?.key === e.key && F.value.field === "end",
								"aria-describedby": F.value?.key === e.key && F.value.field === "end" ? `${H(a)}-time-hint ${H(a)}-error` : `${H(a)}-time-hint`,
								onInput: (t) => ve(e.key),
								onChange: (t) => _e(e.key, "end", t),
								"aria-label": `${o.value.window} ${t + 1}: ${o.value.to}`
							}, null, 40, il), [[Ia, e.end]])]),
							J("label", null, [X(L(o.value.price) + " (ct/kWh)", 1), En(J("input", {
								"onUpdate:modelValue": (t) => e.price = t,
								class: "tariff-plan__price",
								type: "text",
								inputmode: "decimal",
								autocomplete: "off",
								"aria-label": `${o.value.window} ${t + 1}: ${o.value.price} (ct/kWh)`
							}, null, 8, al), [[Ia, e.price]])]),
							J("button", {
								type: "button",
								class: "tariff-plan__remove",
								"aria-label": `${o.value.window} ${t + 1}: ${o.value.remove}`,
								onClick: (e) => Se(t)
							}, L(o.value.remove), 9, ol)
						]))), 128)),
						N.value.length < 8 ? (K(), q("button", {
							key: 1,
							type: "button",
							class: "tariff-plan__add",
							onClick: z
						}, L(o.value.add), 1)) : Z("", !0),
						N.value.length ? (K(), q("p", sl, L(o.value.overnight), 1)) : Z("", !0)
					]),
					J("div", cl, [J("h3", null, L(o.value.feedSection), 1), J("label", null, [
						X(L(o.value.feed) + " (ct/kWh)", 1),
						En(J("input", {
							"onUpdate:modelValue": n[1] ||= (e) => ce.value = e,
							name: "feed_in_price",
							type: "text",
							inputmode: "decimal",
							autocomplete: "off",
							"aria-describedby": `${H(a)}-feed-hint`
						}, null, 8, ll), [[Ia, ce.value]]),
						J("small", { id: `${H(a)}-feed-hint` }, L(o.value.feedHint), 9, ul)
					])]),
					e.compact ? (K(), q("details", {
						key: 0,
						class: "tariff-plan__details tariff-plan__pv-details",
						open: ue.value || P.value === "bridgePvRequired" || P.value === "pvMissing"
					}, [
						J("summary", null, L(o.value.pvDetails), 1),
						J("p", fl, L(o.value.pvHint), 1),
						Y(Ws, {
							modelValue: le.value,
							"onUpdate:modelValue": n[2] ||= (e) => le.value = e,
							hass: e.hass,
							label: ue.value ? o.value.pvRequired : o.value.pv
						}, null, 8, [
							"modelValue",
							"hass",
							"label"
						])
					], 8, dl)) : Z("", !0),
					J("div", pl, [
						J("strong", null, L(o.value.impact), 1),
						J("p", null, L(o.value.impactHint), 1),
						J("p", null, L(o.value.saveHint), 1)
					])
				], 8, qc),
				J("div", ml, [
					J("button", {
						type: "submit",
						class: "tariff-plan__save",
						disabled: j.value || !I.value || pe.value
					}, L(j.value ? o.value[ie.value] : o.value.save), 9, hl),
					J("button", {
						type: "button",
						disabled: j.value,
						onClick: xe
					}, L(o.value.cancel), 9, gl),
					pe.value ? (K(), q("button", {
						key: 0,
						type: "button",
						disabled: j.value || !I.value,
						onClick: be
					}, L(o.value.reload), 9, _l)) : Z("", !0)
				])
			], 40, Gc)) : Z("", !0),
			!A.value && !e.compact && !d.value ? (K(), q("div", vl, [J("p", yl, [J("span", null, L(o.value.currentPrice), 1), J("strong", null, L(C.value ? l.value : o.value.unavailable), 1)]), w.value ? (K(), q("p", bl, [
				J("strong", null, L(o.value.lowTariffPrice) + ":", 1),
				X(" " + L(c(v.value.low_tariff_price_eur_kwh)) + ". ", 1),
				ee.value ? (K(), q(G, { key: 0 }, [X(L(o.value.lowUntil) + " " + L(T.value) + ". ", 1)], 64)) : (K(), q(G, { key: 1 }, [X(L(o.value.notLow), 1)], 64))
			])) : (K(), q("p", xl, L(o.value.noLowTariff), 1))])) : Z("", !0),
			!A.value && !e.compact && C.value && v.value.next_price_change_at && !d.value ? (K(), q("p", Sl, [J("strong", null, L(o.value.next) + ":", 1), X(" " + L(u(v.value.next_price_change_at)), 1)])) : Z("", !0),
			!A.value && !e.compact ? (K(), q("details", Cl, [
				J("summary", null, L(o.value.allPrices), 1),
				J("div", {
					class: "tariff-plan__scroll",
					tabindex: "0",
					role: "region",
					"aria-label": o.value.allPrices
				}, [J("table", Tl, [J("thead", null, [J("tr", null, [
					J("th", El, L(o.value.status), 1),
					J("th", Dl, L(o.value.from), 1),
					J("th", Ol, L(o.value.to), 1),
					J("th", kl, L(o.value.price), 1)
				])]), J("tbody", null, [(K(!0), q(G, null, W(x.value, (e, t) => (K(), q("tr", {
					key: t,
					class: de({
						"tariff-plan__current": ne(e),
						"tariff-plan__low": E(e)
					})
				}, [
					J("td", null, L(te(ne(e), E(e))), 1),
					J("td", null, L(k(e.start)), 1),
					J("td", null, L(k(e.end)), 1),
					J("td", null, L(c(e.price_eur_kwh)), 1)
				], 2))), 128)), J("tr", { class: de({
					"tariff-plan__current": re.value,
					"tariff-plan__low": D.value
				}) }, [
					J("td", null, L(te(re.value, D.value)), 1),
					J("td", Al, L(o.value.base), 1),
					J("td", null, L(c(v.value.base_price_eur_kwh)), 1)
				], 2)])])], 8, wl),
				J("p", null, [J("strong", null, L(o.value.feed) + ":", 1), X(" " + L(c(v.value.feed_in_price_eur_kwh)), 1)]),
				!C.value && !d.value ? (K(), q("p", jl, [X(L(o.value.noPrice), 1), typeof S.value == "string" && S.value ? (K(), q("span", Ml, L(o.value.technicalReason) + ": " + L(S.value), 1)) : Z("", !0)])) : Z("", !0)
			])) : Z("", !0),
			J("details", Nl, [
				J("summary", null, L(o.value.details), 1),
				J("p", null, L(o.value.rule), 1),
				J("p", null, L(o.value.configure), 1)
			])
		], 8, Ec)) : Z("", !0);
	}
}), [["styles", [".tariff-plan{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.tariff-plan h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.tariff-plan__introduction{color:var(--secondary-text-color,#666);margin:0 0 16px}.tariff-plan__compact-summary{margin:0}.tariff-plan__periods{margin:12px 0;padding:0;list-style:none}.tariff-plan__periods li{border-top:1px solid var(--divider-color,#e0e0e0);flex-wrap:wrap;justify-content:space-between;gap:4px 12px;padding:10px 0;line-height:1.5;display:flex}.tariff-plan__period-price{flex-wrap:wrap;align-items:center;gap:8px;display:flex}.tariff-plan__badge{border:1px solid var(--success-color,#43a047);border-radius:6px;margin-inline-start:8px;padding:2px 7px;font-size:12px;font-weight:500;line-height:1.5;display:inline-block}.tariff-plan__periods strong{white-space:nowrap}.tariff-plan__step{margin:20px 0}.tariff-plan__step h3{margin:0 0 10px;font-size:15px;line-height:1.5}.tariff-plan__step>label{max-width:460px}.tariff-plan__step>label input{max-width:240px}.tariff-plan__step .tariff-plan__hint{margin-top:0}.tariff-plan__impact{background:var(--secondary-background-color,#f5f5f5);border-radius:8px;margin:16px 0;padding:14px;font-size:14px;line-height:1.6}.tariff-plan__impact p{margin:6px 0}.tariff-plan__empty{color:var(--secondary-text-color,#666);font-size:14px}.tariff-plan__overview{grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:12px;display:grid}.tariff-plan__overview>p{margin:0}.tariff-plan__current-price{background:var(--secondary-background-color,#f5f5f5);border-radius:8px;flex-direction:column;gap:4px;padding:12px;display:flex}.tariff-plan__current-price>span{color:var(--secondary-text-color,#666);font-size:14px}.tariff-plan__current-price>strong{font-variant-numeric:tabular-nums;font-size:26px}.tariff-plan__low-status{padding:12px 0;font-size:14px}.tariff-plan__low-unavailable{border-inline-start:3px solid var(--warning-color,#ff9800);padding-inline-start:12px;font-size:14px}.tariff-plan p{overflow-wrap:anywhere;line-height:1.6}.tariff-plan p:last-child{margin-bottom:0}.tariff-plan__scroll{overflow-x:auto}.tariff-plan__table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%;line-height:1.5}.tariff-plan__table th,.tariff-plan__table td{text-align:left;white-space:nowrap;border-bottom:1px solid var(--divider-color,#e0e0e0);padding:10px 8px}.tariff-plan__table th:last-child,.tariff-plan__table td:last-child{text-align:right}.tariff-plan__current{background:var(--secondary-background-color,color-mix(in srgb, currentColor 8%, transparent));font-weight:600}.tariff-plan__header{flex-wrap:wrap;justify-content:space-between;align-items:center;gap:12px;margin-bottom:12px;display:flex}.tariff-plan__header h2{margin:0}.tariff-plan button{font:inherit;cursor:pointer;min-height:44px;color:var(--primary-color,#03a9f4);border:1px solid var(--divider-color,#e0e0e0);background:0 0;border-radius:8px;padding:8px 12px}.tariff-plan button:disabled{cursor:default;opacity:.5}.tariff-plan button:focus-visible,.tariff-plan input:focus-visible,.tariff-plan summary:focus-visible,.tariff-plan__scroll:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.tariff-plan__editor{margin-bottom:16px}.tariff-plan__editor fieldset{border:0;min-width:0;margin:0;padding:0}.tariff-plan__editor label{flex-direction:column;gap:6px;min-width:0;font-size:14px;display:flex}.tariff-plan__editor input{box-sizing:border-box;border:1px solid var(--divider-color,#bbb);width:100%;min-width:0;min-height:44px;font:inherit;font-variant-numeric:tabular-nums;color:var(--primary-text-color,#212121);background:var(--card-background-color,#fff);border-radius:6px;padding:10px}.tariff-plan__editor small,.tariff-plan__hint{color:var(--secondary-text-color,#666);font-size:13px}.tariff-plan__window{border-top:1px solid var(--divider-color,#e0e0e0);grid-template-columns:repeat(2,minmax(0,1fr));align-items:end;gap:12px;margin-top:20px;padding-top:16px;display:grid}.tariff-plan__window-name{grid-column:1/-1;font-size:14px;font-weight:600}.tariff-plan__window label:nth-of-type(3){grid-column:1}.tariff-plan__remove{justify-self:end}.tariff-plan__add{margin-top:16px}.tariff-plan__actions{flex-wrap:wrap;gap:8px;display:flex}.tariff-plan .tariff-plan__save{background:var(--primary-color,#03a9f4);color:var(--text-primary-color,#fff)}.tariff-plan__error{color:var(--error-color,#db4437)}.tariff-plan input[aria-invalid=true]{border-color:var(--error-color,#db4437)}.tariff-plan__details{margin-top:14px;font-size:14px}.tariff-plan__details summary{cursor:pointer;color:var(--secondary-text-color,#666);box-sizing:border-box;min-height:44px;padding:12px 0;line-height:1.5}@media (max-width:400px){.tariff-plan__window{grid-template-columns:minmax(0,1fr)}}@media (max-width:600px){.tariff-plan{padding:20px}}@container sax-content (width>=860px){.tariff-plan{padding:18px}.tariff-plan h2{margin-bottom:12px;font-size:16px}.tariff-plan p{margin-top:10px;line-height:1.5}.tariff-plan__table th,.tariff-plan__table td{padding:7px 8px}}"]]]);
//#endregion
//#region src/tariff-chart.ts
function Fl(e, t = 1e3) {
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
var Il = ["aria-busy"], Ll = {
	key: 0,
	role: "status"
}, Rl = {
	key: 1,
	class: "tariff-price-chart__empty",
	role: "status"
}, zl = {
	key: 0,
	class: "tariff-price-chart__partial"
}, Bl = ["viewBox", "aria-label"], Vl = [
	"x2",
	"y1",
	"y2"
], Hl = ["y"], Ul = ["d"], Wl = ["x1", "x2"], Gl = ["x"], Kl = { key: 2 }, ql = [
	"x1",
	"x2",
	"y1",
	"y2"
], Jl = ["x", "text-anchor"], Yl = {
	class: "tariff-price-chart__detail",
	"aria-live": "polite"
}, Xl = { class: "tariff-price-chart__scroll" }, Zl = /*#__PURE__*/ ko(/* @__PURE__ */ zn({
	__name: "TariffPriceChart",
	props: {
		series: { type: [Object, null] },
		hass: { type: Object },
		loading: { type: Boolean }
	},
	setup(e) {
		let t = e, n = Q(() => t.hass?.language?.startsWith("de") ?? !0), r = Q(() => n.value ? {
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
		}), i = /* @__PURE__ */ V(), a = /* @__PURE__ */ V(620), o;
		Xn(() => {
			typeof ResizeObserver > "u" || !i.value || (o = new ResizeObserver((e) => {
				a.value = Math.max(180, e[0]?.contentRect.width ?? 620);
			}), o.observe(i.value));
		}), Zn(() => o?.disconnect());
		let s = Q(() => Fl(t.series, a.value)), c = /* @__PURE__ */ V(null), l = /* @__PURE__ */ V(!1);
		U(() => t.series, () => {
			c.value = null, l.value = !1;
		});
		let u = (e) => uc(e, t.hass, 2) ?? "—", d = Q(() => {
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
		}), f = (e, n = !1) => dc(e, t.hass, {
			...n && d.value ? {
				hour: "2-digit",
				minute: "2-digit",
				timeZoneName: "shortOffset"
			} : { timeStyle: "short" },
			timeZone: t.series?.time_zone
		}) ?? "—", p = Q(() => c.value === null ? null : s.value.slots[c.value]), m = Q(() => Date.parse(t.series?.now ?? "")), h = Q(() => m.value >= s.value.start && m.value < s.value.end), g = Q(() => [
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
		return (t, n) => (K(), q("div", {
			ref_key: "container",
			ref: i,
			class: "tariff-price-chart",
			"aria-busy": e.loading
		}, [e.loading ? (K(), q("p", Ll, L(r.value.loading), 1)) : s.value.slots.length ? (K(), q(G, { key: 2 }, [
			e.series?.status === "partial" ? (K(), q("p", zl, L(r.value.partial), 1)) : Z("", !0),
			(K(), q("svg", {
				viewBox: `0 0 ${a.value} 252`,
				preserveAspectRatio: "none",
				role: "img",
				"aria-label": `${r.value.title}. ${r.value.hint}`,
				tabindex: "0",
				onPointermove: _,
				onPointerdown: _,
				onKeydown: v
			}, [
				J("title", null, L(r.value.title), 1),
				n[0] ||= J("text", {
					x: "48",
					y: "15"
				}, "ct/kWh", -1),
				(K(!0), q(G, null, W(s.value.ticks, (e) => (K(), q("g", { key: e }, [J("line", {
					x1: "48",
					x2: a.value - 12,
					y1: s.value.y(e),
					y2: s.value.y(e),
					class: "tariff-price-chart__grid"
				}, null, 8, Vl), J("text", {
					x: "40",
					y: s.value.y(e) + 4,
					"text-anchor": "end"
				}, L(u(e)), 9, Hl)]))), 128)),
				J("path", {
					d: s.value.path,
					class: "tariff-price-chart__line"
				}, null, 8, Ul),
				h.value ? (K(), q("line", {
					key: 0,
					x1: s.value.x(m.value),
					x2: s.value.x(m.value),
					y1: "25",
					y2: "216",
					class: "tariff-price-chart__now"
				}, null, 8, Wl)) : Z("", !0),
				h.value ? (K(), q("text", {
					key: 1,
					x: Math.max(68, Math.min(a.value - 30, s.value.x(m.value))),
					y: "23",
					"text-anchor": "middle"
				}, L(r.value.now), 9, Gl)) : Z("", !0),
				p.value ? (K(), q("g", Kl, [J("line", {
					x1: s.value.x(p.value.from),
					x2: s.value.x(p.value.to),
					y1: s.value.y(p.value.price_ct_kwh),
					y2: s.value.y(p.value.price_ct_kwh),
					class: "tariff-price-chart__selected"
				}, null, 8, ql)])) : Z("", !0),
				(K(!0), q(G, null, W(g.value, (e, t) => (K(), q("text", {
					key: e,
					x: s.value.x(e),
					y: "244",
					"text-anchor": t === 0 ? "start" : t === 2 ? "end" : "middle"
				}, L(t === 2 ? "24:00" : f(new Date(e).toISOString())), 9, Jl))), 128))
			], 40, Bl)),
			J("p", Yl, L(p.value ? `${f(p.value.start, !0)}–${f(p.value.end, !0)} · ${u(p.value.price_ct_kwh)} ct/kWh` : l.value ? r.value.gap : r.value.hint), 1),
			J("details", null, [J("summary", null, L(r.value.table), 1), J("div", Xl, [J("table", null, [J("thead", null, [J("tr", null, [
				J("th", null, L(r.value.from), 1),
				J("th", null, L(r.value.to), 1),
				J("th", null, L(r.value.price), 1)
			])]), J("tbody", null, [(K(!0), q(G, null, W(s.value.slots, (e) => (K(), q("tr", { key: e.start }, [
				J("td", null, L(f(e.start, !0)), 1),
				J("td", null, L(f(e.end, !0)), 1),
				J("td", null, L(u(e.price_ct_kwh)) + " ct/kWh", 1)
			]))), 128))])])])])
		], 64)) : (K(), q("div", Rl, L(r.value.empty), 1))], 8, Il));
	}
}), [["styles", [".tariff-price-chart{min-width:0}.tariff-price-chart svg{touch-action:pan-y;width:100%;height:240px;display:block;overflow:visible}.tariff-price-chart svg text{fill:var(--secondary-text-color,#666);font-size:14px}.tariff-price-chart__line{fill:none;stroke:var(--primary-color,#03a9f4);stroke-width:3px;vector-effect:non-scaling-stroke}.tariff-price-chart__grid{stroke:var(--divider-color,#ddd);vector-effect:non-scaling-stroke}.tariff-price-chart__now{stroke:var(--secondary-text-color,#666);stroke-dasharray:4;vector-effect:non-scaling-stroke}.tariff-price-chart__selected{stroke:var(--success-color,#38964b);stroke-width:6px;vector-effect:non-scaling-stroke}.tariff-price-chart__empty{text-align:center;min-height:240px;color:var(--secondary-text-color,#666);place-items:center;display:grid}.tariff-price-chart__detail,.tariff-price-chart__partial{min-height:20px;color:var(--secondary-text-color,#666);font-size:14px}.tariff-price-chart summary{cursor:pointer;min-height:32px;padding:6px 0}.tariff-price-chart__scroll{overflow:auto}.tariff-price-chart table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%}.tariff-price-chart th,.tariff-price-chart td{text-align:left;border-bottom:1px solid var(--divider-color,#ddd);white-space:nowrap;padding:8px}.tariff-price-chart th:last-child,.tariff-price-chart td:last-child{text-align:right}"]]]), Ql = { class: "dynamic-charging-settings" }, $l = { class: "dynamic-charging-summary" }, eu = {
	key: 0,
	class: "electricity-muted dynamic-charging-neutral-summary"
}, tu = {
	key: 1,
	class: "electricity-muted"
}, nu = {
	key: 2,
	class: "electricity-error",
	role: "alert"
}, ru = {
	key: 3,
	role: "status",
	"aria-live": "polite"
}, iu = { key: 4 }, au = { class: "electricity-muted" }, ou = ["aria-label", "aria-busy"], su = [
	"data-strategy",
	"aria-pressed",
	"disabled",
	"onClick"
], cu = {
	key: 0,
	class: "electricity-muted"
}, lu = { class: "electricity-muted" }, uu = { class: "electricity-muted" }, du = { class: "electricity-muted" }, fu = { class: "dynamic-charging-notice" }, pu = { class: "electricity-muted" }, mu = { class: "electricity-muted" }, hu = { class: "dynamic-charging-advanced" }, gu = { class: "electricity-muted" }, _u = {
	key: 0,
	class: "electricity-muted"
}, vu = /*#__PURE__*/ ko(/* @__PURE__ */ zn({
	__name: "DynamicChargingSettings",
	props: { editing: { type: Boolean } },
	setup(e) {
		let t = kn(no), n = Q(() => t?.language.value === "de"), r = Q(() => n.value ? {
			mode: "Wann soll der Speicher aus dem Netz laden?",
			saved: "Gespeicherte Ladeweise",
			immediate: "Änderungen gelten nach der Bestätigung durch Home Assistant. Die automatische Netzladung muss zusätzlich eingeschaltet sein.",
			target: "Wie voll soll der Speicher werden?",
			targetLabel: "Ladeziel (%)",
			targetHint: "Dies ist die globale Ladegrenze für alle Lademethoden, auch für PV-Ladung. Bedarfsgerechtes Laden kann weniger Netzstrom nutzen, wenn die PV-Prognose den übrigen Bedarf deckt. Das Ziel ist keine Garantie: Preise, Ladezeit und andere aktive Regeln können die Ladung begrenzen.",
			hours: "Maximale Ladezeit je 24 Stunden",
			hoursHint: "Die günstigsten Zeitabschnitte ergeben zusammen höchstens diese Dauer. Der 24-Stunden-Zyklus beginnt beim Aktivieren dieser Ladeweise, nicht um Mitternacht. Heute/Morgen ändert nur die Preisansicht. Weniger Stunden begrenzen den Netzstrombezug, können aber ein volles Ladeziel verhindern.",
			smartHours: "Bedarfsgerecht nutzt nur die benötigte Zeit; diese Stundenzahl bleibt die Obergrenze. Fehlen Ladestand, Kapazität oder Ladeleistung, werden stattdessen die günstigsten Stunden bis zu dieser Obergrenze ausgewählt.",
			price: "Höchster Preis zum Laden (ct/kWh)",
			priceHint: "Bei einem Preis bis einschließlich dieser Grenze wird geladen, bis die globale Ladegrenze erreicht ist. Oberhalb findet keine preisgesteuerte Netzladung statt. Auch negative Preise sind möglich.",
			noPriceLimit: "Es gilt keine feste Preisgrenze: Auch die günstigsten verfügbaren Stunden können teuer sein. Diese Ladeweise benötigt eine Preisvorschau mit Zeitabschnitten; ein einzelner aktueller Preis reicht nicht.",
			pvMissing: "Ohne PV-Prognose wird keine künftige PV-Energie abgezogen. Eine Prognose kannst du in Schritt 1 ergänzen.",
			pvUsed: "Die gespeicherte PV-Prognose wird berücksichtigt, soweit sie verfügbar ist. Sie kann den benötigten Netzstrom reduzieren. Den angerechneten Anteil findest du in Schritt 1.",
			offHint: "Diese Ladeweise setzt die preisgesteuerte Automatik aus, auch wenn der Hauptschalter eingeschaltet ist. Preise und Einstellungen bleiben erhalten.",
			advanced: "Weitere Einstellungen · Speicher schonen",
			neutral: "Speicher bei günstigem Strom schonen bis (ct/kWh)",
			neutralHint: "Wenn kein Ladeslot aktiv ist, pausiert der Speicher unterhalb dieses Preises: Er lädt und entlädt nicht; das Haus nutzt Netzstrom. So bleibt gespeicherte Energie für teurere Zeiten erhalten. Ab diesem Preis wird der normale Speicherbetrieb wieder freigegeben.",
			absoluteNeutral: "Bei der festen Preisgrenze wirkt diese Pause nur oberhalb der Ladepreisgrenze. Liegt dieser Wert gleich hoch oder niedriger, gibt es keine solche Pause.",
			neutralSummary: "Außerhalb der Ladezeiten: Speicher schonen und Haus aus dem Netz versorgen unter",
			neutralBand: "und oberhalb der Ladepreisgrenze",
			neutralInactive: "Speicher schonen ist ohne Wirkung: Die Grenze liegt nicht über dem höchsten Ladepreis.",
			neutralUnavailable: "Die Grenze zum Schonen des Speichers ist nicht verfügbar.",
			disabled: "Automatische Netzladung ist ausgeschaltet. Die gespeicherte Ladeweise greift erst nach dem Einschalten.",
			unavailable: "Ladeweise nicht verfügbar. Es wird keine Auswahl angenommen.",
			readonly: "Keine Berechtigung zum Ändern der Ladeweise.",
			disconnected: "Keine Verbindung zu Home Assistant.",
			pending: "Ladeweise wird übernommen …",
			targetSummary: "Ladegrenze",
			modes: {
				smart: {
					title: "Bedarfsgerecht laden",
					hint: "Kauft die noch benötigte Energie in günstigen Stunden. Eine PV-Prognose kann den Netzstrombedarf verringern."
				},
				relative: {
					title: "Günstigste Stunden nutzen",
					hint: "Lädt in den günstigsten Zeitabschnitten bis zur eingestellten Stundenzahl oder Ladegrenze."
				},
				absolute: {
					title: "Bis zu einem festen Preis laden",
					hint: "Du legst fest, was eine Kilowattstunde höchstens kosten darf. Nur bis zu diesem Preis wird geladen."
				},
				off: {
					title: "Keine automatische Ladung",
					hint: "Setzt die preisgesteuerte Ladung aus. Die übrigen Einstellungen bleiben gespeichert."
				}
			}
		} : {
			mode: "When should the battery charge from the grid?",
			saved: "Saved charging method",
			immediate: "Changes apply once confirmed by Home Assistant. Automatic grid charging must also be switched on.",
			target: "How full should the battery be?",
			targetLabel: "Charge target (%)",
			targetHint: "This is the global charge limit for every charging method, including solar charging. Charging what is needed may use less grid energy when forecast solar production covers the remaining need. Reaching the target is not guaranteed: prices, charging time and other active rules may limit charging.",
			hours: "Maximum charging time per 24 hours",
			hoursHint: "The cheapest time slots add up to at most this duration. The 24-hour cycle starts when you activate this charging method, not at midnight. Today/Tomorrow only changes the price chart. Fewer hours limit grid energy use but may prevent reaching the charge target.",
			smartHours: "Charging what is needed uses only the required time; these hours remain the upper limit. If battery level, capacity or charging power is missing, the cheapest hours up to this limit are selected instead.",
			price: "Maximum price for charging (ct/kWh)",
			priceHint: "Charging is allowed at or below this price until the global charge limit is reached. Above it, price-controlled grid charging stops. Negative prices are supported.",
			noPriceLimit: "There is no fixed price cap: even the cheapest available hours may be expensive. This method requires a price forecast with time slots; a single current price is not enough.",
			pvMissing: "Without a solar forecast, no future solar energy is deducted. You can add a forecast in step 1.",
			pvUsed: "The saved solar forecast is used when available. It may reduce the grid energy needed. Its contribution is configured in step 1.",
			offHint: "This method pauses price-controlled automation even when the main switch is on. Prices and settings are preserved.",
			advanced: "More settings · Preserve battery energy",
			neutral: "Preserve battery energy below (ct/kWh)",
			neutralHint: "When no charging slot is active, the battery pauses below this price: it neither charges nor discharges, and the house uses grid energy. This keeps stored energy for more expensive times. Normal battery operation resumes at this price or above.",
			absoluteNeutral: "With a fixed charging price, this pause applies only above that charging price. If this value is equal or lower, no such pause occurs.",
			neutralSummary: "Outside charging slots: preserve battery energy and supply the house from the grid below",
			neutralBand: "and above the charging price cap",
			neutralInactive: "Preserving battery energy has no effect: the threshold is not above the maximum charging price.",
			neutralUnavailable: "The threshold for preserving battery energy is unavailable.",
			disabled: "Automatic grid charging is off. The saved method takes effect after switching it on.",
			unavailable: "Charging method unavailable. No selection is assumed.",
			readonly: "You do not have permission to change the charging method.",
			disconnected: "Disconnected from Home Assistant.",
			pending: "Applying charging method …",
			targetSummary: "Charge limit",
			modes: {
				smart: {
					title: "Charge what is needed",
					hint: "Buys the remaining energy needed during cheap hours. A solar forecast can reduce grid energy needs."
				},
				relative: {
					title: "Use the cheapest hours",
					hint: "Charges during the cheapest time slots up to the selected hours or charge limit."
				},
				absolute: {
					title: "Charge below a fixed price",
					hint: "You set the highest price you want to pay per kilowatt-hour. Charging only runs at or below it."
				},
				off: {
					title: "No automatic charging",
					hint: "Pauses price-controlled charging. All other settings are preserved."
				}
			}
		}), i = Q(() => t?.entity("select", "price_charge_strategy")), a = [
			"smart",
			"relative",
			"absolute",
			"off"
		], o = Q(() => {
			let e = i.value?.state?.state;
			return i.value?.available && a.includes(e) ? e : null;
		}), s = Q(() => i.value?.state?.attributes.options), c = Q(() => !i.value?.canControl || i.value.pending), l = Q(() => t?.connected.value ? i.value?.available ? i.value.metadata.can_control ? i.value.pending ? r.value.pending : "" : r.value.readonly : r.value.unavailable : r.value.disconnected), u = Q(() => !!t?.tariff.value?.profiles?.dynamic.pv_sensor), d = Q(() => {
			if (!o.value) return r.value.unavailable;
			let e = r.value.modes[o.value].title;
			if (o.value === "off") return e;
			let n = t?.entity("number", "max_soc")?.displayValue ?? "—";
			return `${e} · ${t?.entity("number", o.value === "absolute" ? "price_charge_max_price" : "price_charge_hours")?.displayValue ?? "—"} · ${r.value.targetSummary} ${n}`;
		}), f = Q(() => {
			let e = t?.entity("number", "price_charge_neutral_price"), n = t?.entity("number", "price_charge_max_price"), i = cc(e?.state?.state), a = cc(n?.state?.state);
			return !e?.available || i === null || o.value === "absolute" && (!n?.available || a === null) ? r.value.neutralUnavailable : o.value === "absolute" && a !== null && i <= a ? r.value.neutralInactive : `${r.value.neutralSummary} ${e.displayValue}${o.value === "absolute" ? ` ${r.value.neutralBand}` : ""}.`;
		});
		async function p(e) {
			!c.value && Array.isArray(s.value) && s.value.includes(e) && o.value !== e && await t?.perform("select", "price_charge_strategy", e);
		}
		return (n, m) => (K(), q("div", Ql, [
			J("p", $l, [J("span", null, L(r.value.saved) + ":", 1), X(" " + L(d.value), 1)]),
			o.value && o.value !== "off" ? (K(), q("p", eu, L(f.value), 1)) : Z("", !0),
			H(t)?.tariff.value?.automation_enabled === !1 ? (K(), q("p", tu, L(r.value.disabled), 1)) : Z("", !0),
			i.value?.error ? (K(), q("p", nu, L(i.value.error), 1)) : l.value ? (K(), q("p", ru, L(l.value), 1)) : Z("", !0),
			e.editing ? (K(), q("div", iu, [
				J("h3", null, L(r.value.mode), 1),
				J("p", au, L(r.value.immediate), 1),
				J("div", {
					class: "dynamic-charging-methods",
					role: "group",
					"aria-label": r.value.mode,
					"aria-busy": i.value?.pending ?? !1
				}, [(K(), q(G, null, W(a, (e) => J("button", {
					key: e,
					type: "button",
					"data-strategy": e,
					"aria-pressed": o.value === e,
					disabled: c.value || !Array.isArray(s.value) || !s.value.includes(e),
					onClick: (t) => p(e)
				}, [J("strong", null, L(r.value.modes[e].title), 1), J("span", null, L(r.value.modes[e].hint), 1)], 8, su)), 64))], 8, ou),
				o.value === "off" ? (K(), q("p", cu, L(r.value.offHint), 1)) : Z("", !0),
				o.value && o.value !== "off" ? (K(), q(G, { key: 1 }, [
					J("h3", null, L(r.value.target), 1),
					Y(Ao, {
						domain: "number",
						"entity-key": "max_soc",
						label: r.value.targetLabel,
						"hide-confirmed-label": ""
					}, null, 8, ["label"]),
					J("p", lu, L(r.value.targetHint), 1),
					o.value === "absolute" ? (K(), q(G, { key: 0 }, [Y(Ao, {
						domain: "number",
						"entity-key": "price_charge_max_price",
						label: r.value.price,
						"hide-confirmed-label": ""
					}, null, 8, ["label"]), J("p", uu, L(r.value.priceHint), 1)], 64)) : (K(), q(G, { key: 1 }, [
						Y(Ao, {
							domain: "number",
							"entity-key": "price_charge_hours",
							label: r.value.hours,
							"hide-confirmed-label": ""
						}, null, 8, ["label"]),
						J("p", du, L(r.value.hoursHint), 1),
						J("p", fu, L(r.value.noPriceLimit), 1),
						o.value === "smart" ? (K(), q(G, { key: 0 }, [J("p", pu, L(r.value.smartHours), 1), J("p", mu, L(u.value ? r.value.pvUsed : r.value.pvMissing), 1)], 64)) : Z("", !0)
					], 64)),
					J("details", hu, [
						J("summary", null, L(r.value.advanced), 1),
						Y(Ao, {
							domain: "number",
							"entity-key": "price_charge_neutral_price",
							label: r.value.neutral,
							"hide-confirmed-label": ""
						}, null, 8, ["label"]),
						J("p", gu, L(r.value.neutralHint), 1),
						o.value === "absolute" ? (K(), q("p", _u, L(r.value.absoluteNeutral), 1)) : Z("", !0)
					])
				], 64)) : Z("", !0)
			])) : Z("", !0)
		]));
	}
}), [["styles", [".dynamic-charging-summary span{font-weight:600}.dynamic-charging-methods{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:16px;display:grid}.dynamic-charging-methods button{text-align:left;color:var(--primary-text-color,#212121);padding:16px}.dynamic-charging-methods button[aria-pressed=true]{border:2px solid var(--primary-color,#03a9f4);background:var(--secondary-background-color,#f5f5f5);padding:15px}.dynamic-charging-methods strong,.dynamic-charging-methods span{line-height:1.5;display:block}.dynamic-charging-methods span{color:var(--secondary-text-color,#666);margin-top:6px;font-size:14px}.dynamic-charging-advanced{border-top:1px solid var(--divider-color,#ddd);margin-top:20px;padding-top:12px}.dynamic-charging-advanced summary{cursor:pointer;align-content:center;min-height:44px}.dynamic-charging-notice{border-left:3px solid var(--primary-color,#03a9f4);padding-left:12px}@media (max-width:700px){.dynamic-charging-methods{grid-template-columns:minmax(0,1fr)}}"]]]), yu = { class: "tou-charging-settings" }, bu = { class: "tou-charging-summary" }, xu = {
	key: 0,
	class: "tou-charging-hint tou-charging-calibration"
}, Su = {
	key: 1,
	class: "tou-charging-threshold"
}, Cu = { class: "tou-charging-month-summary" }, wu = {
	key: 2,
	class: "tou-charging-hint"
}, Tu = {
	key: 0,
	class: "tou-charging-error",
	role: "alert"
}, Eu = {
	key: 1,
	role: "status",
	"aria-live": "polite"
}, Du = {
	key: 3,
	class: "tou-charging-editor"
}, Ou = { class: "tou-charging-hint" }, ku = ["aria-label", "aria-busy"], Au = [
	"data-method",
	"aria-pressed",
	"disabled",
	"onClick"
], ju = {
	key: 0,
	class: "tou-charging-hint"
}, Mu = { class: "tou-charging-hint" }, Nu = {
	key: 0,
	class: "tou-charging-hint tou-charging-calibration"
}, Pu = { class: "tou-charging-advanced" }, Fu = { class: "tou-charging-hint" }, Iu = { class: "tou-charging-hint" }, Lu = /*#__PURE__*/ ko(/* @__PURE__ */ zn({
	__name: "TimeOfUseChargingSettings",
	props: {
		editing: { type: Boolean },
		hass: { type: Object }
	},
	setup(e) {
		let t = e, n = kn(no), r = Q(() => n?.language.value === "de"), i = `sax-tou-method-${Bn()}`, a = /* @__PURE__ */ V(t.editing);
		U(() => t.editing, (e) => {
			e && (a.value = !0);
		});
		let o = Q(() => r.value ? {
			saved: "Gespeicherte Ladeweise",
			mode: "Ladeweise",
			immediate: "Jede Änderung wird einzeln übernommen. Die automatische Netzladung muss zusätzlich eingeschaltet sein.",
			fixed: "Festes Ladeziel",
			fixedHint: "Lädt in den günstigsten Tarifzeiten bis zu deinem Ladeziel. Beginnt nur, wenn der Ladestand unter der Startschwelle liegt.",
			bridge: "Nur Bedarf bis Solarstrom",
			bridgeHint: "Plant anhand deines bisherigen Verbrauchs nur die fehlende Energie bis zum erwarteten Solarstrom. Ist genug Energie im Speicher, wird nicht geladen.",
			target: "Ladeziel",
			fixedTarget: "Ladeziel (%)",
			bridgeTarget: "Höchstens laden bis (%)",
			fixedTargetHint: "Die Netzladung endet beim Ladeziel oder am Ende der günstigen Tarifzeit. Nach der Netzladung entlädt der Speicher bis zum Ende dieser Zeit nicht; Solarstrom kann ihn weiter füllen. Andere aktive Regeln können die Ladung begrenzen.",
			bridgeTargetHint: "Der berechnete Bedarf kann unter dieser Obergrenze liegen. Geladen wird nur in den günstigsten Tarifzeiten. Danach darf der Speicher wieder normal entladen. Ohne Verbrauchs- oder Prognosedaten wird kein neuer Ladeplan erstellt.",
			calibration: "Ausnahme: Bei fälliger Zellkalibrierung sind bis 100 % erlaubt, auch über Ladeziel und globale Ladegrenze hinaus. Alle anderen Ladebedingungen gelten weiter.",
			pvRequired: "Für „Nur Bedarf bis Solarstrom“ benötigst du eine passende PV-Prognose mit dem erwarteten Solarstart. Öffne in Schritt 1 „Bearbeiten“ und ergänze die Solarprognose.",
			months: "Aktive Monate",
			allYear: "Ganzjährig",
			noMonths: "Keine ausgewählt · Automatische Netzladung ganzjährig inaktiv",
			unknownMonths: "Monatsauswahl nicht vollständig bekannt",
			advanced: "Weitere Einstellungen",
			threshold: "Nur starten unter einem Ladestand von (%)",
			thresholdHint: "Beispiel: Bei 20 % beginnt eine neue Netzladung erst unter 20 %. Danach darf sie im selben günstigen Zeitfenster bis zum Ladeziel weiterlaufen. 0 % verhindert einen neuen Start.",
			thresholdSummary: "Neue Netzladung startet nur unter",
			zeroThreshold: "Startschwelle 0 %: Es beginnt keine neue automatische Netzladung.",
			thresholdUnavailable: "Startschwelle nicht verfügbar.",
			global: "Ladegrenze für alle Lademethoden (%)",
			globalHint: "Gilt auch für Solarstrom. Diese Grenze begrenzt das gespeicherte Netzladeziel vorübergehend. Wenn du sie anhebst, wird das ursprüngliche Ziel bis zur neuen globalen Grenze wieder wirksam. Nur wenn du das Netzladeziel ausdrücklich änderst, wird dessen gespeicherter Wert dauerhaft geändert.",
			disabled: "Automatische Netzladung ist aus. Die gespeicherten Einstellungen gelten nach dem Einschalten.",
			unavailable: "Ladeweise nicht verfügbar. Es wird keine Auswahl angenommen.",
			valueUnavailable: "Nicht verfügbar",
			readonly: "Keine Berechtigung zum Ändern der Ladeweise.",
			disconnected: "Keine Verbindung zu Home Assistant.",
			pending: "Ladeweise wird übernommen …"
		} : {
			saved: "Saved charging method",
			mode: "Charging method",
			immediate: "Each change is applied individually. Automatic grid charging must also be switched on.",
			fixed: "Fixed charge target",
			fixedHint: "Charges to your target during the cheapest tariff periods. Only starts when the battery level is below the start threshold.",
			bridge: "Only what is needed until solar power",
			bridgeHint: "Uses your recent consumption to plan only the missing energy until solar power is expected. Does not charge when the battery already holds enough energy.",
			target: "Charge target",
			fixedTarget: "Charge target (%)",
			bridgeTarget: "Charge up to at most (%)",
			fixedTargetHint: "Grid charging ends at the target or the end of the cheap tariff period. After grid charging, the battery does not discharge until this period ends; solar power can charge it further. Other active rules may limit charging.",
			bridgeTargetHint: "The calculated need may be below this upper limit. Charging only uses the cheapest tariff periods. Afterwards, the battery may discharge normally again. Missing consumption or forecast data prevents a new charging plan.",
			calibration: "Exception: When cell calibration is due, charging up to 100% is allowed beyond both the charge target and global limit. Other charging conditions still apply.",
			pvRequired: "“Only what is needed until solar power” requires a suitable forecast with the expected start of solar power. Open “Edit” in step 1 and add the solar forecast.",
			months: "Active months",
			allYear: "All year",
			noMonths: "None selected · Automatic grid charging inactive all year",
			unknownMonths: "Month selection is not fully known",
			advanced: "More settings",
			threshold: "Only start below a battery level of (%)",
			thresholdHint: "For example, 20% means a new grid charge starts only below 20%. It can then continue to the target within the same cheap period. 0% prevents a new start.",
			thresholdSummary: "New grid charging starts only below",
			zeroThreshold: "Start threshold 0%: No new automatic grid charge will start.",
			thresholdUnavailable: "Start threshold unavailable.",
			global: "Charge limit for all charging methods (%)",
			globalHint: "Also applies to solar charging. This limit temporarily caps the saved grid charge target. Raising it makes the original target effective again, up to the new global limit. Only explicitly changing the grid charge target permanently changes its saved value.",
			disabled: "Automatic grid charging is off. Saved settings apply after switching it on.",
			unavailable: "Charging method unavailable. No selection is assumed.",
			valueUnavailable: "Unavailable",
			readonly: "You do not have permission to change the charging method.",
			disconnected: "Disconnected from Home Assistant.",
			pending: "Applying charging method …"
		}), s = Q(() => n?.entity("switch", "bridge_charge_enabled")), c = ["fixed", "bridge"], l = Q(() => s.value?.available ? s.value.state?.state === "off" ? "fixed" : s.value.state?.state === "on" ? "bridge" : null : null), u = Q(() => !s.value?.canControl || s.value.pending || l.value === null), d = Q(() => s.value?.pending ? o.value.pending : n?.connected.value ? l.value ? s.value?.metadata.can_control ? "" : o.value.readonly : o.value.unavailable : o.value.disconnected), f = Q(() => n?.entity("number", "timed_charge_max_soc")), p = Q(() => n?.entity("number", "timed_charge_min_soc")), m = Q(() => {
			let e = cc(p.value?.state?.state);
			return !p.value?.available || e === null ? o.value.thresholdUnavailable : e === 0 ? o.value.zeroThreshold : `${o.value.thresholdSummary} ${p.value.displayValue}.`;
		}), h = Q(() => {
			if (!l.value) return o.value.unavailable;
			let e = l.value === "fixed" ? o.value.fixedTarget : o.value.bridgeTarget, t = f.value?.available ? f.value.displayValue : o.value.valueUnavailable;
			return `${o.value[l.value]} · ${e.replace(" (%)", "")} ${t}`;
		}), g = Q(() => !!n?.tariff.value?.profiles?.time_of_use.pv_sensor), _ = Array.from({ length: 12 }, (e, t) => `timed_charge_month_${t + 1}`), v = Q(() => {
			let e = new Intl.DateTimeFormat(r.value ? "de" : "en", {
				month: "short",
				timeZone: "UTC"
			}), t = _.map((t, r) => {
				let i = n?.entity("switch", t), a = i?.state?.state;
				return {
					known: i?.available && (a === "on" || a === "off"),
					selected: i?.available && a === "on",
					name: e.format(new Date(Date.UTC(2024, r, 1)))
				};
			}), i = t.filter((e) => e.selected), a = t.some((e) => !e.known);
			return i.length === 12 ? o.value.allYear : i.length ? `${i.map((e) => e.name).join(", ")}${a ? ` · ${o.value.unknownMonths}` : ""}` : a ? o.value.unknownMonths : o.value.noMonths;
		});
		async function y(e) {
			u.value || l.value === e || await n?.perform("switch", "bridge_charge_enabled", e === "bridge");
		}
		return (t, r) => (K(), q("div", yu, [
			J("p", bu, [J("strong", null, L(o.value.saved) + ":", 1), X(" " + L(h.value), 1)]),
			l.value && !e.editing ? (K(), q("p", xu, L(o.value.calibration), 1)) : Z("", !0),
			l.value === "fixed" ? (K(), q("p", Su, L(m.value), 1)) : Z("", !0),
			J("p", Cu, [J("strong", null, L(o.value.months) + ":", 1), X(" " + L(v.value), 1)]),
			H(n)?.tariff.value?.automation_enabled === !1 ? (K(), q("p", wu, L(o.value.disabled), 1)) : Z("", !0),
			J("div", {
				id: i,
				class: "tou-charging-feedback"
			}, [e.editing && s.value?.error ? (K(), q("p", Tu, L(s.value.error), 1)) : Z("", !0), d.value && (e.editing || !s.value?.pending) ? (K(), q("p", Eu, L(d.value), 1)) : Z("", !0)]),
			a.value ? En((K(), q("div", Du, [
				J("h3", null, L(o.value.mode), 1),
				J("p", Ou, L(o.value.immediate), 1),
				J("div", {
					class: "tou-charging-methods",
					role: "group",
					"aria-label": o.value.mode,
					"aria-describedby": i,
					"aria-busy": s.value?.pending ?? !1
				}, [(K(), q(G, null, W(c, (e) => J("button", {
					key: e,
					type: "button",
					"data-method": e,
					"aria-pressed": l.value === e,
					disabled: u.value,
					onClick: (t) => y(e)
				}, [J("strong", null, L(o.value[e]), 1), J("span", null, L(e === "fixed" ? o.value.fixedHint : o.value.bridgeHint), 1)], 8, Au)), 64))], 8, ku),
				g.value ? Z("", !0) : (K(), q("p", ju, L(o.value.pvRequired), 1)),
				l.value ? (K(), q(G, { key: 1 }, [
					J("h3", null, L(o.value.target), 1),
					Y(Ao, {
						domain: "number",
						"entity-key": "timed_charge_max_soc",
						label: l.value === "fixed" ? o.value.fixedTarget : o.value.bridgeTarget,
						"hide-confirmed-label": ""
					}, null, 8, ["label"]),
					J("p", Mu, L(l.value === "fixed" ? o.value.fixedTargetHint : o.value.bridgeTargetHint), 1),
					e.editing ? (K(), q("p", Nu, L(o.value.calibration), 1)) : Z("", !0)
				], 64)) : Z("", !0),
				J("details", Pu, [
					J("summary", null, L(o.value.advanced), 1),
					l.value === "fixed" ? (K(), q(G, { key: 0 }, [Y(Ao, {
						domain: "number",
						"entity-key": "timed_charge_min_soc",
						label: o.value.threshold,
						"hide-confirmed-label": ""
					}, null, 8, ["label"]), J("p", Fu, L(o.value.thresholdHint), 1)], 64)) : Z("", !0),
					Y(Ao, {
						domain: "number",
						"entity-key": "max_soc",
						label: o.value.global,
						"hide-confirmed-label": ""
					}, null, 8, ["label"]),
					J("p", Iu, L(o.value.globalHint), 1),
					J("h3", null, L(o.value.months), 1),
					Y(hs, { "entity-keys": H(_) }, null, 8, ["entity-keys"])
				])
			], 512)), [[Xi, e.editing]]) : Z("", !0)
		]));
	}
}), [["styles", [".tou-charging-settings{min-width:0}.tou-charging-editor>.entity-control,.tou-charging-advanced>.entity-control{box-shadow:none;background:0 0;border:0;border-radius:0;padding:12px 0}.tou-charging-summary,.tou-charging-threshold,.tou-charging-month-summary{overflow-wrap:anywhere;line-height:1.5}.tou-charging-hint{color:var(--secondary-text-color,#666);font-size:14px;line-height:1.6}.tou-charging-error{color:var(--error-color,#b00020)}.tou-charging-methods{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:16px 0;display:grid}.tou-charging-methods button{border:1px solid var(--divider-color,#ddd);background:var(--card-background-color,#fff);min-width:0;min-height:44px;color:var(--primary-text-color,#212121);text-align:left;font:inherit;cursor:pointer;border-radius:8px;padding:16px}.tou-charging-methods button[aria-pressed=true]{border:2px solid var(--primary-color,#03a9f4);background:var(--secondary-background-color,#f5f5f5);padding:15px}.tou-charging-methods strong,.tou-charging-methods span{line-height:1.5;display:block}.tou-charging-methods span{color:var(--secondary-text-color,#666);margin-top:6px;font-size:14px}.tou-charging-methods button:disabled{opacity:.55;cursor:not-allowed}.tou-charging-methods button:focus-visible,.tou-charging-advanced summary:focus-visible{outline:3px solid var(--primary-color,#03a9f4);outline-offset:3px}.tou-charging-advanced{border-top:1px solid var(--divider-color,#ddd);margin-top:20px;padding-top:12px}.tou-charging-advanced summary{cursor:pointer;align-content:center;min-height:44px}@media (max-width:700px){.tou-charging-methods{grid-template-columns:minmax(0,1fr)}}"]]]), Ru = { class: "electricity-tariff-view" }, zu = { class: "electricity-card electricity-tariff-bar" }, Bu = { class: "electricity-tariff-bar__row" }, Vu = { class: "electricity-active" }, Hu = ["disabled", "aria-expanded"], Uu = ["aria-busy"], Wu = ["disabled"], Gu = { class: "electricity-sr-only" }, Ku = ["value"], qu = {
	key: 0,
	role: "status"
}, Ju = { class: "electricity-actions" }, Yu = ["disabled"], Xu = ["disabled"], Zu = {
	key: 1,
	class: "electricity-operation-status",
	role: "status",
	"aria-live": "polite"
}, Qu = {
	key: 2,
	role: "alert",
	class: "electricity-error"
}, $u = ["disabled"], ed = {
	key: 4,
	role: "status"
}, td = {
	key: 5,
	role: "status"
}, nd = {
	key: 6,
	role: "status"
}, rd = {
	key: 7,
	class: "electricity-muted"
}, id = ["aria-busy"], ad = ["disabled", "aria-expanded"], od = { class: "electricity-muted electricity-price-summary" }, sd = ["aria-busy"], cd = ["id"], ld = ["disabled"], ud = { class: "electricity-muted" }, dd = { class: "electricity-fields" }, fd = ["aria-invalid", "aria-describedby"], pd = { class: "electricity-muted" }, md = { class: "electricity-muted" }, hd = { class: "electricity-fields" }, gd = { class: "electricity-muted" }, _d = {
	key: 0,
	class: "electricity-muted electricity-additional-settings"
}, vd = { class: "electricity-price-advanced" }, yd = { class: "electricity-fields" }, bd = ["aria-invalid", "aria-describedby"], xd = ["aria-invalid", "aria-describedby"], Sd = ["value"], Cd = { class: "electricity-muted" }, wd = { class: "electricity-muted" }, Td = { class: "electricity-fields" }, Ed = ["aria-invalid", "aria-describedby"], Dd = { class: "electricity-muted" }, Od = { class: "electricity-actions" }, kd = ["disabled"], Ad = ["disabled"], jd = {
	key: 2,
	class: "electricity-card electricity-charging"
}, Md = ["disabled", "aria-expanded"], Nd = {
	key: 2,
	class: "electricity-charging-feedback"
}, Pd = {
	key: 0,
	class: "electricity-error",
	role: "alert"
}, Fd = {
	key: 1,
	role: "status",
	"aria-live": "polite"
}, Id = {
	key: 3,
	class: "electricity-charging-editor"
}, Ld = { class: "electricity-actions" }, Rd = {
	key: 3,
	class: "electricity-card electricity-activation"
}, zd = ["aria-busy"], Bd = [
	"checked",
	"aria-describedby",
	"disabled"
], Vd = {
	id: "electricity-master-status",
	class: "electricity-master-status",
	role: "status",
	"aria-live": "polite"
}, Hd = {
	key: 0,
	id: "electricity-activation-error",
	class: "electricity-error",
	role: "alert"
}, Ud = ["disabled"], Wd = {
	key: 2,
	class: "electricity-muted"
}, Gd = {
	key: 3,
	class: "electricity-muted"
}, Kd = {
	key: 4,
	class: "electricity-muted"
}, qd = { key: 5 }, Jd = {
	key: 4,
	class: "electricity-card electricity-price-card"
}, Yd = { class: "electricity-current-price" }, Xd = { key: 0 }, Zd = { class: "electricity-muted" }, Qd = { class: "electricity-price-details" }, $d = ["aria-label"], ef = ["aria-pressed", "onClick"], tf = { class: "electricity-day" }, nf = { key: 0 }, rf = {
	key: 5,
	class: "electricity-card electricity-plan"
}, af = {
	key: 0,
	class: "electricity-planned-pv"
}, of = /*#__PURE__*/ ko(/* @__PURE__ */ zn({
	__name: "ElectricityTariffView",
	props: { hass: { type: Object } },
	setup(e) {
		let t = e, n = kn(no), r = Q(() => n?.language.value === "de"), i = Q(() => r.value ? {
			active: "Aktiver Tarif",
			tou: "Zeitvariabel",
			dynamic: "Dynamisch",
			unset: "Noch nicht eingerichtet",
			change: "Tarif wechseln",
			apply: "Tarif übernehmen",
			cancel: "Abbrechen",
			save: "Speichern",
			done: "Fertig",
			edit: "Bearbeiten",
			loading: "Wird geladen …",
			saving: "Wird gespeichert …",
			applying: "Tarif wird übernommen …",
			entityPending: "Änderung wird an Home Assistant gesendet …",
			automatic: "Automatische Netzladung",
			turningOn: "Einschalten wird übernommen …",
			turningOff: "Ausschalten wird übernommen …",
			chooseHint: "Nur der gewählte Tarif ist aktiv. Gespeicherte Einstellungen bleiben beim Wechsel erhalten.",
			incomplete: "Dieser Tarif ist noch nicht eingerichtet. Nach dem Wechsel bleibt die automatische Netzladung aus. Richte danach die Preise in Schritt 1 ein.",
			touHint: "Feste Preise zu wiederkehrenden Uhrzeiten",
			dynamicHint: "Preise aus einem Strompreis-Sensor",
			price: "Strompreis",
			current: "Aktuell",
			today: "Heute",
			tomorrow: "Morgen",
			prices: "1. Woher kommen deine Strompreise?",
			feed: "Einspeisevergütung",
			source: "Strompreis-Sensor (erforderlich)",
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
			charging: "2. Wie möchtest du laden?",
			touCharging: "2. Wie viel möchtest du laden?",
			activate: "3. Automatik einschalten",
			activationHint: "Nach dem Einschalten darf der Speicher zu deinen günstigsten Tarifzeiten aus dem Netz laden. Ladeziel, aktive Monate und Schutzregeln gelten weiterhin.",
			dynamicActivationHint: "Nach dem Einschalten lädt der Speicher nach deiner gewählten Ladeweise. Preisgrenze oder günstigste Stunden, Ladegrenze und Schutzregeln bestimmen, wann und wie viel geladen wird.",
			activationOff: "Ausgeschaltet: Diese Automatik lädt derzeit keinen Netzstrom.",
			activationOn: "Eingeschaltet: Der Speicher lädt, sobald die eingestellten Bedingungen erfüllt sind.",
			editFirst: "Beende zuerst die Bearbeitung oben, um die Automatik zu schalten.",
			chart: "Preisverlauf anzeigen",
			touIntro: "Trage die Preise aus deinem Stromvertrag ein und wähle dein Ladeziel. Schalte die Automatik anschließend in Schritt 3 ein.",
			dynamicIntro: "Wähle deinen Strompreis-Sensor und die gewünschte Ladeweise. Schalte die Automatik anschließend in Schritt 3 ein.",
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
			save: "Save",
			done: "Done",
			edit: "Edit",
			loading: "Loading …",
			saving: "Saving …",
			applying: "Applying tariff …",
			entityPending: "Sending change to Home Assistant …",
			automatic: "Automatic grid charging",
			turningOn: "Turning on …",
			turningOff: "Turning off …",
			chooseHint: "Only the selected tariff is active. Saved settings are preserved when switching.",
			incomplete: "This tariff is not configured yet. Automatic grid charging will be off after switching. Set up the prices in step 1 next.",
			touHint: "Fixed prices at recurring times",
			dynamicHint: "Prices from an electricity price sensor",
			price: "Electricity price",
			current: "Current",
			today: "Today",
			tomorrow: "Tomorrow",
			prices: "1. Where do your electricity prices come from?",
			feed: "Feed-in remuneration",
			source: "Electricity price sensor (required)",
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
			charging: "2. How should the battery charge?",
			touCharging: "2. How much should the battery charge?",
			activate: "3. Turn on automatic charging",
			activationHint: "Once enabled, the battery may charge from the grid during your cheapest tariff periods. The charge target, active months and protection rules still apply.",
			dynamicActivationHint: "Once enabled, the battery follows your selected charging method. The price cap or cheapest hours, charge limit and protection rules determine when and how much it charges.",
			activationOff: "Switched off: This automation is not charging from the grid.",
			activationOn: "Switched on: The battery charges when the configured conditions are met.",
			editFirst: "Finish editing above before switching automatic charging.",
			chart: "Show price chart",
			touIntro: "Enter the prices from your electricity contract and choose a charge target. Then switch on automatic charging in step 3.",
			dynamicIntro: "Choose your electricity price sensor and charging method. Then switch on automatic charging in step 3.",
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
		}), a = /* @__PURE__ */ V(null);
		U(() => n?.tariff.value, (e) => {
			e && (a.value = e);
		}, { immediate: !0 });
		let o = Q(() => n?.tariff.value ?? a.value), s = Q(() => o.value?.tariff_type), c = Q(() => s.value === "time_of_use" || s.value === "dynamic"), l = Q(() => n?.connected.value === !0 && n.ready.value), u = Q(() => o.value?.can_configure === !0 && l.value), d = Q(() => s.value === "dynamic" ? i.value.dynamic : s.value === "time_of_use" ? i.value.tou : i.value.unset), f = Q(() => n?.entity("switch", s.value === "dynamic" ? "price_charge_enabled" : "timed_charge_enabled")), p = Q(() => typeof o.value?.automation_enabled == "boolean" ? o.value.automation_enabled : f.value?.available ? f.value.state?.state === "on" : null), m = /* @__PURE__ */ V(null), h = /* @__PURE__ */ V(!1), g = /* @__PURE__ */ V("today"), _ = /* @__PURE__ */ V(null), v = /* @__PURE__ */ V(null), y = /* @__PURE__ */ V(null), b = Bn(), x = /* @__PURE__ */ V(!1), S = /* @__PURE__ */ V(!1), C = /* @__PURE__ */ V(null), w = /* @__PURE__ */ V(null), T = /* @__PURE__ */ V(!1), ee = /* @__PURE__ */ V(!1), E = /* @__PURE__ */ V(!1), D = /* @__PURE__ */ V("time_of_use"), te = /* @__PURE__ */ V(""), O = /* @__PURE__ */ V(!1), ne = /* @__PURE__ */ V(!1), re = /* @__PURE__ */ V(!1), k = /* @__PURE__ */ V({
			feed_in_price_ct_kwh: null,
			price_sensor: null,
			price_attribute: null,
			price_unit: "auto",
			pv_sensor: null,
			pv_factor: 100
		}), A = /* @__PURE__ */ V(""), j = /* @__PURE__ */ V(""), ie = /* @__PURE__ */ V(""), ae = /* @__PURE__ */ V(), oe = /* @__PURE__ */ V(), se = /* @__PURE__ */ V(), M = !1, ce = 0;
		Zn(() => {
			M = !0, ce++, window.clearInterval(_e);
		});
		let le = Q(() => O.value || ne.value || re.value), ue = Q(() => uc(l.value ? m.value?.current_price_ct_kwh : null, t.hass, 2)), N = Q(() => m.value ? dc(`${m.value.date}T12:00:00Z`, t.hass, {
			dateStyle: "medium",
			timeZone: "UTC"
		}) : null), de = Q(() => {
			let e = s.value === "dynamic" ? o.value?.profiles?.dynamic.price_sensor : n?.entity("sensor", "economics_current_import_price")?.metadata.entity_id;
			return e ? t.hass?.states[e] : void 0;
		}), fe = Q(() => {
			let e = n?.entity("sensor", "price_charge_status_text"), r = e?.state?.attributes, i = o.value?.profiles?.dynamic.pv_sensor;
			if (!e?.available || !i || r?.pv_prognose_sensor !== i) return null;
			let a = cc(r.pv_prognose_kwh);
			return a !== null && a >= 0 ? uc(a, t.hass, 1) : null;
		}), P = Array.from({ length: 12 }, (e, t) => `timed_charge_month_${t + 1}`), F = Q(() => (s.value === "dynamic" ? [
			["number", "max_soc"],
			["number", "price_charge_max_price"],
			["number", "price_charge_hours"],
			["number", "price_charge_neutral_price"]
		] : [
			["number", "max_soc"],
			["number", "timed_charge_max_soc"],
			["number", "timed_charge_min_soc"],
			["switch", "bridge_charge_enabled"],
			...P.map((e) => ["switch", e])
		]).map(([e, t]) => n?.entity(e, t)).filter((e) => e && (e.pending || e.error))), pe = Q(() => {
			let e = o.value?.profiles?.dynamic;
			return e ? [
				e.price_attribute ? `${i.value.attribute}: ${e.price_attribute}` : "",
				e.price_unit === "auto" ? "" : `${i.value.unit}: ${i.value.units[e.price_unit]}`,
				e.pv_factor === 100 ? "" : `${i.value.pvFactor}: ${e.pv_factor}`
			].filter(Boolean).join(" · ") : "";
		}), me = Q(() => {
			let e = o.value?.profiles?.dynamic.price_sensor;
			return `${e ? t.hass?.states[e]?.attributes.friendly_name ?? e : i.value.unset} · ${i.value.feed} ${uc(o.value?.profiles?.dynamic.feed_in_price_ct_kwh, t.hass, 2) ?? "—"} ct/kWh`;
		});
		function I(e, t) {
			_.value = t, O.value && (y.value = e, pn(() => {
				if (M) return;
				let t = ae.value?.querySelector(`[name="dynamic_${e}"]`), n = t?.closest("details");
				n && (n.open = !0), t?.focus();
			}));
		}
		function he(e, t = null) {
			if (M) return;
			v.value = t;
			let n = e && typeof e == "object" && "code" in e ? String(e.code) : "failed";
			x.value = n === "conflict", y.value = null;
			let r = {
				price_sensor_not_configured: ["price_sensor", i.value.missingPriceSensor],
				price_sensor_missing: ["price_sensor", i.value.priceSensorMissing],
				price_unit_unsupported: ["price_unit", i.value.unsupportedPriceUnit],
				pv_sensor_missing: ["pv_sensor", i.value.pvSensorMissing],
				invalid_price_attribute: ["price_attribute", i.value.invalidAttribute],
				invalid_feed_in_price: ["feed", A.value.trim() ? i.value.invalidFeed : i.value.missingFeed],
				invalid_pv_factor: ["pv_factor", i.value.invalidPvFactor]
			}[n];
			if (r) {
				I(...r);
				return;
			}
			_.value = n === "bridge_pv_start_required" ? i.value.bridgePvRequired : n === "conflict" ? i.value.conflict : n === "forbidden" ? i.value.readonly : n === "disconnected" ? i.value.disconnected : n === "invalid_tariff" || n === "invalid_format" ? i.value.invalid : i.value.failed;
		}
		async function ge() {
			let e = ++ce;
			if (!n || !l.value || !c.value) {
				m.value = null, h.value = !1;
				return;
			}
			let t = s.value, r = o.value?.revision, i = g.value;
			h.value = !0;
			try {
				let a = await n.loadTariffSeries(i);
				!M && e === ce && s.value === t && o.value?.revision === r && g.value === i && (m.value = a.tariff_type === t && a.revision === r && a.day === i ? a : null);
			} catch {
				!M && e === ce && (m.value = null);
			} finally {
				!M && e === ce && (h.value = !1);
			}
		}
		U([
			l,
			s,
			() => o.value?.revision,
			g,
			de
		], () => {
			ge();
		}, { immediate: !0 }), U(s, (e, t) => {
			t && e !== t && le.value && (O.value = !1, ne.value = !1, re.value = !1, _.value = null, y.value = null, x.value = !1, ee.value = !0), g.value = "today", m.value = null;
		}), U(l, (e) => {
			e && n?.loadTariff().catch(he);
		}, { immediate: !0 });
		let _e = window.setInterval(() => {
			l.value && (ge(), S.value || n?.loadTariff().catch(() => {}));
		}, 6e4), ve = Q(() => {
			let e = o.value?.profiles?.[D.value];
			return !e || e.feed_in_price_ct_kwh === null ? !0 : "price_sensor" in e ? !e.price_sensor : e.base_price_ct_kwh === null;
		});
		function R() {
			ee.value = !1, D.value = s.value === "dynamic" ? "dynamic" : "time_of_use", te.value = o.value?.revision ?? "", E.value = !0, _.value = null, T.value = !1;
		}
		async function ye() {
			if (n && u.value && !S.value) {
				S.value = !0, w.value = "applying", _.value = null;
				try {
					await n.configureTariff({
						revision: te.value,
						tariff_type: D.value,
						...ve.value ? { automation_enabled: !1 } : {}
					}), M || (E.value = !1, T.value = !0);
				} catch (e) {
					he(e);
				} finally {
					w.value = null, S.value = !1;
				}
			}
		}
		async function be(e) {
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
					he(e, "activation");
				} finally {
					C.value = null, S.value = !1;
				}
			}
		}
		async function xe() {
			if (ee.value = !1, n && !S.value) {
				S.value = !0, w.value = "loading", _.value = null, y.value = null, T.value = !1;
				try {
					let e = await n.loadTariff();
					if (M) return;
					if (!e.can_configure || e.tariff_type !== "dynamic" || !e.profiles) throw { code: "forbidden" };
					k.value = { ...e.profiles.dynamic }, A.value = k.value.feed_in_price_ct_kwh === null ? "" : String(k.value.feed_in_price_ct_kwh).replace(".", r.value ? "," : "."), j.value = String(k.value.pv_factor), ie.value = e.revision, O.value = !0, x.value = !1;
				} catch (e) {
					he(e);
				} finally {
					w.value = null, S.value = !1, await pn(), ae.value?.querySelector("select,input")?.focus();
				}
			}
		}
		function z() {
			O.value = !1, _.value = null, y.value = null, x.value = !1, pn(() => oe.value?.focus());
		}
		async function Se() {
			if (!n || S.value || x.value) return;
			if (y.value = null, !k.value.price_sensor) {
				I("price_sensor", i.value.missingPriceSensor);
				return;
			}
			if (!A.value.trim()) {
				I("feed", i.value.missingFeed);
				return;
			}
			let e = /^\d+(?:[.,]\d{1,2})?$/.test(A.value.trim()) ? Number(A.value.trim().replace(",", ".")) : NaN;
			if (!Number.isFinite(e) || e < 0 || e > 200) {
				I("feed", i.value.invalidFeed);
				return;
			}
			let t = Number(j.value);
			if (String(j.value).trim() === "" || !Number.isInteger(t) || t < 0 || t > 100) {
				I("pv_factor", i.value.invalidPvFactor);
				return;
			}
			S.value = !0, w.value = "saving", _.value = null;
			try {
				await n.configureTariff({
					revision: ie.value,
					tariff_type: "dynamic",
					profile: {
						...k.value,
						price_attribute: k.value.price_attribute?.trim() || null,
						feed_in_price_ct_kwh: e,
						pv_factor: t
					}
				}), M || (z(), T.value = !0);
			} catch (e) {
				he(e);
			} finally {
				w.value = null, S.value = !1;
			}
		}
		async function Ce() {
			if (n && !S.value) {
				S.value = !0, w.value = "loading";
				try {
					await n.loadTariff(), M || (O.value = !1, E.value = !1, _.value = null, y.value = null, x.value = !1);
				} catch (e) {
					he(e);
				} finally {
					w.value = null, S.value = !1;
				}
			}
		}
		function we() {
			re.value = !1, pn(() => se.value?.focus());
		}
		return (t, n) => (K(), q("div", Ru, [
			J("section", zu, [
				J("div", Bu, [J("div", Vu, [
					J("span", null, L(i.value.active), 1),
					J("strong", null, L(d.value), 1),
					J("button", {
						type: "button",
						disabled: !u.value || S.value || le.value,
						"aria-expanded": E.value,
						onClick: R
					}, L(i.value.change), 9, Hu)
				])]),
				E.value ? (K(), q("form", {
					key: 0,
					class: "electricity-choice",
					"aria-busy": w.value === "applying",
					onSubmit: Wa(ye, ["prevent"])
				}, [
					J("fieldset", { disabled: S.value || !l.value }, [J("legend", Gu, L(i.value.active), 1), (K(), q(G, null, W(["time_of_use", "dynamic"], (e) => J("label", { key: e }, [En(J("input", {
						"onUpdate:modelValue": n[0] ||= (e) => D.value = e,
						type: "radio",
						name: "electricity-tariff",
						value: e
					}, null, 8, Ku), [[La, D.value]]), J("span", null, [J("strong", null, L(e === "time_of_use" ? i.value.tou : i.value.dynamic), 1), J("small", null, L(e === "time_of_use" ? i.value.touHint : i.value.dynamicHint), 1)])])), 64))], 8, Wu),
					J("p", null, L(i.value.chooseHint), 1),
					ve.value ? (K(), q("p", qu, L(i.value.incomplete), 1)) : Z("", !0),
					J("div", Ju, [J("button", {
						type: "submit",
						disabled: S.value || !l.value || x.value
					}, L(w.value === "applying" ? i.value.applying : i.value.apply), 9, Yu), J("button", {
						type: "button",
						disabled: S.value,
						onClick: n[1] ||= (e) => {
							E.value = !1, _.value = null;
						}
					}, L(i.value.cancel), 9, Xu)])
				], 40, Uu)) : Z("", !0),
				w.value ? (K(), q("p", Zu, L(i.value[w.value]), 1)) : Z("", !0),
				_.value && !y.value && v.value !== "activation" ? (K(), q("p", Qu, L(_.value), 1)) : Z("", !0),
				x.value && v.value !== "activation" ? (K(), q("button", {
					key: 3,
					type: "button",
					disabled: S.value || !l.value,
					onClick: Ce
				}, L(i.value.reload), 9, $u)) : Z("", !0),
				T.value ? (K(), q("p", ed, L(i.value.saved), 1)) : Z("", !0),
				ee.value ? (K(), q("p", td, L(i.value.tariffChanged), 1)) : Z("", !0),
				!o.value && !_.value ? (K(), q("p", nd, L(i.value.loading), 1)) : Z("", !0),
				c.value ? (K(), q("p", rd, L(s.value === "time_of_use" ? i.value.touIntro : i.value.dynamicIntro), 1)) : Z("", !0)
			]),
			s.value === "time_of_use" ? (K(), ai(Pl, {
				key: 0,
				hass: e.hass,
				compact: "",
				onEditing: n[2] ||= (e) => ne.value = e,
				onSaved: ge
			}, null, 8, ["hass"])) : s.value === "dynamic" ? (K(), q("section", {
				key: 1,
				class: "electricity-card electricity-prices",
				"aria-busy": w.value === "loading" || w.value === "saving"
			}, [
				J("header", null, [J("div", null, [J("h2", null, L(i.value.prices), 1)]), O.value ? Z("", !0) : (K(), q("button", {
					key: 0,
					ref_key: "priceButton",
					ref: oe,
					type: "button",
					disabled: S.value || !u.value || E.value,
					"aria-expanded": O.value,
					onClick: xe
				}, L(w.value === "loading" ? i.value.loading : i.value.edit), 9, ad))]),
				J("p", od, L(me.value), 1),
				O.value ? (K(), q("form", {
					key: 0,
					ref_key: "pricesEditor",
					ref: ae,
					class: "electricity-price-editor",
					"aria-busy": w.value === "saving",
					novalidate: "",
					onSubmit: Wa(Se, ["prevent"])
				}, [
					_.value && y.value ? (K(), q("p", {
						key: 0,
						id: H(b),
						role: "alert",
						class: "electricity-error"
					}, L(_.value), 9, cd)) : Z("", !0),
					J("fieldset", { disabled: S.value || !l.value }, [
						J("p", ud, L(i.value.priceHint), 1),
						J("div", dd, [Y(Ws, {
							modelValue: k.value.price_sensor,
							"onUpdate:modelValue": n[3] ||= (e) => k.value.price_sensor = e,
							hass: e.hass,
							label: i.value.source,
							name: "dynamic_price_sensor",
							invalid: y.value === "price_sensor",
							"described-by": y.value === "price_sensor" ? H(b) : void 0
						}, null, 8, [
							"modelValue",
							"hass",
							"label",
							"invalid",
							"described-by"
						]), J("label", null, [X(L(i.value.feed) + " (ct/kWh)", 1), En(J("input", {
							"onUpdate:modelValue": n[4] ||= (e) => A.value = e,
							type: "text",
							inputmode: "decimal",
							name: "dynamic_feed",
							autocomplete: "off",
							required: "",
							"aria-invalid": y.value === "feed" || void 0,
							"aria-describedby": y.value === "feed" ? H(b) : void 0
						}, null, 8, fd), [[Ia, A.value]])])]),
						J("p", pd, L(i.value.sourceHint), 1),
						J("p", md, L(i.value.feedHint), 1),
						J("div", hd, [Y(Ws, {
							modelValue: k.value.pv_sensor,
							"onUpdate:modelValue": n[5] ||= (e) => k.value.pv_sensor = e,
							hass: e.hass,
							label: i.value.pv,
							name: "dynamic_pv_sensor",
							invalid: y.value === "pv_sensor",
							"described-by": y.value === "pv_sensor" ? H(b) : void 0
						}, null, 8, [
							"modelValue",
							"hass",
							"label",
							"invalid",
							"described-by"
						])]),
						J("p", gd, L(i.value.pvHint), 1),
						pe.value ? (K(), q("p", _d, L(i.value.customSettings) + ": " + L(pe.value), 1)) : Z("", !0),
						J("details", vd, [
							J("summary", null, L(i.value.advanced), 1),
							J("h3", null, L(i.value.sourceSettings), 1),
							J("div", yd, [J("label", null, [X(L(i.value.attribute), 1), En(J("input", {
								"onUpdate:modelValue": n[6] ||= (e) => k.value.price_attribute = e,
								name: "dynamic_price_attribute",
								type: "text",
								autocomplete: "off",
								"aria-invalid": y.value === "price_attribute" || void 0,
								"aria-describedby": y.value === "price_attribute" ? H(b) : void 0
							}, null, 8, bd), [[Ia, k.value.price_attribute]])]), J("label", null, [X(L(i.value.unit), 1), En(J("select", {
								"onUpdate:modelValue": n[7] ||= (e) => k.value.price_unit = e,
								name: "dynamic_price_unit",
								"aria-invalid": y.value === "price_unit" || void 0,
								"aria-describedby": y.value === "price_unit" ? H(b) : void 0
							}, [(K(!0), q(G, null, W(i.value.units, (e, t) => (K(), q("option", {
								key: t,
								value: t
							}, L(e), 9, Sd))), 128))], 8, xd), [[Ra, k.value.price_unit]])])]),
							J("p", Cd, L(i.value.attributeHint), 1),
							J("p", wd, L(i.value.unitHint), 1),
							J("div", Td, [J("label", null, [X(L(i.value.pvFactor), 1), En(J("input", {
								"onUpdate:modelValue": n[8] ||= (e) => j.value = e,
								name: "dynamic_pv_factor",
								type: "number",
								min: "0",
								max: "100",
								step: "1",
								"aria-invalid": y.value === "pv_factor" || void 0,
								"aria-describedby": y.value === "pv_factor" ? H(b) : void 0
							}, null, 8, Ed), [[Ia, j.value]])])]),
							J("p", Dd, L(i.value.pvFactorHint), 1)
						])
					], 8, ld),
					J("div", Od, [J("button", {
						type: "submit",
						disabled: S.value || !l.value || x.value
					}, L(w.value === "saving" ? i.value.saving : i.value.save), 9, kd), J("button", {
						type: "button",
						disabled: S.value,
						onClick: z
					}, L(i.value.cancel), 9, Ad)])
				], 40, sd)) : Z("", !0)
			], 8, id)) : Z("", !0),
			c.value ? (K(), q("section", jd, [
				J("header", null, [J("div", null, [J("h2", null, L(s.value === "time_of_use" ? i.value.touCharging : i.value.charging), 1)]), re.value ? Z("", !0) : (K(), q("button", {
					key: 0,
					ref_key: "chargingButton",
					ref: se,
					type: "button",
					disabled: E.value,
					"aria-expanded": re.value,
					onClick: n[9] ||= (e) => re.value = !0
				}, L(i.value.edit), 9, Md))]),
				s.value === "dynamic" ? (K(), ai(vu, {
					key: 0,
					editing: re.value
				}, null, 8, ["editing"])) : Z("", !0),
				s.value === "time_of_use" ? (K(), ai(Lu, {
					key: 1,
					editing: re.value,
					hass: e.hass
				}, null, 8, ["editing", "hass"])) : Z("", !0),
				re.value ? Z("", !0) : (K(), q("div", Nd, [(K(!0), q(G, null, W(F.value, (e) => (K(), q(G, { key: e?.metadata.entity_id }, [e?.error ? (K(), q("p", Pd, L(e.name) + ": " + L(e.error), 1)) : e?.pending ? (K(), q("p", Fd, L(e.name) + ": " + L(i.value.entityPending), 1)) : Z("", !0)], 64))), 128))])),
				re.value ? (K(), q("div", Id, [J("div", Ld, [J("button", {
					type: "button",
					onClick: we
				}, L(i.value.done), 1)])])) : Z("", !0)
			])) : Z("", !0),
			c.value ? (K(), q("section", Rd, [
				J("h2", null, L(i.value.activate), 1),
				J("p", null, L(s.value === "time_of_use" ? i.value.activationHint : i.value.dynamicActivationHint), 1),
				J("label", {
					class: "electricity-master",
					"aria-busy": C.value !== null
				}, [J("input", {
					type: "checkbox",
					role: "switch",
					checked: p.value === !0,
					"aria-describedby": _.value && v.value === "activation" ? "electricity-master-status electricity-activation-error" : "electricity-master-status",
					disabled: !u.value || S.value || p.value === null || E.value || le.value,
					onChange: be
				}, null, 40, Bd), X(L(i.value.automatic), 1)], 8, zd),
				J("p", Vd, L(C.value === null ? "" : C.value ? i.value.turningOn : i.value.turningOff), 1),
				_.value && v.value === "activation" ? (K(), q("p", Hd, L(_.value), 1)) : Z("", !0),
				x.value && v.value === "activation" ? (K(), q("button", {
					key: 1,
					type: "button",
					disabled: S.value || !l.value,
					onClick: Ce
				}, L(i.value.reload), 9, Ud)) : Z("", !0),
				l.value ? u.value ? le.value || E.value ? (K(), q("p", Kd, L(i.value.editFirst), 1)) : (K(), q("p", qd, L(p.value === null ? i.value.unavailable : p.value ? i.value.activationOn : i.value.activationOff), 1)) : (K(), q("p", Gd, L(i.value.readonly), 1)) : (K(), q("p", Wd, L(i.value.disconnected), 1))
			])) : Z("", !0),
			c.value ? (K(), q("section", Jd, [J("header", null, [J("div", null, [
				J("h2", null, L(i.value.price), 1),
				J("p", Yd, [X(L(ue.value ?? i.value.unavailable), 1), ue.value === null ? Z("", !0) : (K(), q("span", Xd, " ct/kWh"))]),
				J("p", Zd, L(i.value.current) + " · " + L(d.value), 1)
			]), Y(Ho, {
				domain: "sensor",
				"entity-key": s.value === "dynamic" ? "price_charge_status_text" : "timed_charge_discharge_status"
			}, null, 8, ["entity-key"])]), J("details", Qd, [
				J("summary", null, L(i.value.chart), 1),
				s.value === "dynamic" ? (K(), q("div", {
					key: 0,
					class: "electricity-days",
					"aria-label": i.value.price
				}, [(K(), q(G, null, W(["today", "tomorrow"], (e) => J("button", {
					key: e,
					type: "button",
					"aria-pressed": g.value === e,
					onClick: (t) => g.value = e
				}, L(e === "today" ? i.value.today : i.value.tomorrow), 9, ef)), 64))], 8, $d)) : Z("", !0),
				J("p", tf, [X(L(g.value === "today" ? i.value.today : i.value.tomorrow), 1), N.value ? (K(), q("span", nf, " · " + L(N.value), 1)) : Z("", !0)]),
				Y(Zl, {
					series: m.value,
					hass: e.hass,
					loading: h.value
				}, null, 8, [
					"series",
					"hass",
					"loading"
				])
			])])) : Z("", !0),
			c.value ? (K(), q("details", rf, [J("summary", null, L(i.value.details), 1), s.value === "time_of_use" ? (K(), ai(Tc, {
				key: 0,
				hass: e.hass
			}, null, 8, ["hass"])) : (K(), q(G, { key: 1 }, [
				Y(Ho, {
					domain: "sensor",
					"entity-key": "price_charge_active_text"
				}),
				Y(Ho, {
					domain: "sensor",
					"entity-key": "price_charge_status_text"
				}),
				Y(Ho, {
					domain: "sensor",
					"entity-key": "price_charge_next_start"
				}),
				fe.value === null ? Z("", !0) : (K(), q("p", af, [X(L(i.value.plannedPv) + ": ", 1), J("strong", null, L(fe.value) + " kWh", 1)]))
			], 64))])) : Z("", !0)
		]));
	}
}), [["styles", [".electricity-tariff-view{gap:16px;min-width:0;margin-top:20px;display:grid}.electricity-card{border:1px solid var(--divider-color,#ddd);border-radius:var(--ha-card-border-radius,12px);background:var(--card-background-color,#fff);min-width:0;padding:20px}.electricity-card h2{margin:0;font-size:18px}.electricity-card h3{margin:20px 0 10px;font-size:16px}.electricity-card p{margin:10px 0 0;line-height:1.6}.electricity-card button{font:inherit;cursor:pointer;border:1px solid var(--divider-color,#ddd);min-height:44px;color:var(--primary-color,#03a9f4);background:0 0;border-radius:7px;padding:8px 12px}.electricity-card button:disabled{opacity:.5;cursor:default}.electricity-card header,.electricity-tariff-bar__row{justify-content:space-between;align-items:center;gap:16px;display:flex}.electricity-card header>div{flex:1;min-width:0}.electricity-card header>button{white-space:nowrap;flex-shrink:0}.electricity-active{flex-wrap:wrap;align-items:center;gap:10px;display:flex}.electricity-active>span,.electricity-muted{color:var(--secondary-text-color,#666)}.electricity-active>strong{color:var(--primary-color,#03a9f4)}.electricity-master{cursor:pointer;align-items:center;gap:10px;min-height:44px;display:flex}.electricity-master-status:empty{display:none}.electricity-master-status{border-left:3px solid var(--primary-color,#03a9f4);background:var(--secondary-background-color,#f5f5f5);padding:10px 14px;font-weight:500}.electricity-activation .electricity-master{margin-top:12px;font-weight:600}.electricity-price-details{margin-top:16px}.electricity-master[aria-busy=true]{cursor:progress}.electricity-master input{width:22px;height:22px;accent-color:var(--primary-color,#03a9f4);flex-shrink:0}.electricity-choice{border-top:1px solid var(--divider-color,#ddd);margin-top:16px;padding-top:16px}.electricity-choice fieldset{border:0;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;min-width:0;padding:0;display:grid}.electricity-choice fieldset>label{border:1px solid var(--divider-color,#ddd);cursor:pointer;border-radius:8px;gap:12px;padding:14px;display:flex}.electricity-choice input{accent-color:var(--primary-color,#03a9f4);flex-shrink:0;width:20px;height:20px}.electricity-choice strong,.electricity-choice small{display:block}.electricity-choice small{color:var(--secondary-text-color,#666);margin-top:5px;font-size:14px}.electricity-actions{flex-wrap:wrap;gap:8px;margin-top:16px;display:flex}.electricity-actions button[type=submit]{background:var(--primary-color,#03a9f4);color:var(--text-primary-color,#fff)}.electricity-current-price{font-size:32px;font-weight:500;line-height:1.1!important}.electricity-current-price span{font-size:16px;font-weight:400}.electricity-days{gap:6px;margin-top:12px;display:flex}.electricity-days [aria-pressed=true]{background:var(--secondary-background-color,#eee);border-color:var(--primary-color,#03a9f4)}.electricity-day{margin:20px 0!important}.electricity-error{color:var(--error-color,#db4437)}.electricity-price-editor [aria-invalid=true]{border-color:var(--error-color,#db4437);outline:1px solid var(--error-color,#db4437)}.electricity-fields{grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:16px;display:grid}.electricity-fields>label{flex-direction:column;gap:6px;min-width:0;font-size:14px;display:flex}.electricity-fields input,.electricity-fields select{width:100%;min-width:0;min-height:44px;font:inherit;color:var(--primary-text-color,#222);background:var(--card-background-color,#fff);border:1px solid var(--divider-color,#ccc);border-radius:6px;padding:10px}.electricity-price-editor fieldset{border:0;min-width:0;margin:0;padding:0}.electricity-price-advanced{border-top:1px solid var(--divider-color,#ddd);margin-top:16px;padding-top:12px}.electricity-price-advanced>summary{cursor:pointer;align-content:center;min-height:44px}.dynamic-charging-settings .entity-control,.electricity-charging-editor .entity-control{margin-top:12px}.electricity-plan>summary,.electricity-price-details>summary{cursor:pointer;align-content:center;min-height:44px;font-size:18px;font-weight:500;display:list-item}.electricity-plan>.charge-plan{box-shadow:none;border:0;padding:16px 0 0}.electricity-sr-only{clip-path:inset(50%);width:1px;height:1px;position:absolute;overflow:hidden}@media (max-width:700px){.electricity-tariff-bar__row{flex-direction:column;align-items:flex-start}.electricity-fields,.electricity-choice fieldset{grid-template-columns:minmax(0,1fr)}.electricity-card{padding:16px}.electricity-card header{align-items:flex-start}.electricity-current-price{font-size:28px}}@media (max-width:400px){.electricity-prices>header,.electricity-charging>header,.electricity-tariff-view .tariff-plan__header{flex-wrap:wrap}.electricity-prices>header>div,.electricity-charging>header>div,.electricity-tariff-view .tariff-plan__header>h2{flex:100%}.electricity-prices>header>button,.electricity-charging>header>button,.electricity-tariff-view .tariff-plan__header>button{margin-left:auto}}"]]]), sf = { class: "savings-view" }, cf = { class: "savings-overview" }, lf = ["aria-labelledby"], uf = ["id"], df = ["aria-labelledby"], ff = ["id"], pf = {
	key: 0,
	class: "savings-progress"
}, mf = ["id"], hf = { class: "savings-large" }, gf = [
	"role",
	"aria-labelledby",
	"aria-valuemin",
	"aria-valuemax",
	"aria-valuenow"
], _f = {
	key: 1,
	class: "savings-rows"
}, vf = { key: 0 }, yf = { key: 1 }, bf = { key: 2 }, xf = { key: 3 }, Sf = ["aria-label"], Cf = { class: "savings-large" }, wf = ["aria-labelledby"], Tf = ["id"], Ef = ["for"], Df = ["id", "max"], Of = ["for"], kf = ["id", "min"], Af = { type: "submit" }, jf = ["disabled"], Mf = {
	key: 0,
	role: "status"
}, Nf = {
	key: 1,
	role: "alert"
}, Pf = { class: "savings-selected-dates" }, Ff = { class: "savings-large" }, If = ["id"], Lf = { class: "savings-chart-hint" }, Rf = [
	"viewBox",
	"aria-labelledby",
	"aria-describedby"
], zf = ["id"], Bf = [
	"x1",
	"x2",
	"y1",
	"y2"
], Vf = ["x"], Hf = ["x"], Uf = ["x"], Wf = ["x"], Gf = [
	"x",
	"y",
	"width",
	"height"
], Kf = { class: "savings-chart-table" }, qf = { class: "savings-table-scroll" }, Jf = { class: "savings-table" }, Yf = {
	key: 1,
	class: "savings-empty"
}, Xf = { class: "savings-card savings-explanation" }, Zf = {
	key: 1,
	class: "savings-card savings-status",
	role: "status"
}, Qf = /*#__PURE__*/ ko(/* @__PURE__ */ zn({
	__name: "SavingsView",
	props: {
		hass: { type: Object },
		entryId: { type: String }
	},
	setup(e) {
		let t = e, n = kn(no), r = Bn(), i = Q(() => n?.language.value === "de"), a = Q(() => i.value ? {
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
		}), o = Q(() => n?.entity("binary_sensor", "economics_investment_configured")), s = Q(() => n?.entity("sensor", "economics_amortization_progress")), c = Q(() => n?.entity("sensor", "economics_remaining_to_payback")), l = Q(() => n?.entity("sensor", "economics_roi")), u = Q(() => n?.entity("sensor", "economics_net_savings")), d = Q(() => n?.entity("sensor", "economics_status")), f = Q(() => s.value?.available ? cc(s.value.state?.state) : null), p = Q(() => f.value === null ? null : Math.max(0, Math.min(100, f.value))), m = (e) => {
			let n = uc(e, t.hass);
			return n === null ? a.value.unavailable : `${n} €`;
		}, h = (e) => dc(e, t.hass) ?? a.value.unavailable, g = (e) => dc(`${e}T12:00:00Z`, t.hass, {
			dateStyle: "medium",
			timeZone: "UTC"
		}) ?? e, _ = Q(() => {
			let e = d.value?.available ? d.value.state?.state : void 0;
			return e === "active" ? null : e === "disabled" || e === "price_unavailable" || e === "origin_unavailable" || e === "partial_price_coverage" || e === "storage_error" ? a.value[e] : a.value.missing;
		}), v = mc(() => t.hass, () => t.entryId, () => u.value?.metadata.entity_id), y = /* @__PURE__ */ V(""), b = /* @__PURE__ */ V(""), x = null;
		U(v.data, (e) => {
			e && ((!y.value && !b.value || y.value === x?.start && b.value === x?.end) && (y.value = e.selected.start_date, b.value = e.selected.end_date), x = {
				start: e.selected.start_date,
				end: e.selected.end_date
			});
		}), U(() => t.entryId, () => {
			y.value = "", b.value = "", x = null;
		});
		let S = Q(() => v.error.value === "invalid" ? a.value.invalid : v.error.value === "failed" ? a.value.failed : v.error.value === "unavailable" || v.data.value?.status === "recorder_unavailable" ? a.value.noRecorder : null), C = [
			"day",
			"week",
			"month",
			"year"
		], w = Q(() => v.data.value?.selected.buckets ?? []), T = /* @__PURE__ */ V(null), ee = /* @__PURE__ */ V(720);
		U(T, (e, t, n) => {
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
		let E = Q(() => {
			let e = w.value.map((e) => cc(e.change)), n = Math.max(0, ...e.map((e) => e ?? 0)), r = Math.min(0, ...e.map((e) => e ?? 0)), i = n - r || 1, a = (e) => 20 + (n - e) / i * 180, o = v.data.value?.selected, s = Date.parse(o?.start ?? ""), c = Date.parse(o?.end ?? ""), l = c - s, u = uc(n, t.hass) ?? "", d = uc(r, t.hass) ?? "", f = Math.max(56, Math.max(u.length, d.length) * 7.1 + 12), p = ee.value - 24, m = Math.max(1, p - f), g = (e) => f + Math.max(0, Math.min(1, (Date.parse(e) - s) / l)) * m;
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
		}), D = Q(() => w.value.some((e) => cc(e.change) !== null)), te = (e) => dc(e, t.hass, v.data.value?.selected.period === "hour" ? { timeStyle: "short" } : v.data.value?.selected.period === "month" ? {
			month: "short",
			year: "numeric"
		} : {
			day: "2-digit",
			month: "short"
		}) ?? e;
		return (t, i) => (K(), q("div", sf, [
			J("div", cf, [o.value?.available && o.value.state?.state === "off" ? (K(), q("section", {
				key: 0,
				class: "savings-card savings-payback",
				"aria-labelledby": `${H(r)}-investment`
			}, [J("h2", { id: `${H(r)}-investment` }, L(a.value.payback), 9, uf), J("p", null, L(a.value.investment), 1)], 8, lf)) : o.value?.available && o.value.state?.state === "on" && (s.value || c.value || l.value || u.value || d.value) ? (K(), q("section", {
				key: 1,
				class: "savings-card savings-payback",
				"aria-labelledby": `${H(r)}-payback`
			}, [
				J("h2", { id: `${H(r)}-payback` }, L(a.value.payback), 9, ff),
				s.value ? (K(), q("div", pf, [
					J("h3", { id: `${H(r)}-progress` }, L(s.value.name), 9, mf),
					J("p", hf, L(f.value === null ? a.value.unavailable : `${H(uc)(f.value, e.hass)} %`), 1),
					J("div", {
						class: "savings-progress__track",
						role: p.value === null ? void 0 : "meter",
						"aria-labelledby": `${H(r)}-progress`,
						"aria-valuemin": p.value === null ? void 0 : 0,
						"aria-valuemax": p.value === null ? void 0 : 100,
						"aria-valuenow": p.value ?? void 0
					}, [p.value === null ? Z("", !0) : (K(), q("span", {
						key: 0,
						style: M({ width: `${p.value}%` })
					}, null, 4))], 8, gf)
				])) : Z("", !0),
				c.value || l.value || u.value || d.value ? (K(), q("dl", _f, [
					c.value ? (K(), q("div", vf, [J("dt", null, L(c.value.name), 1), J("dd", null, L(m(c.value.available ? c.value.state?.state : null)), 1)])) : Z("", !0),
					l.value ? (K(), q("div", yf, [J("dt", null, L(a.value.prior), 1), J("dd", null, L(m(l.value.available ? l.value.state?.attributes.prior_result_eur ?? l.value.state?.attributes.prior_result_eur_formatted : null)), 1)])) : Z("", !0),
					u.value ? (K(), q("div", bf, [J("dt", null, L(a.value.net), 1), J("dd", null, L(m(u.value.available ? u.value.state?.state : null)), 1)])) : Z("", !0),
					d.value ? (K(), q("div", xf, [J("dt", null, L(a.value.started), 1), J("dd", null, L(h(d.value.available ? d.value.state?.attributes.economics_started_at : null)), 1)])) : Z("", !0)
				])) : Z("", !0)
			], 8, df)) : Z("", !0), u.value ? (K(), q("section", {
				key: 2,
				class: "savings-periods",
				"aria-label": a.value.periods
			}, [(K(), q(G, null, W(C, (e) => J("article", {
				key: e,
				class: "savings-card"
			}, [J("h2", null, L(a.value[e]), 1), J("p", Cf, L(H(v).loading.value ? "…" : m(H(v).data.value?.periods[e].change)), 1)])), 64))], 8, Sf)) : Z("", !0)]),
			Y(Pl, {
				hass: e.hass,
				class: "savings-tariff"
			}, null, 8, ["hass"]),
			u.value ? (K(), q("section", {
				key: 0,
				class: "savings-card savings-range",
				"aria-labelledby": `${H(r)}-range`
			}, [
				J("h2", { id: `${H(r)}-range` }, L(a.value.range), 9, Tf),
				J("form", {
					class: "savings-dates",
					onSubmit: i[3] ||= Wa((e) => H(v).select(y.value, b.value), ["prevent"])
				}, [
					J("label", { for: `${H(r)}-from` }, [X(L(a.value.from), 1), En(J("input", {
						id: `${H(r)}-from`,
						"onUpdate:modelValue": i[0] ||= (e) => y.value = e,
						type: "date",
						required: "",
						max: b.value || void 0
					}, null, 8, Df), [[Ia, y.value]])], 8, Ef),
					J("label", { for: `${H(r)}-to` }, [X(L(a.value.to), 1), En(J("input", {
						id: `${H(r)}-to`,
						"onUpdate:modelValue": i[1] ||= (e) => b.value = e,
						type: "date",
						required: "",
						min: y.value || void 0
					}, null, 8, kf), [[Ia, b.value]])], 8, Of),
					J("button", Af, L(a.value.apply), 1),
					J("button", {
						type: "button",
						disabled: H(v).loading.value,
						onClick: i[2] ||= (...e) => H(v).refresh && H(v).refresh(...e)
					}, L(a.value.refresh), 9, jf)
				], 32),
				H(v).loading.value ? (K(), q("p", Mf, L(a.value.loading), 1)) : S.value ? (K(), q("p", Nf, L(S.value), 1)) : H(v).data.value ? (K(), q(G, { key: 2 }, [
					J("p", Pf, L(g(H(v).data.value.selected.start_date)) + " – " + L(g(H(v).data.value.selected.end_date)), 1),
					J("h3", null, L(a.value.selected), 1),
					J("p", Ff, L(m(H(v).data.value.selected.change)), 1),
					J("h3", { id: `${H(r)}-chart` }, L(a.value.chart), 9, If),
					J("p", Lf, L(a.value.chartHint), 1),
					D.value ? (K(), q(G, { key: 0 }, [(K(), q("svg", {
						ref_key: "chartElement",
						ref: T,
						class: "savings-chart",
						viewBox: `0 0 ${ee.value} 240`,
						role: "img",
						"aria-labelledby": `${H(r)}-chart`,
						"aria-describedby": `${H(r)}-chart-description`
					}, [
						J("desc", { id: `${H(r)}-chart-description` }, L(a.value.net) + ": " + L(m(H(v).data.value.selected.change)) + ". " + L(a.value.table) + ". ", 9, zf),
						J("line", {
							x1: E.value.left - 2,
							x2: E.value.right + 2,
							y1: E.value.zero,
							y2: E.value.zero,
							class: "savings-chart__axis"
						}, null, 8, Bf),
						J("text", {
							x: E.value.left - 8,
							y: "24",
							"text-anchor": "end"
						}, L(E.value.highLabel), 9, Vf),
						J("text", {
							x: E.value.left - 8,
							y: "204",
							"text-anchor": "end"
						}, L(E.value.lowLabel), 9, Hf),
						i[4] ||= J("text", {
							x: "10",
							y: "226"
						}, "EUR", -1),
						w.value.length ? (K(), q("text", {
							key: 0,
							x: E.value.left,
							y: "226"
						}, L(te(E.value.start)), 9, Uf)) : Z("", !0),
						w.value.length > 1 ? (K(), q("text", {
							key: 1,
							x: E.value.right,
							y: "226",
							"text-anchor": "end"
						}, L(te(E.value.end)), 9, Wf)) : Z("", !0),
						(K(!0), q(G, null, W(E.value.bars, (e, t) => (K(), q("rect", {
							key: t,
							x: e.x,
							y: e.y,
							width: e.width,
							height: e.height,
							class: de(["savings-chart__bar", { "savings-chart__bar--negative": (e.value ?? 0) < 0 }])
						}, [J("title", null, L(e.label) + ": " + L(m(e.value)), 1)], 10, Gf))), 128))
					], 8, Rf)), J("details", Kf, [J("summary", null, L(a.value.table), 1), J("div", qf, [J("table", Jf, [J("thead", null, [J("tr", null, [
						J("th", null, L(a.value.from), 1),
						J("th", null, L(a.value.to), 1),
						J("th", null, L(a.value.net), 1)
					])]), J("tbody", null, [(K(!0), q(G, null, W(E.value.bars, (e, t) => (K(), q("tr", { key: t }, [
						J("td", null, L(e.label), 1),
						J("td", null, L(h(e.end)), 1),
						J("td", null, L(m(e.value)), 1)
					]))), 128))])])])])], 64)) : Z("", !0),
					!D.value || H(v).data.value.selected.change === null ? (K(), q("p", Yf, L(H(v).data.value.selected.change === null ? a.value.noData : a.value.noChartData), 1)) : Z("", !0)
				], 64)) : Z("", !0)
			], 8, wf)) : Z("", !0),
			J("details", Xf, [
				J("summary", null, L(a.value.explain), 1),
				J("p", null, L(a.value.netHint), 1),
				J("p", null, L(a.value.calendarHint), 1),
				J("p", null, L(a.value.rangeHint), 1)
			]),
			_.value && H(n)?.ready.value ? (K(), q("p", Zf, L(_.value), 1)) : Z("", !0)
		]));
	}
}), [["styles", [".savings-view{gap:20px;min-width:0;margin-top:24px;display:grid}.savings-overview{display:contents}.savings-card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.savings-card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.savings-card h3{margin:20px 0 8px;font-size:16px;font-weight:500}.savings-card p{overflow-wrap:anywhere;line-height:1.6}.savings-card p:last-child{margin-bottom:0}.savings-large{font-variant-numeric:tabular-nums;margin:0 0 12px;font-size:28px;font-weight:500}.savings-progress__track{background:var(--divider-color,#e0e0e0);border-radius:8px;height:16px;overflow:hidden}.savings-progress__track span{background:var(--info-color,#039be5);height:100%;display:block}.savings-rows{margin:20px 0 0}.savings-rows>div{border-bottom:1px solid var(--divider-color,#e0e0e0);justify-content:space-between;gap:16px;padding:12px 0;line-height:1.5;display:flex}.savings-rows>div:last-child{border-bottom:0;padding-bottom:0}.savings-rows dd{text-align:right;font-variant-numeric:tabular-nums;margin:0}.savings-periods{grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:16px;display:grid}.savings-periods h2{font-size:16px}.savings-table-scroll{overflow-x:auto}.savings-table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%;line-height:1.5}.savings-table th,.savings-table td{text-align:left;border-bottom:1px solid var(--divider-color,#e0e0e0);padding:10px 8px}.savings-table th:last-child,.savings-table td:last-child{text-align:right}.savings-dates{flex-wrap:wrap;align-items:end;gap:16px;display:flex}.savings-dates label{flex:180px;gap:8px;min-width:0;display:grid}.savings-dates input,.savings-dates button{box-sizing:border-box;font:inherit;border:1px solid var(--divider-color,#bdbdbd);background:var(--ha-card-background,var(--card-background-color,#fff));min-height:44px;color:var(--primary-text-color,#212121);border-radius:6px;padding:10px 12px}.savings-dates input{--lightningcss-light:initial;--lightningcss-dark: ;color-scheme:light dark;width:100%}@media (prefers-color-scheme:dark){.savings-dates input{--lightningcss-light: ;--lightningcss-dark:initial}}.savings-dates button{cursor:pointer;color:var(--primary-color,#0288d1)}.savings-dates button:disabled{opacity:.6;cursor:default}.savings-dates :focus-visible,.savings-card summary:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:3px}.savings-selected-dates,.savings-empty{color:var(--secondary-text-color,#666)}.savings-chart{width:100%;height:auto;display:block;overflow:visible}.savings-chart text{fill:var(--secondary-text-color,#666);font-size:12px}.savings-chart__axis{stroke:var(--primary-text-color,#212121);stroke-width:1px}.savings-chart__bar{fill:var(--info-color,#039be5)}.savings-chart__bar--negative{fill:var(--error-color,#db4437)}.savings-card summary{cursor:pointer;min-height:24px;font-weight:500;line-height:1.6}.savings-chart-table{margin-top:16px}.savings-status{margin:0;line-height:1.6}@container sax-content (width>=860px){.savings-view{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;gap:16px;margin-top:16px}.savings-view>*{grid-column:1/-1}.savings-overview{gap:16px;min-width:0;display:grid}.savings-overview:empty{display:none}.savings-view:has(>.savings-overview>section):has(>.savings-tariff)>:is(.savings-overview,.savings-tariff){grid-column:auto}.savings-card{padding:18px}.savings-card h2{margin-bottom:12px;font-size:16px}.savings-card h3{margin-top:16px;font-size:14px}.savings-card p{margin-top:10px;line-height:1.5}.savings-progress h3{margin-top:0}.savings-card .savings-large{margin-top:0;margin-bottom:8px;font-size:24px}.savings-rows{margin-top:12px}.savings-rows>div{gap:12px;padding:8px 0}.savings-rows dt{min-width:0}.savings-rows dd{flex-shrink:0;max-width:58%}.savings-periods{grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.savings-view:has(>.savings-tariff) .savings-periods{grid-template-columns:repeat(2,minmax(0,1fr))}.savings-periods .savings-card{padding:14px 16px}.savings-periods h2{margin-bottom:6px;font-size:14px}.savings-periods .savings-large{margin-bottom:0;font-size:22px}.savings-table th,.savings-table td{padding:7px 8px}.savings-dates{gap:12px}.savings-dates label{flex:0 220px;gap:6px}.savings-range .savings-selected-dates{margin-bottom:8px}.savings-range .savings-chart-hint{margin-top:0;margin-bottom:8px}.savings-chart-table{margin-top:12px}}@media (max-width:600px){.savings-view{gap:16px}.savings-card{padding:20px}.savings-rows>div{flex-wrap:wrap;gap:4px 16px}.savings-rows dd{margin-left:auto}}"]]]), $f = ["lang"], ep = { class: "header" }, tp = ["aria-label"], np = ["aria-label"], rp = [
	"href",
	"aria-current",
	"onClick"
], ip = {
	key: 0,
	class: "status",
	role: "alert"
}, ap = { class: "introduction" }, op = {
	key: 0,
	class: "status",
	role: "status"
}, sp = {
	key: 1,
	class: "status",
	role: "status"
}, cp = {
	key: 6,
	class: "status"
}, lp = ["href"], up = /* @__PURE__ */ Ea(/* @__PURE__ */ ko(/* @__PURE__ */ zn({
	__name: "Panel.ce",
	props: {
		hass: { type: Object },
		narrow: { type: Boolean },
		panel: { type: Object },
		route: { type: Object }
	},
	setup(e) {
		let t = e, n = ka(), r = oo(() => t.hass, () => t.panel?.config?.entry_id);
		On(no, r);
		let i = Q(() => t.hass?.language.toLowerCase().startsWith("de") ? "de" : "en"), a = Q(() => eo[i.value]), o = Q(() => !t.hass?.kioskMode && (t.narrow || t.hass?.dockedSidebar === "always_hidden")), s = Q(() => `/${t.panel?.url_path || "sax-power-vue"}`), c = /* @__PURE__ */ V(t.route?.path ?? window.location.pathname), l = Qa, u = Q(() => $a(c.value, s.value)), d = Q(() => ["dynamisches-laden", "ladeautomatik"].includes(u.value) ? "stromtarif" : u.value);
		U([
			() => r.ready.value,
			() => {
				let e = r.entity("sensor", "economics_current_import_price")?.state?.attributes ?? {};
				return JSON.stringify([
					e.tariff_type,
					e.base_price_eur_kwh,
					e.feed_in_price_eur_kwh,
					e.windows,
					e.price_sensor_entity_id
				]);
			},
			() => r.entity("switch", "timed_charge_enabled")?.state?.state,
			() => r.entity("switch", "price_charge_enabled")?.state?.state
		], ([e]) => {
			e && r.loadTariff().catch(() => {});
		}, { immediate: !0 });
		let f = Q(() => Qa.find((e) => e.path === d.value)), p = /* @__PURE__ */ V();
		U(() => t.route?.path, (e) => {
			e !== void 0 && (c.value = e);
		}), U([u, d], ([e, t]) => {
			if (e === t) return;
			let n = `${s.value}/${t}`;
			c.value = n, window.history.replaceState(null, "", n), window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: !0 } })), pn(() => p.value?.focus());
		}, { immediate: !0 });
		function m() {
			c.value = window.location.pathname;
		}
		Xn(() => {
			window.addEventListener("popstate", m), window.addEventListener("location-changed", m);
		}), Zn(() => {
			window.removeEventListener("popstate", m), window.removeEventListener("location-changed", m);
		});
		function h(e, t) {
			e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || (e.preventDefault(), window.location.pathname !== t && (window.history.pushState(null, "", t), window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: !1 } }))), m(), pn(() => p.value?.focus()));
		}
		function g() {
			n?.dispatchEvent(new CustomEvent("hass-toggle-menu", {
				bubbles: !0,
				composed: !0
			}));
		}
		return (t, n) => (K(), q("div", {
			class: de(["dashboard", { narrow: e.narrow }]),
			lang: i.value
		}, [
			J("header", ep, [o.value ? (K(), q("button", {
				key: 0,
				class: "menu-button",
				type: "button",
				"aria-label": a.value.menu,
				onClick: g
			}, [...n[1] ||= [J("svg", {
				viewBox: "0 0 24 24",
				"aria-hidden": "true"
			}, [J("path", { d: "M4 6h16M4 12h16M4 18h16" })], -1)]], 8, tp)) : Z("", !0), n[2] ||= J("div", { class: "brand" }, [J("svg", {
				class: "brand-icon",
				viewBox: "0 0 24 24",
				"aria-hidden": "true"
			}, [J("path", { d: "M9 3h6M8 5h8a1 1 0 0 1 1 1v14H7V6a1 1 0 0 1 1-1Z" }), J("path", { d: "m13 8-3 5h4l-3 5" })]), J("span", null, "SAX Power")], -1)]),
			J("nav", {
				class: "navigation",
				"aria-label": a.value.navigation
			}, [(K(!0), q(G, null, W(H(l), (e) => (K(), q("a", {
				key: e.path,
				href: `${s.value}/${e.path}`,
				"aria-current": d.value === e.path ? "page" : void 0,
				onClick: (t) => h(t, `${s.value}/${e.path}`)
			}, L(e[i.value]), 9, rp))), 128))], 8, np),
			J("main", null, [
				H(r).error.value ? (K(), q("p", ip, L(H(r).error.value), 1)) : Z("", !0),
				J("p", ap, L(a.value.introduction), 1),
				(K(), q("section", {
					key: e.panel?.config?.entry_id,
					class: "section",
					"aria-labelledby": "section-heading"
				}, [J("h1", {
					id: "section-heading",
					ref_key: "heading",
					ref: p,
					tabindex: "-1"
				}, L(f.value?.[i.value] ?? a.value.notFound), 513), e.hass ? e.panel?.config?.entry_id ? d.value === "allgemein" ? (K(), ai(Xo, { key: 2 })) : d.value === "netzdienliches-laden" ? (K(), ai(sc, {
					key: 3,
					hass: e.hass
				}, null, 8, ["hass"])) : d.value === "stromtarif" ? (K(), ai(of, {
					key: 4,
					hass: e.hass
				}, null, 8, ["hass"])) : d.value === "ersparnis" ? (K(), ai(Qf, {
					key: 5,
					hass: e.hass,
					"entry-id": e.panel?.config?.entry_id
				}, null, 8, ["hass", "entry-id"])) : (K(), q("div", cp, [J("p", null, L(a.value.notFoundDescription), 1), J("a", {
					href: `${s.value}/allgemein`,
					onClick: n[0] ||= (e) => h(e, `${s.value}/allgemein`)
				}, L(a.value.returnToOverview), 9, lp)])) : (K(), q("p", sp, L(a.value.missingEntry), 1)) : (K(), q("p", op, L(a.value.loading), 1))]))
			])
		], 10, $f));
	}
}), [["styles", [":host{height:100%;color:var(--primary-text-color,#212121);background:var(--primary-background-color,#fafafa);font-family:var(--paper-font-body1_-_font-family,Roboto, sans-serif);font-size:14px;display:block}*{box-sizing:border-box}.dashboard{min-height:100%;container:sax-panel/inline-size}.header{background:var(--app-header-background-color,var(--primary-color,#03a9f4));min-height:64px;color:var(--app-header-text-color,#fff);align-items:center;gap:14px;padding:8px 24px;display:flex}.brand{align-items:center;gap:10px;font-size:20px;font-weight:500;display:flex}.header svg{fill:none;stroke:currentColor;stroke-width:1.7px;stroke-linecap:round;stroke-linejoin:round}.brand-icon{width:30px;height:30px}.menu-button{width:44px;height:44px;color:inherit;cursor:pointer;background:0 0;border:0;border-radius:50%;place-items:center;margin-left:-10px;display:grid}.menu-button svg{width:24px;height:24px}.navigation{border-bottom:1px solid var(--divider-color,#e0e0e0);background:var(--card-background-color,#fff);padding:0 16px;display:flex;overflow-x:auto}.navigation a{min-height:56px;color:var(--secondary-text-color,#666);white-space:nowrap;border-bottom:3px solid #0000;align-items:center;padding:12px 16px;text-decoration:none;display:flex}.navigation a[aria-current=page]{border-color:var(--primary-color,#03a9f4);color:var(--primary-text-color,#212121);font-weight:600}a{color:var(--primary-text-color,#212121);text-underline-offset:3px}a:focus-visible,button:focus-visible{outline-offset:-4px;outline:2px solid}main{max-width:1120px;margin:0 auto;padding:28px 24px 48px}.introduction{color:var(--secondary-text-color,#666);margin:0 0 24px;line-height:1.6}.section{overflow-wrap:anywhere;border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));box-shadow:var(--ha-card-box-shadow,none);padding:28px;container:sax-content/inline-size}h1{margin:0;font-size:24px;font-weight:500;line-height:1.35}h1:focus{outline:none}h2{margin:0 0 12px;font-size:18px;font-weight:500;line-height:1.5}.status{margin-top:24px;line-height:1.7}.narrow .header{padding-left:16px;padding-right:16px}.narrow main{padding:16px 12px 32px}@container sax-panel (width>=940px){.header{min-height:56px;padding:6px 20px}.navigation a{min-height:48px;padding:8px 14px}main{max-width:1360px;padding:16px 20px 20px}.introduction{margin-bottom:12px}.section{padding:20px}h1{font-size:22px}}@media (max-width:600px){.header{gap:8px;padding:8px 16px}.brand{gap:6px;font-size:18px}.brand-icon{display:none}.navigation{padding:0 4px}main{padding:16px 12px 32px}.introduction{margin-bottom:16px}.section{padding:20px}h1{font-size:22px}}"]]]));
customElements.get("sax-power-vue-panel") || customElements.define("sax-power-vue-panel", up);
//#endregion
export { up as SaxPowerVuePanel };
