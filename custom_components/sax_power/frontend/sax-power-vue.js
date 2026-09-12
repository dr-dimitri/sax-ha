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
}, E = /-\w/g, D = ee((e) => e.replace(E, (e) => e.slice(1).toUpperCase())), O = /\B([A-Z])/g, k = ee((e) => e.replace(O, "-$1").toLowerCase()), A = ee((e) => e.charAt(0).toUpperCase() + e.slice(1)), te = ee((e) => e ? `on${A(e)}` : ""), j = (e, t) => !Object.is(e, t), ne = (e, ...t) => {
	for (let n = 0; n < e.length; n++) e[n](...t);
}, re = (e, t, n, r = !1) => {
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
}, M, oe = () => M ||= typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : typeof global < "u" ? global : {};
function se(e) {
	if (d(e)) {
		let t = {};
		for (let n = 0; n < e.length; n++) {
			let r = e[n], i = g(r) ? de(r) : se(r);
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
	if (n = _(e), r = _(t), n || r) return e === t;
	if (n = d(e), r = d(t), n || r) return n && r ? he(e, t) : !1;
	if (n = v(e), r = v(t), n || r) {
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
var ye = (e) => !!(e && e.__v_isRef === !0), P = (e) => g(e) ? e : e == null ? "" : d(e) || v(e) && (e.toString === b || !h(e.toString)) ? ye(e) ? P(e.value) : JSON.stringify(e, be, 2) : String(e), be = (e, t) => ye(t) ? be(e, t.value) : f(t) ? { [`Map(${t.size})`]: [...t.entries()].reduce((e, [t, n], r) => (e[xe(t, r) + " =>"] = n, e), {}) } : p(t) ? { [`Set(${t.size})`]: [...t.values()].map((e) => xe(e)) } : _(t) ? xe(t) : v(t) && !d(t) && !C(t) ? String(t) : t, xe = (e, t = "") => _(e) ? `Symbol(${e.description ?? t})` : e, F, Se = class {
	constructor(e = !1) {
		this.detached = e, this._active = !0, this._on = 0, this.effects = [], this.cleanups = [], this._isPaused = !1, this._warnOnRun = !0, this.__v_skip = !0, !e && F && (F.active ? (this.parent = F, this.index = (F.scopes || (F.scopes = [])).push(this) - 1) : (this._active = !1, this._warnOnRun = !1));
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
			let t = F;
			try {
				return F = this, e();
			} finally {
				F = t;
			}
		}
	}
	on() {
		++this._on === 1 && (this.prevScope = F, F = this);
	}
	off() {
		if (this._on > 0 && --this._on === 0) {
			if (F === this) F = this.prevScope;
			else {
				let e = F;
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
	return F;
}
function we(e, t = !1) {
	F && F.cleanups.push(e);
}
var I, Te = /* @__PURE__ */ new WeakSet(), Ee = class {
	constructor(e) {
		this.fn = e, this.deps = void 0, this.depsTail = void 0, this.flags = 5, this.next = void 0, this.cleanup = void 0, this.scheduler = void 0, F && (F.active ? F.effects.push(this) : this.flags &= -2);
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
		let e = I, t = ze;
		I = this, ze = !0;
		try {
			return this.fn();
		} finally {
			Pe(this), I = e, ze = t, this.flags &= -3;
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
	let t = e.dep, n = I, r = ze;
	I = e, ze = !0;
	try {
		Ne(e);
		let n = e.fn(e._value);
		(t.version === 0 || j(n, e._value)) && (e.flags |= 128, e._value = n, t.version++);
	} catch (e) {
		throw t.version++, e;
	} finally {
		I = n, ze = r, Pe(e), e.flags &= -3;
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
		let e = I;
		I = void 0;
		try {
			t();
		} finally {
			I = e;
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
		if (!I || !ze || I === this.computed) return;
		let t = this.activeLink;
		if (t === void 0 || t.sub !== I) t = this.activeLink = new Ge(I, this), I.deps ? (t.prevDep = I.depsTail, I.depsTail.nextDep = t, I.depsTail = t) : I.deps = I.depsTail = t, qe(t);
		else if (t.version === -1 && (t.version = this.version, t.nextDep)) {
			let e = t.nextDep;
			e.prevDep = t.prevDep, t.prevDep && (t.prevDep.nextDep = e), t.prevDep = I.depsTail, t.nextDep = void 0, I.depsTail.nextDep = t, I.depsTail = t, I.deps === t && (I.deps = e);
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
function L(e, t, n) {
	if (ze && I) {
		let t = Je.get(e);
		t || Je.set(e, t = /* @__PURE__ */ new Map());
		let r = t.get(n);
		r || (t.set(n, r = new Ke()), r.map = t, r.key = n), r.track();
	}
}
function Qe(e, t, n, r, i, a) {
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
		let i = d(e), a = i && w(n);
		if (i && n === "length") {
			let e = Number(r);
			o.forEach((t, n) => {
				(n === "length" || n === Ze || !_(n) && n >= e) && s(t);
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
function $e(e) {
	let t = /* @__PURE__ */ R(e);
	return t === e ? t : (L(t, "iterate", Ze), /* @__PURE__ */ Rt(e) ? t : t.map(Vt));
}
function et(e) {
	return L(e = /* @__PURE__ */ R(e), "iterate", Ze), e;
}
function tt(e, t) {
	return /* @__PURE__ */ Lt(e) ? Ht(/* @__PURE__ */ It(e) ? Vt(t) : t) : Vt(t);
}
var nt = {
	__proto__: null,
	[Symbol.iterator]() {
		return rt(this, Symbol.iterator, (e) => tt(this, e));
	},
	concat(...e) {
		return $e(this).concat(...e.map((e) => d(e) ? $e(e) : e));
	},
	entries() {
		return rt(this, "entries", (e) => (e[1] = tt(this, e[1]), e));
	},
	every(e, t) {
		return at(this, "every", e, t, void 0, arguments);
	},
	filter(e, t) {
		return at(this, "filter", e, t, (e) => e.map((e) => tt(this, e)), arguments);
	},
	find(e, t) {
		return at(this, "find", e, t, (e) => tt(this, e), arguments);
	},
	findIndex(e, t) {
		return at(this, "findIndex", e, t, void 0, arguments);
	},
	findLast(e, t) {
		return at(this, "findLast", e, t, (e) => tt(this, e), arguments);
	},
	findLastIndex(e, t) {
		return at(this, "findLastIndex", e, t, void 0, arguments);
	},
	forEach(e, t) {
		return at(this, "forEach", e, t, void 0, arguments);
	},
	includes(...e) {
		return st(this, "includes", e);
	},
	indexOf(...e) {
		return st(this, "indexOf", e);
	},
	join(e) {
		return $e(this).join(e);
	},
	lastIndexOf(...e) {
		return st(this, "lastIndexOf", e);
	},
	map(e, t) {
		return at(this, "map", e, t, void 0, arguments);
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
		return at(this, "some", e, t, void 0, arguments);
	},
	splice(...e) {
		return ct(this, "splice", e);
	},
	toReversed() {
		return $e(this).toReversed();
	},
	toSorted(e) {
		return $e(this).toSorted(e);
	},
	toSpliced(...e) {
		return $e(this).toSpliced(...e);
	},
	unshift(...e) {
		return ct(this, "unshift", e);
	},
	values() {
		return rt(this, "values", (e) => tt(this, e));
	}
};
function rt(e, t, n) {
	let r = et(e), i = r[t]();
	return r !== e && !/* @__PURE__ */ Rt(e) && (i._next = i.next, i.next = () => {
		let e = i._next();
		return e.done || (e.value = n(e.value)), e;
	}), i;
}
var it = Array.prototype;
function at(e, t, n, r, i, a) {
	let o = et(e), s = o !== e && !/* @__PURE__ */ Rt(e), c = o[t];
	if (c !== it[t]) {
		let t = c.apply(e, a);
		return s ? Vt(t) : t;
	}
	let l = n;
	o !== e && (s ? l = function(t, r) {
		return n.call(this, tt(e, t), r, e);
	} : n.length > 2 && (l = function(t, r) {
		return n.call(this, t, r, e);
	}));
	let u = c.call(o, l, r);
	return s && i ? i(u) : u;
}
function ot(e, t, n, r) {
	let i = et(e), a = i !== e && !/* @__PURE__ */ Rt(e), o = n, s = !1;
	i !== e && (a ? (s = r.length === 0, o = function(t, r, i) {
		return s && (s = !1, t = tt(e, t)), n.call(this, t, tt(e, r), i, e);
	}) : n.length > 3 && (o = function(t, r, i) {
		return n.call(this, t, r, i, e);
	}));
	let c = i[t](o, ...r);
	return s ? tt(e, c) : c;
}
function st(e, t, n) {
	let r = /* @__PURE__ */ R(e);
	L(r, "iterate", Ze);
	let i = r[t](...n);
	return (i === -1 || i === !1) && /* @__PURE__ */ zt(n[0]) ? (n[0] = /* @__PURE__ */ R(n[0]), r[t](...n)) : i;
}
function ct(e, t, n = []) {
	Ve(), je();
	let r = (/* @__PURE__ */ R(e))[t].apply(e, n);
	return Me(), He(), r;
}
var lt = /* @__PURE__ */ e("__proto__,__v_isRef,__isVue"), ut = new Set(/* @__PURE__ */ Object.getOwnPropertyNames(Symbol).filter((e) => e !== "arguments" && e !== "caller").map((e) => Symbol[e]).filter(_));
function dt(e) {
	_(e) || (e = String(e));
	let t = /* @__PURE__ */ R(this);
	return L(t, "has", e), t.hasOwnProperty(e);
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
			if (a && (e = nt[t])) return e;
			if (t === "hasOwnProperty") return dt;
		}
		let o = Reflect.get(e, t, /* @__PURE__ */ z(e) ? e : n);
		if ((_(t) ? ut.has(t) : lt(t)) || (r || L(e, "get", t), i)) return o;
		if (/* @__PURE__ */ z(o)) {
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
			let e = /* @__PURE__ */ Lt(i);
			if (!/* @__PURE__ */ Rt(n) && !/* @__PURE__ */ Lt(n) && (i = /* @__PURE__ */ R(i), n = /* @__PURE__ */ R(n)), !a && /* @__PURE__ */ z(i) && !/* @__PURE__ */ z(n)) return e || (i.value = n), !0;
		}
		let o = a ? Number(t) < e.length : u(e, t), s = Reflect.set(e, t, n, /* @__PURE__ */ z(e) ? e : r);
		return e === /* @__PURE__ */ R(r) && s && (o ? j(n, i) && Qe(e, "set", t, n, i) : Qe(e, "add", t, n)), s;
	}
	deleteProperty(e, t) {
		let n = u(e, t), r = e[t], i = Reflect.deleteProperty(e, t);
		return i && n && Qe(e, "delete", t, void 0, r), i;
	}
	has(e, t) {
		let n = Reflect.has(e, t);
		return (!_(t) || !ut.has(t)) && L(e, "has", t), n;
	}
	ownKeys(e) {
		return L(e, "iterate", d(e) ? "length" : Ye), Reflect.ownKeys(e);
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
		let i = this.__v_raw, a = /* @__PURE__ */ R(i), o = f(a), c = e === "entries" || e === Symbol.iterator && o, l = e === "keys" && o, u = i[e](...r), d = n ? vt : t ? Ht : Vt;
		return !t && L(a, "iterate", l ? Xe : Ye), s(Object.create(u), { next() {
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
			e || (j(n, a) && L(i, "get", n), L(i, "get", a));
			let { has: o } = yt(i), s = t ? vt : e ? Ht : Vt;
			if (o.call(i, n)) return s(r.get(n));
			if (o.call(i, a)) return s(r.get(a));
			r !== i && r.get(n);
		},
		get size() {
			let t = this.__v_raw;
			return !e && L(/* @__PURE__ */ R(t), "iterate", Ye), t.size;
		},
		has(t) {
			let n = this.__v_raw, r = /* @__PURE__ */ R(n), i = /* @__PURE__ */ R(t);
			return e || (j(t, i) && L(r, "has", t), L(r, "has", i)), t === i ? n.has(t) : n.has(t) || n.has(i);
		},
		forEach(n, r) {
			let i = this, a = i.__v_raw, o = /* @__PURE__ */ R(a), s = t ? vt : e ? Ht : Vt;
			return !e && L(o, "iterate", Ye), a.forEach((e, t) => n.call(r, s(e), s(t), i));
		}
	};
	return s(n, e ? {
		add: xt("add"),
		set: xt("set"),
		delete: xt("delete"),
		clear: xt("clear")
	} : {
		add(e) {
			let n = /* @__PURE__ */ R(this), r = yt(n), i = /* @__PURE__ */ R(e), a = !t && !/* @__PURE__ */ Rt(e) && !/* @__PURE__ */ Lt(e) ? i : e;
			return r.has.call(n, a) || j(e, a) && r.has.call(n, e) || j(i, a) && r.has.call(n, i) || (n.add(a), Qe(n, "add", a, a)), this;
		},
		set(e, n) {
			!t && !/* @__PURE__ */ Rt(n) && !/* @__PURE__ */ Lt(n) && (n = /* @__PURE__ */ R(n));
			let r = /* @__PURE__ */ R(this), { has: i, get: a } = yt(r), o = i.call(r, e);
			o ||= (e = /* @__PURE__ */ R(e), i.call(r, e));
			let s = a.call(r, e);
			return r.set(e, n), o ? j(n, s) && Qe(r, "set", e, n, s) : Qe(r, "add", e, n), this;
		},
		delete(e) {
			let t = /* @__PURE__ */ R(this), { has: n, get: r } = yt(t), i = n.call(t, e);
			i ||= (e = /* @__PURE__ */ R(e), n.call(t, e));
			let a = r ? r.call(t, e) : void 0, o = t.delete(e);
			return i && Qe(t, "delete", e, void 0, a), o;
		},
		clear() {
			let e = /* @__PURE__ */ R(this), t = e.size !== 0, n = e.clear();
			return t && Qe(e, "clear", void 0, void 0, void 0), n;
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
	return /* @__PURE__ */ Lt(e) ? e : Ft(e, !1, ht, wt, Dt);
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
	return /* @__PURE__ */ Lt(e) ? /* @__PURE__ */ It(e.__v_raw) : !!(e && e.__v_isReactive);
}
// @__NO_SIDE_EFFECTS__
function Lt(e) {
	return !!(e && e.__v_isReadonly);
}
// @__NO_SIDE_EFFECTS__
function Rt(e) {
	return !!(e && e.__v_isShallow);
}
// @__NO_SIDE_EFFECTS__
function zt(e) {
	return e ? !!e.__v_raw : !1;
}
// @__NO_SIDE_EFFECTS__
function R(e) {
	let t = e && e.__v_raw;
	return t ? /* @__PURE__ */ R(t) : e;
}
function Bt(e) {
	return !u(e, "__v_skip") && Object.isExtensible(e) && re(e, "__v_skip", !0), e;
}
var Vt = (e) => v(e) ? /* @__PURE__ */ Mt(e) : e, Ht = (e) => v(e) ? /* @__PURE__ */ Pt(e) : e;
// @__NO_SIDE_EFFECTS__
function z(e) {
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
	return /* @__PURE__ */ z(e) ? e : new Gt(e, t);
}
var Gt = class {
	constructor(e, t) {
		this.dep = new Ke(), this.__v_isRef = !0, this.__v_isShallow = !1, this._rawValue = t ? e : /* @__PURE__ */ R(e), this._value = t ? e : Vt(e), this.__v_isShallow = t;
	}
	get value() {
		return this.dep.track(), this._value;
	}
	set value(e) {
		let t = this._rawValue, n = this.__v_isShallow || /* @__PURE__ */ Rt(e) || /* @__PURE__ */ Lt(e);
		e = n ? e : /* @__PURE__ */ R(e), j(e, t) && (this._rawValue = e, this._value = n ? e : Vt(e), this.dep.trigger());
	}
};
function V(e) {
	return /* @__PURE__ */ z(e) ? e.value : e;
}
var Kt = {
	get: (e, t, n) => t === "__v_raw" ? e : V(Reflect.get(e, t, n)),
	set: (e, t, n, r) => {
		let i = e[t];
		return /* @__PURE__ */ z(i) && !/* @__PURE__ */ z(n) ? (i.value = n, !0) : Reflect.set(e, t, n, r);
	}
};
function qt(e) {
	return /* @__PURE__ */ It(e) ? e : new Proxy(e, Kt);
}
var Jt = class {
	constructor(e, t, n) {
		this.fn = e, this.setter = t, this._value = void 0, this.dep = new Ke(this), this.__v_isRef = !0, this.deps = void 0, this.depsTail = void 0, this.flags = 16, this.globalVersion = We - 1, this.next = void 0, this.effect = this, this.__v_isReadonly = !t, this.isSSR = n;
	}
	notify() {
		if (this.flags |= 16, !(this.flags & 8) && I !== this) return Ae(this, !0), !0;
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
	let { immediate: a, deep: o, once: s, scheduler: l, augmentJob: u, call: f } = i, p = (e) => o ? e : /* @__PURE__ */ Rt(e) || o === !1 || o === 0 ? tn(e, 1) : tn(e), m, g, _, v, y = !1, b = !1;
	if (/* @__PURE__ */ z(e) ? (g = () => e.value, y = /* @__PURE__ */ Rt(e)) : /* @__PURE__ */ It(e) ? (g = () => p(e), y = !0) : d(e) ? (b = !0, y = e.some((e) => /* @__PURE__ */ It(e) || /* @__PURE__ */ Rt(e)), g = () => e.map((e) => {
		if (/* @__PURE__ */ z(e)) return e.value;
		if (/* @__PURE__ */ It(e)) return p(e);
		if (h(e)) return f ? f(e, 2) : e();
	})) : g = h(e) ? n ? f ? () => f(e, 2) : e : () => {
		if (_) {
			Ve();
			try {
				_();
			} finally {
				He();
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
	let C = b ? Array(e.length).fill(Xt) : Xt, w = (e) => {
		if (m.flags & 1 && (m.dirty || e)) {
			if (n) {
				let t = m.run();
				if (e || o || y || (b ? t.some((e, t) => j(e, C[t])) : j(t, C))) {
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
	return u && u(w), m = new Ee(g), m.scheduler = l ? () => l(w, !1) : w, v = (e) => $t(e, !1, m), _ = m.onStop = () => {
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
	if (n.set(e, t), t--, /* @__PURE__ */ z(e)) tn(e.value, t, n);
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
			Ve(), nn(o, null, 10, [
				e,
				i,
				a
			]), He();
			return;
		}
	}
	on(e, r, a, i, s);
}
function on(e, t, n, r = !0, i = !1) {
	if (i) throw e;
	console.error(e);
}
var H = [], sn = -1, cn = [], ln = null, un = 0, dn = /* @__PURE__ */ Promise.resolve(), fn = null;
function pn(e) {
	let t = fn || dn;
	return e ? t.then(this ? e.bind(this) : e) : t;
}
function mn(e) {
	let t = sn + 1, n = H.length;
	for (; t < n;) {
		let r = t + n >>> 1, i = H[r], a = bn(i);
		a < e || a === e && i.flags & 2 ? t = r + 1 : n = r;
	}
	return t;
}
function hn(e) {
	if (!(e.flags & 1)) {
		let t = bn(e), n = H[H.length - 1];
		!n || !(e.flags & 2) && t >= bn(n) ? H.push(e) : H.splice(mn(t), 0, e), e.flags |= 1, gn();
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
	for (; n < H.length; n++) {
		let t = H[n];
		if (t && t.flags & 2) {
			if (e && t.id !== e.uid) continue;
			H.splice(n, 1), n--, t.flags & 4 && (t.flags &= -2), t(), t.flags & 4 || (t.flags &= -2);
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
		for (sn = 0; sn < H.length; sn++) {
			let e = H[sn];
			e && !(e.flags & 8) && (e.flags & 4 && (e.flags &= -2), nn(e, e.i, e.i ? 15 : 14), e.flags & 4 || (e.flags &= -2));
		}
	} finally {
		for (; sn < H.length; sn++) {
			let e = H[sn];
			e && (e.flags &= -2);
		}
		sn = -1, H.length = 0, yn(e), fn = null, (H.length || cn.length) && xn(e);
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
		r._d && ei(-1);
		let i = wn(t), a = Zr.length, o;
		try {
			o = e(...n);
		} finally {
			for (let e = Zr.length; e > a; e--) Qr();
			wn(i), r._d && ei(1);
		}
		return o;
	};
	return r._n = !0, r._c = !0, r._d = !0, r;
}
function En(e, n) {
	if (Sn === null) return e;
	let r = Mi(Sn), i = e.dirs ||= [];
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
function Dn(e, t, n, r) {
	let i = e.dirs, a = t && t.dirs;
	for (let o = 0; o < i.length; o++) {
		let s = i[o];
		a && (s.oldValue = a[o].value);
		let c = s.dir[r];
		c && (Ve(), rn(c, n, 8, [
			e.el,
			s,
			e,
			t
		]), He());
	}
}
function On(e, t) {
	if (Q) {
		let n = Q.provides, r = Q.parent && Q.parent.provides;
		r === n && (n = Q.provides = Object.create(r)), n[e] = t;
	}
}
function kn(e, t, n = !1) {
	let r = yi();
	if (r || sr) {
		let i = sr ? sr._context.provides : r ? r.parent == null || r.ce ? r.vnode.appContext && r.vnode.appContext.provides : r.parent.provides : void 0;
		if (i && e in i) return i[e];
		if (arguments.length > 1) return n && h(t) ? t.call(r && r.proxy) : t;
	}
}
var An = /* @__PURE__ */ Symbol.for("v-scx"), jn = () => kn(An);
function Mn(e, t, n) {
	return Nn(e, t, n);
}
function Nn(e, n, i = t) {
	let { immediate: a, deep: o, flush: c, once: l } = i, u = s({}, i), d = n && a || !n && c !== "post", f;
	if (Ti) {
		if (c === "sync") {
			let e = jn();
			f = e.__watcherHandles ||= [];
		} else if (!d) {
			let e = () => {};
			return e.stop = r, e.resume = r, e.pause = r, e;
		}
	}
	let p = Q;
	u.call = (e, t, n) => rn(e, p, t, n);
	let m = !1;
	c === "post" ? u.scheduler = (e) => {
		W(e, p && p.suspense);
	} : c !== "sync" && (m = !0, u.scheduler = (e, t) => {
		t ? e() : hn(e);
	}), u.augmentJob = (e) => {
		n && (e.flags |= 4), m && (e.flags |= 2, p && (e.id = p.uid, e.i = p));
	};
	let h = en(e, n, u);
	return Ti && (f ? f.push(h) : d && h()), h;
}
var Pn = /* @__PURE__ */ Symbol("_vte"), Fn = (e) => e.__isTeleport, In = /* @__PURE__ */ Symbol("_leaveCb");
function Ln(e) {
	let t = e[0];
	if (e.length > 1) {
		for (let n of e) if (n.type !== Yr) {
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
	let e = yi();
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
	let s = a.shapeFlag & 4 ? Mi(a.component) : a.el, l = o ? null : s, { i: f, r: p } = e, m = n && n.r, _ = f.refs === t ? f.refs = {} : f.refs, v = f.setupState, y = /* @__PURE__ */ R(v), b = v === t ? i : (e) => !Un(_, e) && u(y, e), x = (e, t) => !(t && Un(_, t));
	if (m != null && m !== p) {
		if (Kn(n), g(m)) _[m] = null, b(m) && (v[m] = null);
		else if (/* @__PURE__ */ z(m)) {
			let e = n;
			x(m, e.k) && (m.value = null), e.k && (_[e.k] = null);
		}
	}
	if (h(p)) nn(p, f, 12, [l, _]);
	else {
		let t = g(p), n = /* @__PURE__ */ z(p);
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
				t.id = -1, Wn.set(e, t), W(t, r);
			} else Kn(e), i();
		}
	}
}
function Kn(e) {
	let t = Wn.get(e);
	t && (t.flags |= 8, Wn.delete(e));
}
oe().requestIdleCallback, oe().cancelIdleCallback;
var qn = (e) => !!e.type.__asyncLoader, Jn = (e) => e.type.__isKeepAlive;
function Yn(e, t, n = Q, r = !1) {
	if (n) {
		let i = n[e] || (n[e] = []), a = t.__weh ||= (...r) => {
			Ve();
			let i = Si(n), a = rn(t, n, e, r);
			return i(), He(), a;
		};
		return r ? i.unshift(a) : i.push(a), a;
	}
}
var Xn = (e) => (t, n = Q) => {
	(!Ti || e === "sp") && Yn(e, (...e) => t(...e), n);
}, Zn = Xn("m"), Qn = Xn("bum"), $n = /* @__PURE__ */ Symbol.for("v-ndc");
function U(e, t, n, r) {
	let i, a = n && n[r], o = d(e);
	if (o || g(e)) {
		let n = o && /* @__PURE__ */ It(e), r = !1, s = !1;
		n && (r = !/* @__PURE__ */ Rt(e), s = /* @__PURE__ */ Lt(e), e = et(e)), i = Array(e.length);
		for (let n = 0, o = e.length; n < o; n++) i[n] = t(r ? s ? Ht(Vt(e[n])) : Vt(e[n]) : e[n], n, void 0, a && a[n]);
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
var er = (e) => e ? wi(e) ? Mi(e) : er(e.parent) : null, tr = /* @__PURE__ */ s(/* @__PURE__ */ Object.create(null), {
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
		hn(e.update);
	},
	$nextTick: (e) => e.n ||= pn.bind(e.proxy),
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
		if (d) return n === "$attrs" && L(e.attrs, "get", ""), d(e);
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
			version: Pi,
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
					let u = l._ceVNode || oi(n, r);
					return u.appContext = i, s === !0 ? s = "svg" : s === !1 && (s = void 0), o && t ? t(u, a) : e(u, a, s), c = !0, l._container = a, a.__vue_app__ = l, Mi(u.component);
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
	s && (s.trim && (a = r.map((e) => g(e) ? e.trim() : e)), s.number && (a = a.map(ie)));
	let c, l = i[c = te(n)] || i[c = te(D(n))];
	!l && o && (l = i[c = te(k(n))]), l && rn(l, e, 6, a);
	let u = i[c + "Once"];
	if (u) {
		if (!e.emitted) e.emitted = {};
		else if (e.emitted[c]) return;
		e.emitted[c] = !0, rn(u, e, 6, a);
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
	let { type: t, vnode: n, proxy: r, withProxy: i, propsOptions: [a], slots: s, attrs: c, emit: l, render: u, renderCache: d, props: f, data: p, setupState: m, ctx: h, inheritAttrs: g } = e, _ = wn(e), v, y;
	try {
		if (n.shapeFlag & 4) {
			let e = i || r, t = e;
			v = di(u.call(t, e, d, f, m, p, h)), y = c;
		} else {
			let e = t;
			v = di(e.length > 1 ? e(f, {
				attrs: c,
				slots: s,
				emit: l
			}) : e(f, null)), y = t.props ? c : pr(c);
		}
	} catch (t) {
		Zr.length = 0, an(t, e, 1), v = oi(Yr);
	}
	let b = v;
	if (y && g !== !1) {
		let e = Object.keys(y), { shapeFlag: t } = b;
		e.length && t & 7 && (a && e.some(o) && (y = mr(y, a)), b = li(b, y, !1, !0));
	}
	return n.dirs && (b = li(b, null, !1, !0), b.dirs = b.dirs ? b.dirs.concat(n.dirs) : n.dirs), n.transition && zn(Fn(b.type) && Rn(b) || b, n.transition), v = b, wn(_), v;
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
	return n === "style" && v(r) && v(i) ? !_e(r, i) : r !== i;
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
	e.props = n ? r ? i : /* @__PURE__ */ Nt(i) : e.type.props ? i : a, e.attrs = a;
}
function Cr(e, t, n, r) {
	let { props: i, attrs: a, vnode: { patchFlag: o } } = e, s = /* @__PURE__ */ R(i), [c] = e.propsOptions, l = !1;
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
	l && Qe(e.attrs, "set", "");
}
function wr(e, n, r, i) {
	let [a, o] = e.propsOptions, s = !1, c;
	if (n) for (let t in n) {
		if (T(t)) continue;
		let l = n[t], d;
		a && u(a, d = D(t)) ? !o || !o.includes(d) ? r[d] = l : (c ||= {})[d] = l : dr(e.emitsOptions, t) || (!(t in i) || l !== i[t]) && (i[t] = l, s = !0);
	}
	if (o) {
		let n = /* @__PURE__ */ R(r), i = c || t;
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
					let o = Si(i);
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
	return e[0] !== "$" && !T(e);
}
var Or = (e) => e === "_" || e === "_ctx" || e === "$stable", kr = (e) => d(e) ? e.map(di) : [di(e)], Ar = (e, t, n) => {
	if (t._n) return t;
	let r = Tn((...e) => kr(t(...e)), n);
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
		e ? (Nr(r, t, n), n && re(r, "_", e, !0)) : jr(t, r);
	} else t && Mr(e, t);
}, Fr = (e, n, r) => {
	let { vnode: i, slots: a } = e, o = !0, s = t;
	if (i.shapeFlag & 32) {
		let e = n._;
		e ? r && e === 1 ? o = !1 : Nr(a, n, r) : (o = !n.$stable, jr(n, a)), s = n;
	} else n && (Mr(e, n), s = { default: 1 });
	if (o) for (let e in a) !Or(e) && s[e] == null && delete a[e];
}, W = qr;
function Ir(e) {
	return Lr(e);
}
function Lr(e, i) {
	let a = oe();
	a.__VUE__ = !0;
	let { insert: o, remove: s, patchProp: c, createElement: l, createText: u, createComment: d, setText: f, setElementText: p, parentNode: m, nextSibling: h, setScopeId: g = r, insertStaticContent: _ } = e, v = (e, t, n, r = null, i = null, a = null, o = void 0, s = null, c = !!t.dynamicChildren) => {
		if (e === t) return;
		e && !ri(e, t) && (r = he(e), de(e, i, a, !0), e = null), t.patchFlag === -2 && (c = !1, t.dynamicChildren = null);
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
			case G:
				te(e, t, n, r, i, a, o, s, c);
				break;
			default: d & 1 ? w(e, t, n, r, i, a, o, s, c) : d & 6 ? j(e, t, n, r, i, a, o, s, c) : (d & 64 || d & 128) && l.process(e, t, n, r, i, a, o, s, c, ve);
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
				n && n._beginPatch(), O(e, t, i, a, o, s, c);
			} finally {
				n && n._endPatch();
			}
		}
	}, ee = (e, t, n, r, i, a, s, u) => {
		let d, f, { props: m, shapeFlag: h, transition: g, dirs: _ } = e;
		if (d = e.el = l(e.type, a, m && m.is, m), h & 8 ? p(d, e.children) : h & 16 && D(e.children, d, null, r, i, Rr(e, a), s, u), _ && Dn(e, null, r, "created"), E(d, e, e.scopeId, s, r), m) {
			for (let e in m) e !== "value" && !T(e) && c(d, e, null, m[e], a, r);
			"value" in m && c(d, "value", null, m.value, a), (f = m.onVnodeBeforeMount) && hi(f, r, e);
		}
		_ && Dn(e, null, r, "beforeMount");
		let v = Br(i, g);
		v && g.beforeEnter(d), o(d, t, n), ((f = m && m.onVnodeMounted) || v || _) && W(() => {
			try {
				f && hi(f, r, e), v && g.enter(d), _ && Dn(e, null, r, "mounted");
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
			let c = e[l] = s ? fi(e[l]) : di(e[l]);
			v(null, c, t, n, r, i, a, o, s);
		}
	}, O = (e, n, r, i, a, o, s) => {
		let l = n.el = e.el, { patchFlag: u, dynamicChildren: d, dirs: f } = n;
		u |= e.patchFlag & 16;
		let m = e.props || t, h = n.props || t, g;
		if (r && zr(r, !1), (g = h.onVnodeBeforeUpdate) && hi(g, r, n, e), f && Dn(n, e, r, "beforeUpdate"), r && zr(r, !0), d && (!e.dynamicChildren || e.dynamicChildren.length !== d.length) && (u = 0, s = !1, d = null), (m.innerHTML && h.innerHTML == null || m.textContent && h.textContent == null) && p(l, ""), d ? k(e.dynamicChildren, d, l, r, i, Rr(n, a), o) : s || se(e, n, l, null, r, i, Rr(n, a), o, !1), u > 0) {
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
		((g = h.onVnodeUpdated) || f) && W(() => {
			g && hi(g, r, n, e), f && Dn(n, e, r, "updated");
		}, i);
	}, k = (e, t, n, r, i, a, o) => {
		for (let s = 0; s < t.length; s++) {
			let c = e[s], l = t[s], u = c.el && (c.type === G || !ri(c, l) || c.shapeFlag & 198) ? m(c.el) : n;
			v(c, l, u, null, r, i, a, o, !0);
		}
	}, A = (e, n, r, i, a) => {
		if (n !== r) {
			if (n !== t) for (let t in n) !T(t) && !(t in r) && c(e, t, n[t], null, a, i);
			for (let t in r) {
				if (T(t)) continue;
				let o = r[t], s = n[t];
				o !== s && t !== "value" && c(e, t, s, o, a, i);
			}
			"value" in r && c(e, "value", n.value, r.value, a);
		}
	}, te = (e, t, n, r, i, a, s, c, l) => {
		let d = t.el = e ? e.el : u(""), f = t.anchor = e ? e.anchor : u(""), { patchFlag: p, dynamicChildren: m, slotScopeIds: h } = t;
		h && (c = c ? c.concat(h) : h), e == null ? (o(d, n, r), o(f, n, r), D(t.children || [], n, f, i, a, s, c, l)) : p > 0 && p & 64 && m && e.dynamicChildren && e.dynamicChildren.length === m.length ? (k(e.dynamicChildren, m, n, i, a, s, c), (t.key != null || i && t === i.subTree) && Vr(e, t, !0)) : se(e, t, n, f, i, a, s, c, l);
	}, j = (e, t, n, r, i, a, o, s, c) => {
		t.slotScopeIds = s, e == null ? t.shapeFlag & 512 ? i.ctx.activate(t, n, r, o, c) : re(t, n, r, i, a, o, c) : ie(e, t, c);
	}, re = (e, t, n, r, i, a, o) => {
		let s = e.component = vi(e, r, i);
		if (Jn(e) && (s.ctx.renderer = ve), Ei(s, !1, o), s.asyncDep) {
			if (i && i.registerDep(s, ae, o), !e.el) {
				let r = s.subTree = oi(Yr);
				b(null, r, t, n), e.placeholder = r.el;
			}
		} else ae(s, e, t, n, i, a, o);
	}, ie = (e, t, n) => {
		let r = t.component = e.component;
		if (hr(e, t, n)) {
			if (r.asyncDep && !r.asyncResolved) {
				M(r, t, n);
				return;
			}
			r.next = t, r.update();
		} else t.el = e.el, r.vnode = t;
	}, ae = (e, t, n, r, i, a, o) => {
		let s = () => {
			if (e.isMounted) {
				let { next: t, bu: n, u: r, parent: s, vnode: c } = e;
				{
					let n = Ur(e);
					if (n) {
						t && (t.el = c.el, M(e, t, o)), n.asyncDep.then(() => {
							W(() => {
								e.isUnmounted || l();
							}, i);
						});
						return;
					}
				}
				let u = t, d;
				zr(e, !1), t ? (t.el = c.el, M(e, t, o)) : t = c, n && ne(n), (d = t.props && t.props.onVnodeBeforeUpdate) && hi(d, s, t, c), zr(e, !0);
				let f = fr(e), p = e.subTree;
				e.subTree = f, v(p, f, m(p.el), he(p), e, i, a), t.el = f.el, u === null && vr(e, f.el), r && W(r, i), (d = t.props && t.props.onVnodeUpdated) && W(() => hi(d, s, t, c), i);
			} else {
				let o, { el: s, props: c } = t, { bm: l, m: u, parent: d, root: f, type: p } = e, m = qn(t);
				if (zr(e, !1), l && ne(l), !m && (o = c && c.onVnodeBeforeMount) && hi(o, d, t), zr(e, !0), s && P) {
					let t = () => {
						e.subTree = fr(e), P(s, e.subTree, e, i, null);
					};
					m && p.__asyncHydrate ? p.__asyncHydrate(s, e, t) : t();
				} else {
					f.ce && f.ce._hasShadowRoot() && f.ce._injectChildStyle(p, e.parent ? e.parent.type : void 0);
					let o = e.subTree = fr(e);
					v(null, o, n, r, e, i, a), t.el = o.el;
				}
				if (u && W(u, i), !m && (o = c && c.onVnodeMounted)) {
					let e = t;
					W(() => hi(o, d, e), i);
				}
				(t.shapeFlag & 256 || d && qn(d.vnode) && d.vnode.shapeFlag & 256) && e.a && W(e.a, i), e.isMounted = !0, t = n = r = null;
			}
		};
		e.scope.on();
		let c = e.effect = new Ee(s);
		e.scope.off();
		let l = e.update = c.run.bind(c), u = e.job = c.runIfDirty.bind(c);
		u.i = e, u.id = e.uid, c.scheduler = () => hn(u), zr(e, !0), l();
	}, M = (e, t, n) => {
		t.component = e;
		let r = e.vnode.props;
		e.vnode = t, e.next = null, Cr(e, t.props, r, n), Fr(e, t.children, n), Ve(), vn(e), He();
	}, se = (e, t, n, r, i, a, o, s, c = !1) => {
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
		m & 8 ? (u & 16 && me(l, i, a), d !== l && p(n, d)) : u & 16 ? m & 16 ? le(l, d, n, r, i, a, o, s, c) : me(l, i, a, !0) : (u & 8 && p(n, ""), m & 16 && D(d, n, r, i, a, o, s, c));
	}, ce = (e, t, r, i, a, o, s, c, l) => {
		e ||= n, t ||= n;
		let u = e.length, d = t.length, f = Math.min(u, d), p = 0;
		for (; p < f; p++) {
			let n = t[p] = l ? fi(t[p]) : di(t[p]);
			v(e[p], n, r, null, a, o, s, c, l);
		}
		u > d ? me(e, a, o, !0, !1, f) : D(t, r, i, a, o, s, c, l, f);
	}, le = (e, t, r, i, a, o, s, c, l) => {
		let u = 0, d = t.length, f = e.length - 1, p = d - 1;
		for (; u <= f && u <= p;) {
			let n = e[u], i = t[u] = l ? fi(t[u]) : di(t[u]);
			if (ri(n, i)) v(n, i, r, null, a, o, s, c, l);
			else break;
			u++;
		}
		for (; u <= f && u <= p;) {
			let n = e[f], i = t[p] = l ? fi(t[p]) : di(t[p]);
			if (ri(n, i)) v(n, i, r, null, a, o, s, c, l);
			else break;
			f--, p--;
		}
		if (u > f) {
			if (u <= p) {
				let e = p + 1, n = e < d ? t[e].el : i;
				for (; u <= p;) v(null, t[u] = l ? fi(t[u]) : di(t[u]), r, n, a, o, s, c, l), u++;
			}
		} else if (u > p) for (; u <= f;) de(e[u], a, o, !0), u++;
		else {
			let m = u, h = u, g = /* @__PURE__ */ new Map();
			for (u = h; u <= p; u++) {
				let e = t[u] = l ? fi(t[u]) : di(t[u]);
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
				else for (_ = h; _ <= p; _++) if (C[_ - h] === 0 && ri(n, t[_])) {
					i = _;
					break;
				}
				i === void 0 ? de(n, a, o, !0) : (C[i - h] = u + 1, i >= S ? S = i : x = !0, v(n, t[i], r, null, a, o, s, c, l), y++);
			}
			let w = x ? Hr(C) : n;
			for (_ = w.length - 1, u = b - 1; u >= 0; u--) {
				let e = h + u, n = t[e], f = t[e + 1], p = e + 1 < d ? f.el || Gr(f) : i;
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
			c.move(e, t, n, ve);
			return;
		}
		if (c === G) {
			o(a, t, n);
			for (let e = 0; e < u.length; e++) ue(u[e], t, n, r);
			o(e.anchor, t, n);
			return;
		}
		if (c === Xr) {
			S(e, t, n);
			return;
		}
		if (r !== 2 && d & 1 && l) {
			if (r === 0) l.persisted && !a[In] ? o(a, t, n) : (l.beforeEnter(a), o(a, t, n), W(() => l.enter(a), i));
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
		if (d === -2 && (i = !1), s != null && (Ve(), Gn(s, null, n, e, !0), He()), p != null && (t.renderCache[p] = void 0), u & 256) {
			t.ctx.deactivate(e);
			return;
		}
		let h = u & 1 && f, g = !qn(e), _;
		if (g && (_ = o && o.onVnodeBeforeUnmount) && hi(_, t, e), u & 6) pe(e.component, n, r);
		else {
			if (u & 128) {
				e.suspense.unmount(n, r);
				return;
			}
			h && Dn(e, null, t, "beforeUnmount"), u & 64 ? e.type.remove(e, t, n, ve, r) : l && !l.hasOnce && (a !== G || d > 0 && d & 64) ? me(l, t, n, !1, !0) : (a === G && d & 384 || !i && u & 16) && me(c, t, n), r && N(e);
		}
		let v = m != null && p == null;
		(g && (_ = o && o.onVnodeUnmounted) || h || v) && W(() => {
			_ && hi(_, t, e), h && Dn(e, null, t, "unmounted"), v && (e.el = null);
		}, n);
	}, N = (e) => {
		let { type: t, el: n, anchor: r, transition: i } = e;
		if (t === G) {
			fe(n, r);
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
	}, fe = (e, t) => {
		let n;
		for (; e !== t;) n = h(e), s(e), e = n;
		s(t);
	}, pe = (e, t, n) => {
		let { bum: r, scope: i, job: a, subTree: o, um: s, m: c, a: l } = e;
		Wr(c), Wr(l), r && ne(r), i.stop(), a && (a.flags |= 8, de(o, e, t, n)), s && W(s, t), W(() => {
			e.isUnmounted = !0;
		}, t);
	}, me = (e, t, n, r = !1, i = !1, a = 0) => {
		for (let o = a; o < e.length; o++) de(e[o], t, n, r, i);
	}, he = (e) => {
		if (e.shapeFlag & 6) return he(e.component.subTree);
		if (e.shapeFlag & 128) return e.suspense.next();
		let t = h(e.anchor || e.el), n = t && t[Pn];
		return n ? h(n) : t;
	}, ge = !1, _e = (e, t, n) => {
		let r;
		e == null ? t._vnode && (de(t._vnode, null, null, !0), r = t._vnode.component) : v(t._vnode || null, e, t, null, null, null, n), t._vnode = e, ge ||= (ge = !0, vn(r), yn(), !1);
	}, ve = {
		p: v,
		um: de,
		m: ue,
		r: N,
		mt: re,
		mc: D,
		pc: se,
		pbc: k,
		n: he,
		o: e
	}, ye, P;
	return i && ([ye, P] = i(ve)), {
		render: _e,
		hydrate: ye,
		createApp: or(_e, ye)
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
		a.shapeFlag & 1 && !a.dynamicChildren && ((a.patchFlag <= 0 || a.patchFlag === 32) && (a = i[e] = fi(i[e]), a.el = t.el), !n && a.patchFlag !== -2 && Vr(t, a)), a.type === Jr && (a.patchFlag === -1 && (a = i[e] = fi(a)), a.el = t.el), a.type === Yr && !a.el && (a.el = t.el);
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
	t && t.pendingBranch ? d(e) ? t.effects.push(...e) : t.effects.push(e) : _n(e);
}
var G = /* @__PURE__ */ Symbol.for("v-fgt"), Jr = /* @__PURE__ */ Symbol.for("v-txt"), Yr = /* @__PURE__ */ Symbol.for("v-cmt"), Xr = /* @__PURE__ */ Symbol.for("v-stc"), Zr = [], K = null;
function q(e = !1) {
	Zr.push(K = e ? null : []);
}
function Qr() {
	Zr.pop(), K = Zr[Zr.length - 1] || null;
}
var $r = 1;
function ei(e, t = !1) {
	$r += e, e < 0 && K && t && (K.hasOnce = !0);
}
function ti(e) {
	return e.dynamicChildren = $r > 0 ? K || n : null, Qr(), $r > 0 && K && K.push(e), e;
}
function J(e, t, n, r, i, a) {
	return ti(X(e, t, n, r, i, a, !0));
}
function Y(e, t, n, r, i) {
	return ti(oi(e, t, n, r, i, !0));
}
function ni(e) {
	return e ? e.__v_isVNode === !0 : !1;
}
function ri(e, t) {
	return e.type === t.type && e.key === t.key;
}
var ii = ({ key: e }) => e ?? null, ai = ({ ref: e, ref_key: t, ref_for: n }) => (typeof e == "number" && (e = "" + e), e == null ? null : g(e) || /* @__PURE__ */ z(e) || h(e) ? {
	i: Sn,
	r: e,
	k: t,
	f: !!n
} : e);
function X(e, t = null, n = null, r = 0, i = null, a = e === G ? 0 : 1, o = !1, s = !1) {
	let c = {
		__v_isVNode: !0,
		__v_skip: !0,
		type: e,
		props: t,
		key: t && ii(t),
		ref: t && ai(t),
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
	return s ? (pi(c, n), a & 128 && e.normalize(c)) : n && (c.shapeFlag |= g(n) ? 8 : 16), $r > 0 && !o && K && (c.patchFlag > 0 || a & 6) && c.patchFlag !== 32 && K.push(c), c;
}
var oi = si;
function si(e, t = null, n = null, r = 0, i = null, a = !1) {
	if ((!e || e === $n) && (e = Yr), ni(e)) {
		let r = li(e, t, !0);
		return n && pi(r, n), $r > 0 && !a && K && (r.shapeFlag & 6 ? K[K.indexOf(e)] = r : K.push(r)), r.patchFlag = -2, r;
	}
	if (Ni(e) && (e = e.__vccOpts), t) {
		t = ci(t);
		let { class: e, style: n } = t;
		e && !g(e) && (t.class = N(e)), v(n) && (/* @__PURE__ */ zt(n) && !d(n) && (n = s({}, n)), t.style = se(n));
	}
	let o = g(e) ? 1 : Kr(e) ? 128 : Fn(e) ? 64 : v(e) ? 4 : h(e) ? 2 : 0;
	return X(e, t, n, r, i, o, a, !0);
}
function ci(e) {
	return e ? /* @__PURE__ */ zt(e) || xr(e) ? s({}, e) : e : null;
}
function li(e, t, n = !1, r = !1) {
	let { props: i, ref: a, patchFlag: o, children: s, transition: c } = e, l = t ? mi(i || {}, t) : i, u = {
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
		patchFlag: t && e.type !== G ? o === -1 ? 16 : o | 16 : o,
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
	return c && r && zn(u, c.clone(u)), u;
}
function ui(e = " ", t = 0) {
	return oi(Jr, null, e, t);
}
function Z(e = "", t = !1) {
	return t ? (q(), Y(Yr, null, e)) : oi(Yr, null, e);
}
function di(e) {
	return e == null || typeof e == "boolean" ? oi(Yr) : d(e) ? oi(G, null, e.slice()) : ni(e) ? fi(e) : oi(Jr, null, String(e));
}
function fi(e) {
	return e.el === null && e.patchFlag !== -1 || e.memo ? e : li(e);
}
function pi(e, t) {
	let n = 0, { shapeFlag: r } = e;
	if (t == null) t = null;
	else if (d(t)) n = 16;
	else if (typeof t == "object") {
		if (r & 65) {
			let n = t.default;
			n && (n._c && (n._d = !1), pi(e, n()), n._c && (n._d = !0));
			return;
		}
		{
			n = 32;
			let r = t._;
			!r && !xr(t) ? t._ctx = Sn : r === 3 && Sn && (Sn.slots._ === 1 ? t._ = 1 : (t._ = 2, e.patchFlag |= 1024));
		}
	} else if (h(t)) {
		if (r & 65) {
			pi(e, { default: t });
			return;
		}
		t = {
			default: t,
			_ctx: Sn
		}, n = 32;
	} else t = String(t), r & 64 ? (n = 16, t = [ui(t)]) : n = 8;
	e.children = t, e.shapeFlag |= n;
}
function mi(...e) {
	let t = {};
	for (let n = 0; n < e.length; n++) {
		let r = e[n];
		for (let e in r) if (e === "class") t.class !== r.class && (t.class = N([t.class, r.class]));
		else if (e === "style") t.style = se([t.style, r.style]);
		else if (a(e)) {
			let n = t[e], i = r[e];
			i && n !== i && !(d(n) && n.includes(i)) ? t[e] = n ? [].concat(n, i) : i : i == null && n == null && !o(e) && (t[e] = i);
		} else e !== "" && (t[e] = r[e]);
	}
	return t;
}
function hi(e, t, n, r = null) {
	rn(e, t, 7, [n, r]);
}
var gi = ir(), _i = 0;
function vi(e, n, r) {
	let i = e.type, a = (n ? n.appContext : e.appContext) || gi, o = {
		uid: _i++,
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
var Q = null, yi = () => Q || Sn, bi, xi;
{
	let e = oe(), t = (t, n) => {
		let r;
		return (r = e[t]) || (r = e[t] = []), r.push(n), (e) => {
			r.length > 1 ? r.forEach((t) => t(e)) : r[0](e);
		};
	};
	bi = t("__VUE_INSTANCE_SETTERS__", (e) => Q = e), xi = t("__VUE_SSR_SETTERS__", (e) => Ti = e);
}
var Si = (e) => {
	let t = Q;
	return bi(e), e.scope.on(), () => {
		e.scope.off(), bi(t);
	};
}, Ci = () => {
	Q && Q.scope.off(), bi(null);
};
function wi(e) {
	return e.vnode.shapeFlag & 4;
}
var Ti = !1;
function Ei(e, t = !1, n = !1) {
	t && xi(t);
	let { props: r, children: i } = e.vnode, a = wi(e);
	Sr(e, r, a, t), Pr(e, i, n || t);
	let o = a ? Di(e, t) : void 0;
	return t && xi(!1), o;
}
function Di(e, t) {
	let n = e.type;
	e.accessCache = /* @__PURE__ */ Object.create(null), e.proxy = new Proxy(e.ctx, rr);
	let { setup: r } = n;
	if (r) {
		Ve();
		let n = e.setupContext = r.length > 1 ? ji(e) : null, i = Si(e), a = nn(r, e, 0, [e.props, n]), o = y(a);
		if (He(), i(), (o || e.sp) && !qn(e) && Hn(e), o) {
			if (a.then(Ci, Ci), t) return a.then((n) => {
				xi(!0);
				try {
					Oi(e, n, t);
				} finally {
					xi(!1);
				}
			}).catch((t) => {
				an(t, e, 0);
			});
			e.asyncDep = a;
		} else Oi(e, a, t);
	} else ki(e, t);
}
function Oi(e, t, n) {
	h(t) ? e.type.__ssrInlineRender ? e.ssrRender = t : e.render = t : v(t) && (e.setupState = qt(t)), ki(e, n);
}
function ki(e, t, n) {
	let i = e.type;
	e.render ||= i.render || r;
}
var Ai = { get(e, t) {
	return L(e, "get", ""), e[t];
} };
function ji(e) {
	return {
		attrs: new Proxy(e.attrs, Ai),
		slots: e.slots,
		emit: e.emit,
		expose: (t) => {
			e.exposed = t || {};
		}
	};
}
function Mi(e) {
	return e.exposed ? e.exposeProxy ||= new Proxy(qt(Bt(e.exposed)), {
		get(t, n) {
			if (n in t) return t[n];
			if (n in tr) return tr[n](e);
		},
		has(e, t) {
			return t in e || t in tr;
		}
	}) : e.proxy;
}
function Ni(e) {
	return h(e) && "__vccOpts" in e;
}
var $ = (e, t) => /* @__PURE__ */ Yt(e, t, Ti), Pi = "3.5.42", Fi = void 0, Ii = typeof window < "u" && window.trustedTypes;
if (Ii) try {
	Fi = /* @__PURE__ */ Ii.createPolicy("vue", { createHTML: (e) => e });
} catch {}
var Li = Fi ? (e) => Fi.createHTML(e) : (e) => e, Ri = "http://www.w3.org/2000/svg", zi = "http://www.w3.org/1998/Math/MathML", Bi = typeof document < "u" ? document : null, Vi = Bi && /* @__PURE__ */ Bi.createElement("template"), Hi = {
	insert: (e, t, n) => {
		t.insertBefore(e, n || null);
	},
	remove: (e) => {
		let t = e.parentNode;
		t && t.removeChild(e);
	},
	createElement: (e, t, n, r) => {
		let i = t === "svg" ? Bi.createElementNS(Ri, e) : t === "mathml" ? Bi.createElementNS(zi, e) : n ? Bi.createElement(e, { is: n }) : Bi.createElement(e);
		return e === "select" && r && r.multiple != null && i.setAttribute("multiple", r.multiple), i;
	},
	createText: (e) => Bi.createTextNode(e),
	createComment: (e) => Bi.createComment(e),
	setText: (e, t) => {
		e.nodeValue = t;
	},
	setElementText: (e, t) => {
		e.textContent = t;
	},
	parentNode: (e) => e.parentNode,
	nextSibling: (e) => e.nextSibling,
	querySelector: (e) => Bi.querySelector(e),
	setScopeId(e, t) {
		e.setAttribute(t, "");
	},
	insertStaticContent(e, t, n, r, i, a) {
		let o = n ? n.previousSibling : t.lastChild;
		if (i && (i === a || i.nextSibling)) for (; t.insertBefore(i.cloneNode(!0), n), i !== a && (i = i.nextSibling););
		else {
			Vi.innerHTML = Li(r === "svg" ? `<svg>${e}</svg>` : r === "mathml" ? `<math>${e}</math>` : e);
			let i = Vi.content;
			if (r === "svg" || r === "mathml") {
				let e = i.firstChild;
				for (; e.firstChild;) i.appendChild(e.firstChild);
				i.removeChild(e);
			}
			t.insertBefore(i, n);
		}
		return [o ? o.nextSibling : t.firstChild, n ? n.previousSibling : t.lastChild];
	}
}, Ui = /* @__PURE__ */ Symbol("_vtc");
function Wi(e, t, n) {
	let r = e[Ui];
	r && (t = (t ? [t, ...r] : [...r]).join(" ")), t == null ? e.removeAttribute("class") : n ? e.setAttribute("class", t) : e.className = t;
}
var Gi = /* @__PURE__ */ Symbol("_vod"), Ki = /* @__PURE__ */ Symbol("_vsh"), qi = /* @__PURE__ */ Symbol(""), Ji = /(?:^|;)\s*display\s*:/;
function Yi(e, t, n) {
	let r = e.style, i = g(n), a = !1;
	if (n && !i) {
		if (t) {
			if (g(t)) for (let e of t.split(";")) {
				let t = e.slice(0, e.indexOf(":")).trim();
				n[t] ?? Zi(r, t, "");
			}
			else for (let e in t) n[e] ?? Zi(r, e, "");
		}
		for (let i in n) {
			i === "display" && (a = !0);
			let o = n[i];
			o == null ? Zi(r, i, "") : ta(e, i, !g(t) && t ? t[i] : void 0, o) || Zi(r, i, o);
		}
	} else if (i) {
		if (t !== n) {
			let e = r[qi];
			e && (n += ";" + e), r.cssText = n, a = Ji.test(n);
		}
	} else t && e.removeAttribute("style");
	Gi in e && (e[Gi] = a ? r.display : "", e[Ki] && (r.display = "none"));
}
var Xi = /\s*!important$/;
function Zi(e, t, n) {
	if (d(n)) n.forEach((n) => Zi(e, t, n));
	else if (n ??= "", t.startsWith("--")) Xi.test(n) ? e.setProperty(t, n.replace(Xi, ""), "important") : e.setProperty(t, n);
	else {
		let r = ea(e, t);
		Xi.test(n) ? e.setProperty(k(r), n.replace(Xi, ""), "important") : e[r] = n;
	}
}
var Qi = [
	"Webkit",
	"Moz",
	"ms"
], $i = {};
function ea(e, t) {
	let n = $i[t];
	if (n) return n;
	let r = D(t);
	if (r !== "filter" && r in e) return $i[t] = r;
	r = A(r);
	for (let n = 0; n < Qi.length; n++) {
		let i = Qi[n] + r;
		if (i in e) return $i[t] = i;
	}
	return t;
}
function ta(e, t, n, r) {
	return e.tagName === "TEXTAREA" && (t === "width" || t === "height") && g(r) && n === r;
}
var na = "http://www.w3.org/1999/xlink";
function ra(e, t, n, r, i, a = pe(t)) {
	r && t.startsWith("xlink:") ? n == null ? e.removeAttributeNS(na, t.slice(6, t.length)) : e.setAttributeNS(na, t, n) : n == null || a && !me(n) ? e.removeAttribute(t) : e.setAttribute(t, a ? "" : _(n) ? String(n) : n);
}
function ia(e, t, n, r, i) {
	if (t === "innerHTML" || t === "textContent") {
		n != null && (e[t] = t === "innerHTML" ? Li(n) : n);
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
function aa(e, t, n, r) {
	e.addEventListener(t, n, r);
}
function oa(e, t, n, r) {
	e.removeEventListener(t, n, r);
}
var sa = /* @__PURE__ */ Symbol("_vei");
function ca(e, t, n, r, i = null) {
	let a = e[sa] || (e[sa] = {}), o = a[t];
	if (r && o) o.value = r;
	else {
		let [n, s] = da(t);
		r ? aa(e, n, a[t] = ha(r, i), s) : o && (oa(e, n, o, s), a[t] = void 0);
	}
}
var la = /(Once|Passive|Capture)$/, ua = /^on:?(?:Once|Passive|Capture)$/;
function da(e) {
	let t, n;
	for (; (n = e.match(la)) && !ua.test(e);) t ||= {}, e = e.slice(0, e.length - n[1].length), t[n[1].toLowerCase()] = !0;
	return [e[2] === ":" ? e.slice(3) : k(e.slice(2)), t];
}
var fa = 0, pa = /* @__PURE__ */ Promise.resolve(), ma = () => fa ||= (pa.then(() => fa = 0), Date.now());
function ha(e, t) {
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
	return n.value = e, n.attached = ma(), n;
}
var ga = (e) => e.charCodeAt(0) === 111 && e.charCodeAt(1) === 110 && e.charCodeAt(2) > 96 && e.charCodeAt(2) < 123, _a = (e, t, n, r, i, s) => {
	let c = i === "svg";
	t === "class" ? Wi(e, r, c) : t === "style" ? Yi(e, n, r) : a(t) ? o(t) || ca(e, t, n, r, s) : (t[0] === "." ? (t = t.slice(1), 1) : t[0] === "^" ? (t = t.slice(1), 0) : va(e, t, r, c)) ? (ia(e, t, r), !e.tagName.includes("-") && (t === "value" || t === "checked" || t === "selected") && ra(e, t, r, c, s, t !== "value")) : e._isVueCE && (ya(e, t) || e._def.__asyncLoader && (/[A-Z]/.test(t) || !g(r))) ? ia(e, D(t), r, s, t) : (t === "true-value" ? e._trueValue = r : t === "false-value" && (e._falseValue = r), ra(e, t, r, c));
};
function va(e, t, n, r) {
	if (r) return !!(t === "innerHTML" || t === "textContent" || t in e && ga(t) && h(n));
	if (t === "spellcheck" || t === "draggable" || t === "translate" || t === "autocorrect" || t === "sandbox" && e.tagName === "IFRAME" || t === "form" || t === "list" && e.tagName === "INPUT" || t === "type" && e.tagName === "TEXTAREA") return !1;
	if (t === "width" || t === "height") {
		let t = e.tagName;
		if (t === "IMG" || t === "VIDEO" || t === "CANVAS" || t === "SOURCE") return !1;
	}
	return ga(t) && g(n) ? !1 : t in e;
}
function ya(e, t) {
	let n = e._def.props;
	if (!n) return !1;
	let r = D(t);
	return Array.isArray(n) ? n.some((e) => D(e) === r) : Object.keys(n).some((e) => D(e) === r);
}
var ba = {};
// @__NO_SIDE_EFFECTS__
function xa(e, t, n) {
	let r = /* @__PURE__ */ Bn(e, t);
	C(r) && (r = s({}, r, t));
	class i extends Ca {
		constructor(e) {
			super(r, e, n);
		}
	}
	return i.def = r, i;
}
var Sa = typeof HTMLElement < "u" ? HTMLElement : class {}, Ca = class e extends Sa {
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
		let t = this.hasAttribute(e), n = t ? this.getAttribute(e) : ba, r = D(e);
		t && this._numberProps && this._numberProps[r] && (n = ae(n)), this._setProp(r, n, !1, !0);
	}
	_getProp(e) {
		return this._props[e];
	}
	_setProp(e, t, n = !0, r = !1) {
		if (t !== this._props[e] && (this._dirty = !0, t === ba ? delete this._props[e] : (this._props[e] = t, e === "key" && this._app && (this._app._ceVNode.key = t)), r && this._instance && this._update(), n)) {
			let n = this._ob;
			n && (this._processMutations(n.takeRecords()), n.disconnect()), t === !0 ? this.setAttribute(k(e), "") : typeof t == "string" || typeof t == "number" ? this.setAttribute(k(e), t + "") : t || this.removeAttribute(k(e)), n && n.observe(this, { attributes: !0 });
		}
	}
	_update() {
		let e = this._createVNode();
		this._app && (e.appContext = this._app._context), Ya(e, this._root);
	}
	_createVNode() {
		let e = {};
		this.shadowRoot || (e.onVnodeMounted = e.onVnodeUpdated = this._renderSlots.bind(this));
		let t = oi(this._def, s(e, this._props));
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
function wa(e) {
	let t = yi();
	return t && t.ce || null;
}
var Ta = (e) => {
	let t = e.props["onUpdate:modelValue"] || !1;
	return d(t) ? (e) => ne(t, e) : t;
};
function Ea(e) {
	e.target.composing = !0;
}
function Da(e) {
	let t = e.target;
	t.composing && (t.composing = !1, t.dispatchEvent(new Event("input")));
}
var Oa = /* @__PURE__ */ Symbol("_assign"), ka = /* @__PURE__ */ Symbol("_initialValue");
function Aa(e, t, n) {
	return t && (e = e.trim()), n && (e = ie(e)), e;
}
var ja = {
	created(e, { modifiers: { lazy: t, trim: n, number: r } }, i) {
		e.parentNode && (e.type === "text" ? e[ka] = e.defaultValue.replace(/[\r\n]/g, "") : e.type === "textarea" && (e[ka] = e.defaultValue.replace(/\r\n?/g, "\n"))), e[Oa] = Ta(i);
		let a = r || i.props && i.props.type === "number";
		aa(e, t ? "change" : "input", (t) => {
			t.target.composing || e[Oa](Aa(e.value, n, a));
		}), (n || a) && aa(e, "change", () => {
			e.value = Aa(e.value, n, a);
		}), t || (aa(e, "compositionstart", Ea), aa(e, "compositionend", Da), aa(e, "change", Da));
	},
	mounted(e, { value: t, modifiers: { trim: n, number: r } }) {
		let i = t ?? "", a = e[ka];
		delete e[ka], a !== void 0 && (e.type === "text" || e.type === "textarea") && e.value !== a ? e[Oa](Aa(e.value, n, r)) : e.value = i;
	},
	beforeUpdate(e, { value: t, oldValue: n, modifiers: { lazy: r, trim: i, number: a } }, o) {
		if (e[Oa] = Ta(o), e.composing) return;
		let s = (a || e.type === "number") && !/^0\d/.test(e.value) ? ie(e.value) : e.value, c = t ?? "";
		if (s === c) return;
		let l = e.getRootNode();
		(l instanceof Document || l instanceof ShadowRoot) && l.activeElement === e && e.type !== "range" && (r && t === n || i && e.value.trim() === c) || (e.value = c);
	}
}, Ma = {
	deep: !0,
	created(e, t, n) {
		e[Oa] = Ta(n), aa(e, "change", () => {
			let t = e._modelValue, n = Ra(e), r = e.checked, i = e[Oa];
			if (d(t)) {
				let e = ve(t, n), a = e !== -1;
				if (r && !a) i(t.concat(n));
				else if (!r && a) {
					let n = [...t];
					n.splice(e, 1), i(n);
				}
			} else if (p(t)) {
				let e = new Set(t);
				r ? e.add(n) : e.delete(n), i(e);
			} else i(za(e, r));
		});
	},
	mounted: Na,
	beforeUpdate(e, t, n) {
		e[Oa] = Ta(n), Na(e, t, n);
	}
};
function Na(e, { value: t, oldValue: n }, r) {
	e._modelValue = t;
	let i;
	if (d(t)) i = ve(t, r.props.value) > -1;
	else if (p(t)) i = t.has(r.props.value);
	else {
		if (t === n) return;
		i = _e(t, za(e, !0));
	}
	e.checked !== i && (e.checked = i);
}
var Pa = {
	created(e, { value: t }, n) {
		e.checked = _e(t, n.props.value), e[Oa] = Ta(n), aa(e, "change", () => {
			e[Oa](Ra(e));
		});
	},
	beforeUpdate(e, { value: t, oldValue: n }, r) {
		e[Oa] = Ta(r), t !== n && (e.checked = _e(t, r.props.value));
	}
}, Fa = {
	deep: !0,
	created(e, { value: t, modifiers: { number: n } }, r) {
		e._modelValue = t, aa(e, "change", () => {
			let t = Array.prototype.filter.call(e.options, (e) => e.selected).map((e) => n ? ie(Ra(e)) : Ra(e)), r = e.multiple, i = r ? p(e._modelValue) ? new Set(t) : t : t[0], a = e._pendingValue = [r, r ? d(i) ? t.slice() : t : i];
			try {
				e[Oa](i);
			} finally {
				pn(() => {
					e._pendingValue === a && (e._pendingValue = void 0);
				});
			}
		}), e[Oa] = Ta(r);
	},
	mounted(e, { value: t }) {
		La(e, t);
	},
	beforeUpdate(e, { value: t }, n) {
		e._modelValue = t, e[Oa] = Ta(n);
	},
	updated(e, { value: t }) {
		let n = e._pendingValue;
		e._pendingValue = void 0, (!n || n[0] !== e.multiple || !Ia(t, n[1], n[0])) && La(e, t);
	}
};
function Ia(e, t, n) {
	if (!n || d(e)) return _e(e, t);
	if (p(e)) {
		if (e.size !== t.length) return !1;
		for (let n of t) if (!e.has(n)) return !1;
		return !0;
	}
	return !1;
}
function La(e, t) {
	let n = e.multiple, r = d(t);
	if (!n || r || p(t)) {
		for (let i = 0, a = e.options.length; i < a; i++) {
			let a = e.options[i], o = Ra(a);
			if (n) {
				if (r) {
					let e = typeof o;
					a.selected = e === "string" || e === "number" ? t.some((e) => String(e) === String(o)) : ve(t, o) > -1;
				} else a.selected = t.has(o);
			} else if (_e(Ra(a), t)) {
				e.selectedIndex !== i && (e.selectedIndex = i);
				return;
			}
		}
		!n && e.selectedIndex !== -1 && (e.selectedIndex = -1);
	}
}
function Ra(e) {
	return "_value" in e ? e._value : e.value;
}
function za(e, t) {
	let n = t ? "_trueValue" : "_falseValue";
	return n in e ? e[n] : t;
}
var Ba = {
	created(e, t, n) {
		Ha(e, t, n, null, "created");
	},
	mounted(e, t, n) {
		Ha(e, t, n, null, "mounted");
	},
	beforeUpdate(e, t, n, r) {
		Ha(e, t, n, r, "beforeUpdate");
	},
	updated(e, t, n, r) {
		Ha(e, t, n, r, "updated");
	}
};
function Va(e, t) {
	switch (e) {
		case "SELECT": return Fa;
		case "TEXTAREA": return ja;
		default: switch (t) {
			case "checkbox": return Ma;
			case "radio": return Pa;
			default: return ja;
		}
	}
}
function Ha(e, t, n, r, i) {
	let a = Va(e.tagName, n.props && n.props.type)[i];
	a && a(e, t, n, r);
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
}, Ka = /* @__PURE__ */ s({ patchProp: _a }, Hi), qa;
function Ja() {
	return qa ||= Ir(Ka);
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
		de: "Ersparnis",
		en: "Savings"
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
}, no = {
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
}, ro = Symbol("sax-dashboard");
function io(e) {
	return typeof e != "string" || e.length !== 5 && e.length !== 8 || !/^([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(e) ? null : e.length === 5 ? `${e}:00` : e;
}
function ao(e, t, n, r, i) {
	let a = no[r];
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
		case "time": {
			let e = io(t);
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
function so(e, t) {
	let n = $(() => e()?.language.toLowerCase().startsWith("de") ? "de" : "en"), r = /* @__PURE__ */ B(!1), i = /* @__PURE__ */ B(!1), a = /* @__PURE__ */ B(null), o = $(() => a.value ? no[n.value][a.value] : null), s = /* @__PURE__ */ Ut([]), c = /* @__PURE__ */ Mt(/* @__PURE__ */ new Map()), l = /* @__PURE__ */ Mt(/* @__PURE__ */ new Map()), u = (e, n) => JSON.stringify([
		t(),
		e,
		n
	]), d = 0;
	function f(e = !0) {
		e && (d += 1), r.value = !1, s.value = [];
		for (let [e, t] of c) t.pending ? t.error = null : c.delete(e);
	}
	let p = Mn([
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
	we(() => {
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
			error: p?.error ? no[n.value][p.error] : null
		};
	}
	async function h(t, n, i) {
		let a = m(t, n);
		if (!a || a.pending) return !1;
		let o = /* @__PURE__ */ Mt({
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
	async function g(t, n, i) {
		let a = [`${t}_start`, `${t}_end`], o = a.map((e) => m("time", e));
		if (o.some((e) => e?.pending)) return !1;
		let s = /* @__PURE__ */ Mt({
			pending: !1,
			error: null
		});
		for (let e of o) e && c.set(e.metadata.entity_id, s);
		let f = o[0]?.metadata.device_id, p = e();
		if (!r.value || !p?.callService || !f || o.some((e) => !e?.canControl || e.metadata.device_id !== f)) return s.error = "forbidden", !1;
		let h = io(n), g = io(i);
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
		ready: /* @__PURE__ */ Pt(r),
		connected: /* @__PURE__ */ Pt(i),
		error: o,
		entity: m,
		perform: h,
		performTimeWindow: g
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
}, bo = ["aria-labelledby", "aria-describedby"], xo = ["id"], So = ["id"], Co = { class: "entity-control__confirmation-actions" }, wo = ["disabled"], To = /*@__PURE__*/ Bn({
	__name: "EntityControl",
	props: {
		domain: { type: String },
		entityKey: { type: String },
		confirmSwitch: { type: Boolean },
		hideConfirmedValue: { type: Boolean },
		timeUnit: { type: Boolean }
	},
	setup(e) {
		let t = e, n = kn(ro), r = $(() => n?.entity(t.domain, t.entityKey)), i = Vn(), a = `sax-control-${i}`, o = `sax-status-${i}`, s = `sax-value-${i}`, c = /* @__PURE__ */ B(""), l = /* @__PURE__ */ B(), u = /* @__PURE__ */ Ut(null), d = $(() => r.value?.state?.state ?? ""), f = $(() => r.value?.state?.attributes ?? {}), p = $(() => {
			let e = f.value.options;
			return Array.isArray(e) ? e.filter((e) => typeof e == "string") : [];
		}), m = $(() => n?.language.value ?? "en"), h = $(() => t.hideConfirmedValue ? o : `${s} ${o}`), g = $(() => {
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
		}), v = $(() => !r.value?.canControl || r.value.pending), y = $(() => n?.connected.value ? r.value?.available ? r.value.metadata.can_control ? r.value.pending ? _.value.pending : "" : _.value.readOnly : _.value.unavailable : _.value.disconnected);
		function b(e) {
			return r.value?.available ? e : "";
		}
		Mn([() => r.value?.metadata.entity_id, () => d.value], ([, e]) => {
			c.value = b(e);
		}, { immediate: !0 });
		function x(e) {
			let t = f.value[e];
			return typeof t == "number" && Number.isFinite(t) ? t : void 0;
		}
		function S(e) {
			return r.value?.metadata.states[e] ?? e;
		}
		async function C() {
			v.value || !n || t.domain !== "number" && t.domain !== "time" || await n.perform(t.domain, t.entityKey, c.value);
		}
		function w() {
			u.value = null, l.value?.open && l.value.close();
		}
		function T() {
			l.value?.open || (u.value = null);
		}
		Mn([
			() => r.value?.metadata.entity_id,
			d,
			v,
			() => t.domain,
			() => t.entityKey,
			() => t.confirmSwitch
		], w, { flush: "sync" }), Qn(w);
		async function ee() {
			let e = u.value;
			w(), e && !v.value && n && e.entityId === r.value?.metadata.entity_id && e.sourceState === d.value && e.domain === t.domain && e.key === t.entityKey && await n.perform(t.domain, t.entityKey, e.desired);
		}
		async function E(e) {
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
		async function D(e) {
			let r = e.target, i = r.value;
			r.value = d.value, !v.value && n && await n.perform(t.domain, t.entityKey, i);
		}
		return (t, n) => r.value ? (q(), J("form", {
			key: 0,
			class: "entity-control",
			"aria-busy": r.value.pending,
			onSubmit: Ga(C, ["prevent"])
		}, [
			X("div", lo, [X("label", {
				for: a,
				class: "entity-control__name"
			}, P(r.value.name), 1), e.hideConfirmedValue ? Z("", !0) : (q(), J("p", {
				key: 0,
				id: s,
				class: "entity-control__value"
			}, [X("span", null, P(_.value.confirmed) + ":", 1), ui(" " + P(g.value), 1)]))]),
			X("div", uo, [e.domain === "switch" ? (q(), J("label", {
				key: 0,
				for: a,
				class: "entity-control__switch-target"
			}, [X("input", {
				id: a,
				type: "checkbox",
				role: "switch",
				checked: d.value === "on",
				disabled: v.value,
				"aria-describedby": h.value,
				onChange: E
			}, null, 40, fo)])) : e.domain === "select" ? (q(), J("select", {
				key: 1,
				id: a,
				value: r.value.available ? d.value : "",
				disabled: v.value,
				"aria-describedby": h.value,
				onChange: D
			}, [r.value.available ? Z("", !0) : (q(), J("option", mo, P(_.value.unavailable), 1)), (q(!0), J(G, null, U(p.value, (e) => (q(), J("option", {
				key: e,
				value: e
			}, P(S(e)), 9, ho))), 128))], 40, po)) : (q(), J(G, { key: 2 }, [En(X("input", {
				id: a,
				"onUpdate:modelValue": n[0] ||= (e) => c.value = e,
				type: e.domain === "number" ? "number" : "time",
				min: e.domain === "number" ? x("min") : void 0,
				max: e.domain === "number" ? x("max") : void 0,
				step: e.domain === "number" ? x("step") : 1,
				disabled: v.value,
				"aria-describedby": h.value,
				required: ""
			}, null, 8, go), [[Ba, c.value]]), X("button", {
				type: "submit",
				disabled: v.value || c.value === ""
			}, P(_.value.apply), 9, _o)], 64))]),
			X("div", {
				id: o,
				class: "entity-control__feedback"
			}, [r.value.error ? (q(), J("p", vo, P(r.value.error), 1)) : y.value ? (q(), J("p", yo, P(y.value), 1)) : Z("", !0)]),
			e.confirmSwitch ? (q(), J("dialog", {
				key: 0,
				ref_key: "dialog",
				ref: l,
				class: "entity-control__confirmation",
				"aria-labelledby": `${V(i)}-confirmation-title`,
				"aria-describedby": `${V(i)}-confirmation-question`,
				onCancel: Ga(w, ["prevent"]),
				onClose: T
			}, [
				X("h3", { id: `${V(i)}-confirmation-title` }, P(_.value.confirmationTitle), 9, xo),
				X("p", { id: `${V(i)}-confirmation-question` }, P(_.value.confirmationQuestion), 9, So),
				X("div", Co, [X("button", {
					type: "button",
					autofocus: "",
					onClick: w
				}, P(_.value.cancel), 1), X("button", {
					type: "button",
					disabled: v.value || !u.value,
					onClick: ee
				}, P(u.value?.desired ? _.value.turnOn : _.value.turnOff), 9, wo)])
			], 40, bo)) : Z("", !0)
		], 40, co)) : Z("", !0);
	}
}), Eo = ".entity-control{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));color:var(--primary-text-color,#212121);box-shadow:var(--ha-card-box-shadow,none);flex-wrap:wrap;align-items:center;gap:12px 24px;padding:20px;display:flex}.entity-control__description{overflow-wrap:anywhere;flex:200px;min-width:0}.entity-control__name{font-weight:500;line-height:1.5;display:block}.entity-control__value{color:var(--secondary-text-color,#666);margin:4px 0 0;font-size:.9em;line-height:1.5}.entity-control__input{flex-wrap:wrap;align-items:center;gap:8px;max-width:100%;display:flex}.entity-control__switch-target{display:contents}.entity-control input,.entity-control select,.entity-control button{border:1px solid var(--divider-color,#767676);max-width:100%;min-height:44px;color:inherit;background:var(--card-background-color,#fff);font:inherit;border-radius:6px;padding:8px 12px}.entity-control input[type=number]{width:120px}.entity-control input[type=checkbox]{width:28px;accent-color:var(--primary-color,#03a9f4);cursor:pointer;margin:0 8px}.entity-control button{border-color:var(--primary-color,#03a9f4);color:var(--primary-text-color,#212121);cursor:pointer}.entity-control :disabled{cursor:not-allowed;opacity:.6}.entity-control input:focus-visible,.entity-control select:focus-visible,.entity-control button:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.entity-control__feedback{color:var(--secondary-text-color,#666);flex-basis:100%;line-height:1.5}.entity-control__feedback:empty{display:none}.entity-control__feedback p{margin:0}.entity-control__error{color:var(--error-color,#b71c1c)}.entity-control__confirmation{border:1px solid var(--divider-color,#767676);background:var(--card-background-color,#fff);width:min(440px,100vw - 32px);max-height:calc(100vh - 32px);color:var(--primary-text-color,#212121);border-radius:12px;padding:24px;overflow:auto}.entity-control__confirmation::backdrop{background:#0000008c}.entity-control__confirmation h3{margin:0;font-size:20px;line-height:1.4}.entity-control__confirmation p{margin:16px 0 24px;line-height:1.6}.entity-control__confirmation-actions{flex-wrap:wrap;justify-content:flex-end;gap:12px;display:flex}@container sax-content (width>=860px){.entity-control{gap:8px 12px;padding:14px}.entity-control__description{flex-basis:140px}.entity-control__value{margin-top:2px;font-size:14px}.entity-control input[type=number]{width:104px}}", Do = (e, t) => {
	let n = e.__vccOpts || e;
	for (let [e, r] of t) n[e] = r;
	return n;
}, Oo = /*#__PURE__*/ Do(To, [["styles", [Eo]]]), ko = [
	"role",
	"aria-labelledby",
	"aria-valuemin",
	"aria-valuemax",
	"aria-valuenow",
	"aria-valuetext"
], Ao = {
	viewBox: "0 0 240 124",
	"aria-hidden": "true"
}, jo = ["stroke-dasharray", "stroke-dashoffset"], Mo = ["transform"], No = {
	class: "entity-gauge__scale",
	"aria-hidden": "true"
}, Po = { class: "entity-gauge__value" }, Fo = {
	key: 0,
	class: "entity-gauge__range"
}, Io = /*#__PURE__*/ Do(/* @__PURE__ */ Bn({
	__name: "EntityGauge",
	props: {
		entityKey: { type: String },
		maximum: { type: Number },
		segments: { type: Array }
	},
	setup(e) {
		let t = e, n = kn(ro), r = $(() => n?.entity("sensor", t.entityKey)), i = `sax-gauge-${Vn()}`, a = $(() => {
			let e = r.value?.state?.state.trim();
			if (!r.value?.available || !e) return null;
			let t = Number(e);
			return Number.isFinite(t) ? t : null;
		}), o = $(() => a.value === null ? null : Math.max(0, Math.min(t.maximum, a.value))), s = $(() => a.value === null ? null : [...t.segments].reverse().find((e) => a.value >= e.from)?.label ?? t.segments[0]?.label), c = $(() => r.value?.available && a.value === null ? n?.language.value === "de" ? "Unbekannt" : "Unknown" : r.value?.displayValue), l = $(() => t.segments.map((e, n) => ({
			...e,
			offset: -(e.from / t.maximum) * 100,
			length: ((t.segments[n + 1]?.from ?? t.maximum) - e.from) / t.maximum * 100
		})));
		return (t, n) => r.value ? (q(), J("section", {
			key: 0,
			class: "entity-gauge",
			"aria-labelledby": i
		}, [X("h2", { id: i }, P(r.value.name), 1), X("div", {
			class: "entity-gauge__meter",
			role: o.value === null ? void 0 : "meter",
			"aria-labelledby": o.value === null ? void 0 : i,
			"aria-valuemin": o.value === null ? void 0 : 0,
			"aria-valuemax": o.value === null ? void 0 : e.maximum,
			"aria-valuenow": o.value ?? void 0,
			"aria-valuetext": o.value === null ? void 0 : `${c.value} · ${s.value}`
		}, [
			(q(), J("svg", Ao, [n[1] ||= X("path", {
				class: "entity-gauge__track",
				d: "M20 110 A100 100 0 0 1 220 110"
			}, null, -1), o.value === null ? Z("", !0) : (q(), J(G, { key: 0 }, [
				(q(!0), J(G, null, U(l.value, (e) => (q(), J("path", {
					key: e.from,
					class: N(["entity-gauge__segment", `entity-gauge__segment--${e.color}`]),
					d: "M20 110 A100 100 0 0 1 220 110",
					pathLength: "100",
					"stroke-dasharray": `${e.length} 100`,
					"stroke-dashoffset": e.offset
				}, null, 10, jo))), 128)),
				X("line", {
					class: "entity-gauge__needle",
					x1: "120",
					y1: "110",
					x2: "120",
					y2: "33",
					transform: `rotate(${o.value / e.maximum * 180 - 90} 120 110)`
				}, null, 8, Mo),
				n[0] ||= X("circle", {
					class: "entity-gauge__pivot",
					cx: "120",
					cy: "110",
					r: "5"
				}, null, -1)
			], 64))])),
			X("div", No, [n[2] ||= X("span", null, "0", -1), X("span", null, P(e.maximum), 1)]),
			X("p", Po, P(c.value), 1),
			s.value ? (q(), J("p", Fo, P(s.value), 1)) : Z("", !0)
		], 8, ko)])) : Z("", !0);
	}
}), [["styles", [".entity-gauge{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);text-align:center;padding:24px}.entity-gauge h2{overflow-wrap:anywhere;margin:0 0 20px;font-size:16px;font-weight:500;line-height:1.5}.entity-gauge__meter{max-width:260px;margin:0 auto}.entity-gauge svg{fill:none;width:100%;display:block}.entity-gauge__track,.entity-gauge__segment{stroke-width:15px;stroke-linecap:butt}.entity-gauge__track{stroke:var(--divider-color,#e0e0e0)}.entity-gauge__segment--red{stroke:var(--error-color,#db4437)}.entity-gauge__segment--yellow{stroke:var(--warning-color,#f4b400)}.entity-gauge__segment--green{stroke:var(--success-color,#0f9d58)}.entity-gauge__needle{stroke:var(--primary-text-color,#212121);stroke-width:3px;stroke-linecap:round}.entity-gauge__pivot{stroke:none;fill:var(--primary-text-color,#212121)}.entity-gauge__scale{color:var(--secondary-text-color,#666);justify-content:space-between;padding:2px 7px;font-size:12px;display:flex}.entity-gauge__value{overflow-wrap:anywhere;margin:10px 0 0;font-size:28px;font-weight:500;line-height:1.4}.entity-gauge__range{color:var(--secondary-text-color,#666);margin:4px 0 0;font-size:14px;line-height:1.5}@container sax-content (width>=860px){.entity-gauge{padding:16px}.entity-gauge h2{margin-bottom:8px}.entity-gauge__meter{max-width:180px}.entity-gauge__value{margin-top:6px;font-size:24px}.entity-gauge__range{margin-top:2px}}"]]]), Lo = {
	key: 0,
	class: "entity-value"
}, Ro = { class: "entity-value__name" }, zo = { class: "entity-value__state" }, Bo = /*#__PURE__*/ Do(/* @__PURE__ */ Bn({
	__name: "EntityValue",
	props: {
		domain: { type: null },
		entityKey: { type: String }
	},
	setup(e) {
		let t = e, n = kn(ro), r = $(() => n?.entity(t.domain, t.entityKey));
		return (e, t) => r.value ? (q(), J("div", Lo, [X("span", Ro, P(r.value.name), 1), X("span", zo, P(r.value.displayValue), 1)])) : Z("", !0);
	}
}), [["styles", [".entity-value{color:var(--primary-text-color,#212121);overflow-wrap:anywhere;flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:8px 20px;line-height:1.5;display:flex}.entity-value__name{color:var(--secondary-text-color,#666)}.entity-value__state{font-weight:500}"]]]), Vo = { class: "general-view" }, Ho = {
	key: 0,
	class: "general-view__status",
	role: "status"
}, Uo = {
	key: 1,
	class: "general-view__status",
	role: "status"
}, Wo = {
	key: 2,
	class: "general-view__gauges"
}, Go = ["aria-labelledby"], Ko = ["id"], qo = { class: "general-view__rows" }, Jo = /*#__PURE__*/ Do(/* @__PURE__ */ Bn({
	__name: "GeneralView",
	setup(e) {
		let t = kn(ro), n = Vn(), r = $(() => t?.language.value === "de" ? {
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
		return (e, i) => (q(), J("div", Vo, [
			!V(t)?.ready.value && !V(t)?.error.value ? (q(), J("p", Ho, P(r.value.loading), 1)) : V(t)?.ready.value && !s.value ? (q(), J("p", Uo, P(r.value.empty), 1)) : Z("", !0),
			o.value ? (q(), J("div", Wo, [oi(Io, {
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
			}, null, 8, ["segments"]), oi(Io, {
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
			(q(!0), J(G, null, U(a.value, (e) => (q(), J("section", {
				key: e.title,
				class: N(["general-view__card", `general-view__card--${e.title}`]),
				"aria-labelledby": `${V(n)}-${e.title}`
			}, [X("h2", { id: `${V(n)}-${e.title}` }, P(r.value[e.title]), 9, Ko), X("div", qo, [(q(!0), J(G, null, U(e.entities, ([e, t]) => (q(), J(G, { key: `${e}.${t}` }, [e === "number" || e === "switch" ? (q(), Y(Oo, {
				key: 0,
				domain: e,
				"entity-key": t,
				"confirm-switch": e === "switch" && t === "storage_switch"
			}, null, 8, [
				"domain",
				"entity-key",
				"confirm-switch"
			])) : (q(), Y(Bo, {
				key: 1,
				domain: e,
				"entity-key": t
			}, null, 8, ["domain", "entity-key"]))], 64))), 128))])], 10, Go))), 128))
		]));
	}
}), [["styles", [".general-view{gap:20px;min-width:0;margin-top:24px;display:grid}.general-view__gauges{grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr));gap:20px;display:grid}.general-view__card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.general-view__card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.general-view__rows{gap:16px;display:grid}.general-view__rows .entity-control{border:0;border-bottom:1px solid var(--divider-color,#e0e0e0);box-shadow:none;border-radius:0;padding:0 0 16px}.general-view__rows .entity-control:last-child{border-bottom:0;padding-bottom:0}.general-view__status{color:var(--secondary-text-color,#666);margin:0;line-height:1.6}@container sax-content (width>=860px){.general-view{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;gap:16px;margin-top:16px}.general-view__gauges{grid-column:1;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.general-view__gauges:has(>:only-child){grid-template-columns:minmax(0,1fr)}.general-view__card{padding:18px}.general-view__card--power{grid-column:1}.general-view__card--device{grid-area:1/2/span 2}:is(.general-view:not(:has(.general-view__gauges)) .general-view__card--device,.general-view:not(:has(.general-view__card--power)) .general-view__card--device){grid-row:1}:is(.general-view:has(>:only-child),.general-view:not(:has(.general-view__card--device))){grid-template-columns:minmax(0,1fr)}.general-view__card:only-child{grid-area:auto}.general-view__card h2{margin-bottom:12px;font-size:16px}.general-view__rows{gap:10px}.general-view__rows .entity-control{padding:0 0 10px}.general-view__rows .entity-control:last-child{padding-bottom:0}.general-view__status{grid-column:1/-1}}@media (max-width:600px){.general-view,.general-view__gauges{gap:16px}.general-view__card{padding:20px}}"]]]), Yo = ["aria-busy"], Xo = { class: "time-window-control__inputs" }, Zo = ["for"], Qo = [
	"id",
	"value",
	"disabled",
	"aria-describedby",
	"onInput"
], $o = ["disabled"], es = ["id"], ts = ["aria-label"], ns = [
	"disabled",
	"aria-label",
	"aria-valuenow",
	"aria-valuetext",
	"aria-describedby",
	"onKeydown",
	"onPointerdown"
], rs = {
	class: "time-window-control__marker-label",
	"aria-hidden": "true"
}, is = { class: "time-window-control__duration" }, as = ["id"], os = ["id"], ss = {
	key: 0,
	class: "time-window-control__error",
	role: "alert"
}, cs = {
	key: 1,
	role: "status"
}, ls = /*#__PURE__*/ Do(/* @__PURE__ */ Bn({
	__name: "TimeWindowControl",
	props: { kind: { type: String } },
	setup(e) {
		let t = e, n = kn(ro), r = $(() => n?.entity("time", `${t.kind}_start`)), i = $(() => n?.entity("time", `${t.kind}_end`)), a = `sax-window-${Vn()}`, o = $(() => n?.language.value ?? "en"), s = $(() => o.value === "de" ? {
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
		}), c = /* @__PURE__ */ B(""), l = /* @__PURE__ */ B(""), u = /* @__PURE__ */ B(), d = /* @__PURE__ */ B(!1), f = /* @__PURE__ */ B(!1), p = /* @__PURE__ */ B(!1), m = 0, h = null;
		function g(e) {
			if (!/^(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(e)) return null;
			let [t, n, r = 0] = e.split(":").map(Number);
			return t * 3600 + n * 60 + r;
		}
		function _(e) {
			let t = (e) => String(e).padStart(2, "0");
			return `${t(Math.floor(e / 3600))}:${t(Math.floor(e / 60) % 60)}:${t(e % 60)}`;
		}
		function v(e) {
			let t = g(e);
			if (t === null) return "—";
			let n = _(t);
			return t % 60 ? n : n.slice(0, 5);
		}
		let y = $(() => r.value?.state?.state ?? ""), b = $(() => i.value?.state?.state ?? ""), x = $(() => !!r.value?.available && !!i.value?.available && g(y.value) !== null && g(b.value) !== null), S = $(() => typeof r.value?.metadata.device_id == "string" && r.value.metadata.device_id.length > 0 && r.value.metadata.device_id === i.value?.metadata.device_id), C = $(() => x.value ? `${v(y.value)} – ${v(b.value)}${s.value.unit ? ` ${s.value.unit}` : ""}` : [r.value, i.value].map((e) => e?.available && g(e.state?.state ?? "") !== null ? `${v(e.state.state)}${s.value.unit ? ` ${s.value.unit}` : ""}` : s.value.missingValue).join(" – ")), w = $(() => g(c.value) !== null && g(l.value) !== null), T = $(() => g(c.value) !== g(y.value) || g(l.value) !== g(b.value)), ee = $(() => d.value || !!r.value?.pending || !!i.value?.pending), E = $(() => !n?.ready.value || !n.connected.value || !x.value || !S.value || !r.value?.canControl || !i.value?.canControl || ee.value), D = $(() => r.value?.error || i.value?.error), O = $(() => n?.connected.value ? x.value ? S.value ? !r.value?.canControl || !i.value?.canControl ? s.value.readOnly : ee.value ? s.value.pending : f.value ? s.value.awaiting : p.value ? s.value.changed : w.value ? "" : s.value.invalid : s.value.incompatible : s.value.unavailable : s.value.disconnected), k = $(() => {
			let e = g(c.value), t = g(l.value);
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
		}), A = $(() => {
			let e = g(c.value), t = g(l.value);
			return e === null || t === null || e === t ? [] : (t > e ? [[e, t]] : [[e, 86400], [0, t]]).filter(([e, t]) => e !== t).map(([e, t]) => ({
				left: `${e / 864}%`,
				width: `${(t - e) / 864}%`
			}));
		}), te = $(() => [{
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
		function j() {
			let e = h;
			h = null, e?.target.hasPointerCapture?.(e.pointerId) && e.target.releasePointerCapture(e.pointerId);
		}
		Mn([
			() => r.value?.metadata.entity_id,
			() => i.value?.metadata.entity_id,
			y,
			b,
			x,
			S,
			() => r.value?.metadata.device_id,
			() => i.value?.metadata.device_id,
			() => t.kind
		], (e, t) => {
			let n = typeof t?.[2] == "string" ? t[2] : "", r = typeof t?.[3] == "string" ? t[3] : "", i = g(c.value) !== g(n) || g(l.value) !== g(r), a = ee.value || f.value;
			m += 1, j(), d.value = !1, f.value = !1, p.value = !!t?.length && i && !a && x.value, c.value = x.value ? y.value : "", l.value = x.value ? b.value : "";
		}, {
			immediate: !0,
			flush: "sync"
		}), Mn(E, (e) => {
			e && j();
		}, { flush: "sync" }), Qn(j);
		function ne(e, t) {
			E.value || (e === "start" ? c.value = t : l.value = t, f.value = !1, p.value = !1);
		}
		function re(e, t) {
			ne(e, t.target.value);
		}
		function ie(e, t) {
			if (E.value) return;
			let n = g(e === "start" ? c.value : l.value);
			if (n === null) return;
			let r = {
				ArrowRight: 60,
				ArrowUp: 60,
				ArrowLeft: -60,
				ArrowDown: -60,
				PageUp: 900,
				PageDown: -900
			};
			(t.key in r || t.key === "Home" || t.key === "End") && (t.preventDefault(), ne(e, _(t.key === "Home" ? 0 : t.key === "End" ? 86399 : Math.max(0, Math.min(86399, Math.floor(n / 60) * 60 + r[t.key])))));
		}
		function ae(e) {
			if (!h || h.pointerId !== e.pointerId || E.value || !u.value) return;
			let t = u.value.getBoundingClientRect();
			if (t.width <= 0) return;
			let n = Math.max(0, Math.min(1439, Math.round(h.originSeconds / 60 + (e.clientX - h.originX) / t.width * 1440)));
			h.moved = !0, ne(h.boundary, _(n * 60));
		}
		function M(e, t) {
			if (E.value || !w.value || t.button !== 0 || t.isPrimary === !1) return;
			let n = t.currentTarget;
			n.focus(), h = {
				boundary: e,
				pointerId: t.pointerId,
				target: n,
				moved: !1,
				originX: t.clientX,
				originSeconds: g(e === "start" ? c.value : l.value)
			}, n.setPointerCapture?.(t.pointerId), t.preventDefault();
		}
		function oe(e) {
			h?.pointerId === e.pointerId && (h.moved && ae(e), j());
		}
		async function ce() {
			if (!n || E.value || !w.value || !T.value) return;
			let e = m;
			d.value = !0, p.value = !1;
			let r = await n.performTimeWindow(t.kind, c.value, l.value);
			e === m && (d.value = !1, f.value = r && T.value);
		}
		return (e, t) => r.value || i.value ? (q(), J("form", {
			key: 0,
			class: "time-window-control",
			"aria-busy": ee.value,
			onSubmit: Ga(ce, ["prevent"])
		}, [
			X("div", Xo, [(q(!0), J(G, null, U(te.value, (e) => (q(), J("label", {
				key: e.key,
				for: `${a}-${e.key}`,
				class: "time-window-control__field"
			}, [X("span", null, [ui(P(e.name), 1), s.value.unit ? (q(), J(G, { key: 0 }, [ui(" (" + P(s.value.unit) + ")", 1)], 64)) : Z("", !0)]), X("input", {
				id: `${a}-${e.key}`,
				type: "time",
				step: "1",
				required: "",
				value: e.value,
				disabled: E.value,
				"aria-describedby": `${a}-confirmed ${a}-status`,
				onInput: (t) => re(e.key, t)
			}, null, 40, Qo)], 8, Zo))), 128)), X("button", {
				class: "time-window-control__apply",
				type: "submit",
				disabled: E.value || !w.value || !T.value
			}, P(s.value.apply), 9, $o)]),
			X("p", {
				id: `${a}-confirmed`,
				class: "time-window-control__confirmed"
			}, P(s.value.confirmed) + ": " + P(C.value), 9, es),
			X("div", {
				class: "time-window-control__timeline",
				"aria-label": s.value.timeline,
				role: "group"
			}, [X("div", {
				ref_key: "rail",
				ref: u,
				class: N(["time-window-control__rail", { "time-window-control__rail--draft": T.value }])
			}, [(q(!0), J(G, null, U(A.value, (e, t) => (q(), J("span", {
				key: t,
				class: "time-window-control__segment",
				style: se(e)
			}, null, 4))), 128))], 2), (q(!0), J(G, null, U(te.value, (e) => (q(), J("button", {
				key: e.key,
				type: "button",
				role: "slider",
				class: N(["time-window-control__handle", `time-window-control__handle--${e.key}`]),
				style: se({ left: `${(g(e.value) ?? 0) / 864}%` }),
				disabled: E.value || !w.value,
				"aria-label": e.marker,
				"aria-valuemin": "0",
				"aria-valuemax": "86399",
				"aria-valuenow": g(e.value) ?? 0,
				"aria-valuetext": `${v(e.value)}${s.value.unit ? ` ${s.value.unit}` : ""}`,
				"aria-describedby": `${a}-help ${a}-confirmed`,
				"aria-orientation": "horizontal",
				onKeydown: (t) => ie(e.key, t),
				onPointerdown: (t) => M(e.key, t),
				onPointermove: ae,
				onPointerup: oe,
				onPointercancel: j,
				onLostpointercapture: j
			}, [X("span", rs, P(e.shortName), 1), t[0] ||= X("span", {
				class: "time-window-control__marker-dot",
				"aria-hidden": "true"
			}, null, -1)], 46, ns))), 128))], 8, ts),
			t[1] ||= X("div", {
				class: "time-window-control__ticks",
				"aria-hidden": "true"
			}, [
				X("span", null, "00"),
				X("span", null, "06"),
				X("span", null, "12"),
				X("span", null, "18"),
				X("span", null, "24")
			], -1),
			X("p", is, [X("span", null, P(T.value ? s.value.draft : s.value.duration) + ":", 1), ui(" " + P(k.value), 1)]),
			X("p", {
				id: `${a}-help`,
				class: "time-window-control__sr-only"
			}, P(s.value.help), 9, as),
			X("div", {
				id: `${a}-status`,
				class: "time-window-control__feedback"
			}, [D.value ? (q(), J("p", ss, P(D.value), 1)) : O.value ? (q(), J("p", cs, P(O.value), 1)) : Z("", !0)], 8, os)
		], 40, Yo)) : Z("", !0);
	}
}), [["styles", [".time-window-control{min-width:0;color:var(--primary-text-color,#212121)}.time-window-control__inputs{flex-wrap:wrap;align-items:end;gap:10px;display:flex}.time-window-control__field{flex:136px;gap:5px;min-width:0;font-size:14px;display:grid}.time-window-control__field input,.time-window-control__apply{box-sizing:border-box;border:1px solid var(--divider-color,#767676);min-width:0;max-width:100%;min-height:44px;color:inherit;background:var(--card-background-color,#fff);font:inherit;border-radius:6px;padding:8px 10px;font-size:16px}.time-window-control__field input{width:100%}.time-window-control__apply{border-color:var(--primary-color,#03a9f4);cursor:pointer;flex:none}.time-window-control__confirmed,.time-window-control__duration{color:var(--secondary-text-color,#666);overflow-wrap:anywhere;margin:9px 0 0;font-size:14px;line-height:1.5}.time-window-control__timeline{height:94px;margin:6px 22px 0;position:relative}.time-window-control__rail{background:var(--divider-color,#ddd);border-radius:3px;height:6px;position:absolute;top:44px;left:0;right:0;overflow:hidden}.time-window-control__segment{background:var(--primary-color,#03a9f4);height:100%;position:absolute}.time-window-control__rail--draft .time-window-control__segment{background-image:repeating-linear-gradient(135deg,#0000 0 5px,#ffffff3d 5px 8px)}.time-window-control__handle{width:44px;height:44px;min-height:0;color:inherit;font:inherit;cursor:ew-resize;touch-action:none;background:0 0;border:0;border-radius:6px;padding:0;display:block;position:absolute;transform:translate(-50%)}.time-window-control__handle--start{top:0}.time-window-control__handle--end{top:50px}.time-window-control__marker-label{white-space:nowrap;width:max-content;font-size:12px;line-height:16px;position:absolute;left:50%;transform:translate(-50%)}.time-window-control__handle--start .time-window-control__marker-label{top:0}.time-window-control__handle--end .time-window-control__marker-label{bottom:0}.time-window-control__marker-dot{box-sizing:border-box;border:2px solid var(--primary-color,#03a9f4);background:var(--card-background-color,#fff);border-radius:50%;width:18px;height:18px;position:absolute;left:13px}.time-window-control__handle--start .time-window-control__marker-dot{bottom:3px}.time-window-control__handle--end .time-window-control__marker-dot{top:3px}.time-window-control__marker-dot:after{content:\"\";background:var(--primary-color,#03a9f4);width:2px;height:6px;position:absolute;left:6px}.time-window-control__handle--start .time-window-control__marker-dot:after{top:14px}.time-window-control__handle--end .time-window-control__marker-dot:after{bottom:14px}.time-window-control__ticks{height:18px;color:var(--secondary-text-color,#666);margin:0 22px;font-size:12px;position:relative}.time-window-control__ticks span{white-space:nowrap;position:absolute;left:0}.time-window-control__ticks span:nth-child(2){left:25%;transform:translate(-50%)}.time-window-control__ticks span:nth-child(3){left:50%;transform:translate(-50%)}.time-window-control__ticks span:nth-child(4){left:75%;transform:translate(-50%)}.time-window-control__ticks span:last-child{left:auto;right:0}.time-window-control :disabled{opacity:.6;cursor:not-allowed}.time-window-control input:focus-visible,.time-window-control button:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:2px}.time-window-control__feedback{color:var(--secondary-text-color,#666);overflow-wrap:anywhere;margin-top:6px;font-size:14px;line-height:1.5}.time-window-control__feedback:empty{display:none}.time-window-control__feedback p{margin:0}.time-window-control__error{color:var(--error-color,#b71c1c)}.time-window-control__sr-only{clip-path:inset(50%);white-space:nowrap;border:0;width:1px;height:1px;margin:-1px;padding:0;position:absolute;overflow:hidden}"]]]), us = { class: "charging-view" }, ds = {
	key: 0,
	class: "charging-view__status",
	role: "status"
}, fs = {
	key: 1,
	class: "charging-view__status",
	role: "status"
}, ps = {
	key: 3,
	class: "charging-view__cards"
}, ms = ["aria-labelledby"], hs = ["id"], gs = /*#__PURE__*/ Do(/* @__PURE__ */ Bn({
	__name: "ChargingLayout",
	props: {
		switchKey: { type: String },
		cards: { type: Array }
	},
	setup(e) {
		let t = e, n = kn(ro), r = Vn(), i = $(() => n?.language.value ?? "en"), a = $(() => t.cards.map((e) => {
			let t = e.entities.filter(([e, t]) => n?.entity(e, t));
			return {
				...e,
				showTimeWindow: !!(e.timeWindow && t.some(([e]) => e === "time")),
				entities: t.filter(([t]) => !e.timeWindow || t !== "time")
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
		return (t, l) => (q(), J("div", us, [
			!V(n)?.ready.value && !V(n)?.error.value ? (q(), J("p", ds, P(c.value.loading), 1)) : V(n)?.ready.value && !s.value && !a.value.length ? (q(), J("p", fs, P(c.value.empty), 1)) : Z("", !0),
			s.value ? (q(), Y(Oo, {
				key: 2,
				domain: "switch",
				"entity-key": e.switchKey
			}, null, 8, ["entity-key"])) : Z("", !0),
			o.value.length ? (q(), J("div", ps, [(q(!0), J(G, null, U(o.value, (e) => (q(), J("div", {
				key: e.key,
				class: N(["charging-view__group", { "charging-view__group--wide": e.wide }])
			}, [(q(!0), J(G, null, U(e.cards, (e) => (q(), J("section", {
				key: e.key,
				class: "charging-view__card",
				"aria-labelledby": `${V(r)}-${e.key}`
			}, [
				X("h2", { id: `${V(r)}-${e.key}` }, P(e.title[i.value]), 9, hs),
				e.showTimeWindow && e.timeWindow ? (q(), Y(ls, {
					key: 0,
					kind: e.timeWindow
				}, null, 8, ["kind"])) : Z("", !0),
				e.entities.length ? (q(), J("div", {
					key: 1,
					class: N(["charging-view__rows", {
						"charging-view__rows--columns": e.layout === "columns",
						"charging-view__rows--months": e.layout === "months"
					}])
				}, [(q(!0), J(G, null, U(e.entities, ([t, n]) => (q(), J(G, { key: `${t}.${n}` }, [t === "switch" || t === "number" || t === "time" || t === "select" ? (q(), Y(Oo, {
					key: 0,
					domain: t,
					"entity-key": n,
					"hide-confirmed-value": e.layout === "months" && t === "switch"
				}, null, 8, [
					"domain",
					"entity-key",
					"hide-confirmed-value"
				])) : (q(), Y(Bo, {
					key: 1,
					domain: t,
					"entity-key": n
				}, null, 8, ["domain", "entity-key"]))], 64))), 128))], 2)) : Z("", !0)
			], 8, ms))), 128))], 2))), 128))])) : Z("", !0)
		]));
	}
}), [["styles", [".charging-view{gap:20px;min-width:0;margin-top:24px;display:grid}.charging-view__cards,.charging-view__group{align-content:start;gap:20px;min-width:0;display:grid}.charging-view__card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.charging-view__card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.charging-view__rows{gap:16px;display:grid}.charging-view__card>.time-window-control+.charging-view__rows{border-top:1px solid var(--divider-color,#e0e0e0);margin-top:20px;padding-top:16px}.charging-view__rows .entity-control{border:0;border-bottom:1px solid var(--divider-color,#e0e0e0);box-shadow:none;border-radius:0;padding:0 0 16px}.charging-view__rows .entity-control:last-child{border-bottom:0;padding-bottom:0}.charging-view__status{color:var(--secondary-text-color,#666);margin:0;line-height:1.6}@media (max-width:600px){.charging-view,.charging-view__cards,.charging-view__group{gap:16px}.charging-view__card{padding:20px}}@container sax-content (width>=860px){.charging-view{gap:14px;margin-top:16px}.charging-view__cards{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;gap:16px}.charging-view__group{gap:14px}.charging-view__group--wide{grid-column:1/-1}.charging-view__card{padding:18px}.charging-view__card h2{margin-bottom:12px;font-size:16px}.charging-view__rows{gap:12px}.charging-view__rows .entity-control{gap:8px 12px;padding-bottom:12px}.charging-view__rows .entity-control:last-child{padding-bottom:0}.charging-view__rows .entity-control__description{flex-basis:120px}.charging-view__rows--columns{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;column-gap:24px}.charging-view__rows--columns>:last-child:nth-child(odd){grid-column:1/-1}.charging-view__rows--columns .entity-value{min-height:44px;padding-block:8px}}.charging-view__rows--months{grid-template-columns:repeat(auto-fit,minmax(min(100%,132px),1fr));gap:8px}.charging-view__rows--months .entity-control,.charging-view__rows--months .entity-control:last-child{border:1px solid var(--divider-color,#e0e0e0);border-radius:8px;gap:4px;min-width:0;padding:4px 6px}.charging-view__rows--months .entity-control__description{flex-basis:0}.charging-view__rows--months .entity-control__name{font-size:14px;line-height:1.3}.charging-view__rows--months .entity-control__input{flex-shrink:0}.charging-view__rows--months .entity-control__switch-target{cursor:pointer;justify-content:center;align-items:center;width:44px;min-height:44px;display:flex}.charging-view__rows--months .entity-control__switch-target:has(:disabled){cursor:not-allowed}.charging-view__rows--months .entity-control input[type=checkbox]{flex-shrink:0;width:22px;height:22px;min-height:22px;margin:0;padding:0}.charging-view__rows--months .entity-control__feedback{overflow-wrap:anywhere;min-width:0;font-size:14px}@container sax-content (width>=600px){.charging-view__rows--months{grid-template-columns:repeat(4,minmax(0,1fr))}}@container sax-content (width>=960px){.charging-view__rows--months{grid-template-columns:repeat(6,minmax(0,1fr))}}"]]]), _s = /* @__PURE__ */ Bn({
	__name: "TimedChargingView",
	setup(e) {
		let t = [
			{
				key: "window",
				group: "schedule",
				timeWindow: "timed_charge",
				title: {
					de: "Zeitfenster",
					en: "Time window"
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
		];
		return (e, n) => (q(), Y(gs, {
			"switch-key": "timed_charge_enabled",
			cards: t
		}));
	}
}), vs = /* @__PURE__ */ Bn({
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
		return (e, n) => (q(), Y(gs, {
			"switch-key": "grid_serving_enabled",
			cards: t
		}));
	}
}), ys = /* @__PURE__ */ Bn({
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
		return (e, n) => (q(), Y(gs, {
			"switch-key": "price_charge_enabled",
			cards: t
		}));
	}
});
//#endregion
//#region src/savings.ts
function bs(e) {
	if (typeof e != "number" && typeof e != "string" || typeof e == "string" && !e.trim()) return null;
	let t = Number(e);
	return Number.isFinite(t) ? t : null;
}
function xs(e) {
	return {
		comma_decimal: "en-US",
		decimal_comma: "de-DE",
		space_comma: "fr-FR"
	}[e?.locale?.number_format ?? ""] ?? e?.locale?.language ?? e?.language ?? "en";
}
function Ss(e, t, n = 2) {
	let r = bs(e);
	return r === null ? null : new Intl.NumberFormat(xs(t), {
		minimumFractionDigits: n,
		maximumFractionDigits: n,
		useGrouping: t?.locale?.number_format !== "none"
	}).format(r);
}
function Cs(e, t, n = {
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
function ws(e, t) {
	let n = (e) => /^\d{4}-\d{2}-\d{2}$/.test(e) && Number(e.slice(0, 4)) > 0 && Number.isFinite(Date.parse(`${e}T00:00:00Z`)) && (/* @__PURE__ */ new Date(`${e}T00:00:00Z`)).toISOString().slice(0, 10) === e;
	return n(e) && n(t) && e <= t;
}
function Ts(e) {
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
function Es(e, t, n) {
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
					first_weekday: Ts(u),
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
		if (!ws(e, t)) {
			a.value = "invalid";
			return;
		}
		o = {
			start_date: e,
			end_date: t
		}, l();
	}
	return Mn([
		() => e()?.connection,
		t,
		n,
		() => Ts(e()),
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
//#region src/views/SavingsView.vue?vue&type=script&setup=true&lang.ts
var Ds = { class: "savings-view" }, Os = { class: "savings-overview" }, ks = ["aria-labelledby"], As = ["id"], js = ["aria-labelledby"], Ms = ["id"], Ns = {
	key: 0,
	class: "savings-progress"
}, Ps = ["id"], Fs = { class: "savings-large" }, Is = [
	"role",
	"aria-labelledby",
	"aria-valuemin",
	"aria-valuemax",
	"aria-valuenow"
], Ls = {
	key: 1,
	class: "savings-rows"
}, Rs = { key: 0 }, zs = { key: 1 }, Bs = { key: 2 }, Vs = { key: 3 }, Hs = ["aria-label"], Us = { class: "savings-large" }, Ws = ["aria-labelledby"], Gs = ["id"], Ks = { class: "savings-table-scroll" }, qs = { class: "savings-table" }, Js = { colspan: "2" }, Ys = { key: 0 }, Xs = { key: 0 }, Zs = { key: 1 }, Qs = ["aria-labelledby"], $s = ["id"], ec = ["for"], tc = ["id", "max"], nc = ["for"], rc = ["id", "min"], ic = { type: "submit" }, ac = ["disabled"], oc = {
	key: 0,
	role: "status"
}, sc = {
	key: 1,
	role: "alert"
}, cc = { class: "savings-selected-dates" }, lc = { class: "savings-large" }, uc = ["id"], dc = { class: "savings-chart-hint" }, fc = [
	"viewBox",
	"aria-labelledby",
	"aria-describedby"
], pc = ["id"], mc = [
	"x1",
	"x2",
	"y1",
	"y2"
], hc = ["x"], gc = ["x"], _c = ["x"], vc = ["x"], yc = [
	"x",
	"y",
	"width",
	"height"
], bc = { class: "savings-chart-table" }, xc = { class: "savings-table-scroll" }, Sc = { class: "savings-table" }, Cc = {
	key: 1,
	class: "savings-empty"
}, wc = { class: "savings-card savings-explanation" }, Tc = {
	key: 2,
	class: "savings-card savings-status",
	role: "status"
}, Ec = /*#__PURE__*/ Do(/* @__PURE__ */ Bn({
	__name: "SavingsView",
	props: {
		hass: { type: Object },
		entryId: { type: String }
	},
	setup(e) {
		let t = e, n = kn(ro), r = Vn(), i = $(() => n?.language.value === "de"), a = $(() => i.value ? {
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
		}), o = $(() => n?.entity("binary_sensor", "economics_investment_configured")), s = $(() => n?.entity("sensor", "economics_amortization_progress")), c = $(() => n?.entity("sensor", "economics_remaining_to_payback")), l = $(() => n?.entity("sensor", "economics_roi")), u = $(() => n?.entity("sensor", "economics_net_savings")), d = $(() => n?.entity("sensor", "economics_status")), f = $(() => n?.entity("sensor", "economics_current_import_price")), p = $(() => s.value?.available ? bs(s.value.state?.state) : null), m = $(() => p.value === null ? null : Math.max(0, Math.min(100, p.value))), h = (e) => {
			let n = Ss(e, t.hass);
			return n === null ? a.value.unavailable : `${n} €`;
		}, g = (e) => {
			let n = Ss(e, t.hass, 4);
			return n === null ? a.value.unavailable : `${n} EUR/kWh`;
		}, _ = (e) => Cs(e, t.hass) ?? a.value.unavailable, v = (e) => Cs(`${e}T12:00:00Z`, t.hass, {
			dateStyle: "medium",
			timeZone: "UTC"
		}) ?? e, y = $(() => {
			let e = d.value?.available ? d.value.state?.state : void 0;
			return e === "active" ? null : e === "disabled" || e === "price_unavailable" || e === "origin_unavailable" || e === "partial_price_coverage" || e === "storage_error" ? a.value[e] : a.value.missing;
		}), b = $(() => f.value?.state?.attributes ?? {}), x = $(() => b.value.tariff_type === "time_of_use"), S = $(() => Array.isArray(b.value.windows) ? b.value.windows.filter((e) => !!e && typeof e == "object" && typeof e.start == "string" && typeof e.end == "string") : []), C = $(() => b.value.unavailable_reason), w = $(() => f.value?.available && bs(f.value.state?.state) !== null && C.value == null), T = $(() => {
			let e = b.value.active_window;
			return e && typeof e == "object" ? e : null;
		}), ee = (e) => w.value && bs(e.price_eur_kwh) !== null && T.value?.start === e.start && T.value?.end === e.end, E = $(() => w.value && T.value === null && bs(b.value.base_price_eur_kwh) !== null), D = (e) => Cs(`2000-01-01T${e.length === 5 ? `${e}:00` : e}Z`, t.hass, {
			timeStyle: "short",
			timeZone: "UTC"
		}) ?? e.slice(0, 5), O = Es(() => t.hass, () => t.entryId, () => u.value?.metadata.entity_id), k = /* @__PURE__ */ B(""), A = /* @__PURE__ */ B(""), te = null;
		Mn(O.data, (e) => {
			e && ((!k.value && !A.value || k.value === te?.start && A.value === te?.end) && (k.value = e.selected.start_date, A.value = e.selected.end_date), te = {
				start: e.selected.start_date,
				end: e.selected.end_date
			});
		}), Mn(() => t.entryId, () => {
			k.value = "", A.value = "", te = null;
		});
		let j = $(() => O.error.value === "invalid" ? a.value.invalid : O.error.value === "failed" ? a.value.failed : O.error.value === "unavailable" || O.data.value?.status === "recorder_unavailable" ? a.value.noRecorder : null), ne = [
			"day",
			"week",
			"month",
			"year"
		], re = $(() => O.data.value?.selected.buckets ?? []), ie = /* @__PURE__ */ B(null), ae = /* @__PURE__ */ B(720);
		Mn(ie, (e, t, n) => {
			if (!e) return;
			let r = (e) => {
				Number.isFinite(e) && e > 0 && (ae.value = e);
			};
			if (r(e.getBoundingClientRect().width), typeof ResizeObserver > "u") return;
			let i = new ResizeObserver((e) => {
				for (let t of e) r(t.contentRect.width);
			});
			i.observe(e), n(() => i.disconnect());
		});
		let M = $(() => {
			let e = re.value.map((e) => bs(e.change)), n = Math.max(0, ...e.map((e) => e ?? 0)), r = Math.min(0, ...e.map((e) => e ?? 0)), i = n - r || 1, a = (e) => 20 + (n - e) / i * 180, o = O.data.value?.selected, s = Date.parse(o?.start ?? ""), c = Date.parse(o?.end ?? ""), l = c - s, u = Ss(n, t.hass) ?? "", d = Ss(r, t.hass) ?? "", f = Math.max(56, Math.max(u.length, d.length) * 7.1 + 12), p = ae.value - 24, m = Math.max(1, p - f), h = (e) => f + Math.max(0, Math.min(1, (Date.parse(e) - s) / l)) * m;
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
				bars: re.value.map((t, n) => {
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
		}), oe = $(() => re.value.some((e) => bs(e.change) !== null)), ce = (e) => Cs(e, t.hass, O.data.value?.selected.period === "hour" ? { timeStyle: "short" } : O.data.value?.selected.period === "month" ? {
			month: "short",
			year: "numeric"
		} : {
			day: "2-digit",
			month: "short"
		}) ?? e;
		return (t, i) => (q(), J("div", Ds, [
			X("div", Os, [o.value?.available && o.value.state?.state === "off" ? (q(), J("section", {
				key: 0,
				class: "savings-card savings-payback",
				"aria-labelledby": `${V(r)}-investment`
			}, [X("h2", { id: `${V(r)}-investment` }, P(a.value.payback), 9, As), X("p", null, P(a.value.investment), 1)], 8, ks)) : o.value?.available && o.value.state?.state === "on" && (s.value || c.value || l.value || u.value || d.value) ? (q(), J("section", {
				key: 1,
				class: "savings-card savings-payback",
				"aria-labelledby": `${V(r)}-payback`
			}, [
				X("h2", { id: `${V(r)}-payback` }, P(a.value.payback), 9, Ms),
				s.value ? (q(), J("div", Ns, [
					X("h3", { id: `${V(r)}-progress` }, P(s.value.name), 9, Ps),
					X("p", Fs, P(p.value === null ? a.value.unavailable : `${V(Ss)(p.value, e.hass)} %`), 1),
					X("div", {
						class: "savings-progress__track",
						role: m.value === null ? void 0 : "meter",
						"aria-labelledby": `${V(r)}-progress`,
						"aria-valuemin": m.value === null ? void 0 : 0,
						"aria-valuemax": m.value === null ? void 0 : 100,
						"aria-valuenow": m.value ?? void 0
					}, [m.value === null ? Z("", !0) : (q(), J("span", {
						key: 0,
						style: se({ width: `${m.value}%` })
					}, null, 4))], 8, Is)
				])) : Z("", !0),
				c.value || l.value || u.value || d.value ? (q(), J("dl", Ls, [
					c.value ? (q(), J("div", Rs, [X("dt", null, P(c.value.name), 1), X("dd", null, P(h(c.value.available ? c.value.state?.state : null)), 1)])) : Z("", !0),
					l.value ? (q(), J("div", zs, [X("dt", null, P(a.value.prior), 1), X("dd", null, P(h(l.value.available ? l.value.state?.attributes.prior_result_eur ?? l.value.state?.attributes.prior_result_eur_formatted : null)), 1)])) : Z("", !0),
					u.value ? (q(), J("div", Bs, [X("dt", null, P(a.value.net), 1), X("dd", null, P(h(u.value.available ? u.value.state?.state : null)), 1)])) : Z("", !0),
					d.value ? (q(), J("div", Vs, [X("dt", null, P(a.value.started), 1), X("dd", null, P(_(d.value.available ? d.value.state?.attributes.economics_started_at : null)), 1)])) : Z("", !0)
				])) : Z("", !0)
			], 8, js)) : Z("", !0), u.value ? (q(), J("section", {
				key: 2,
				class: "savings-periods",
				"aria-label": a.value.periods
			}, [(q(), J(G, null, U(ne, (e) => X("article", {
				key: e,
				class: "savings-card"
			}, [X("h2", null, P(a.value[e]), 1), X("p", Us, P(V(O).loading.value ? "…" : h(V(O).data.value?.periods[e].change)), 1)])), 64))], 8, Hs)) : Z("", !0)]),
			x.value ? (q(), J("section", {
				key: 0,
				class: "savings-card savings-tariff",
				"aria-labelledby": `${V(r)}-tariff`
			}, [
				X("h2", { id: `${V(r)}-tariff` }, P(a.value.tariff), 9, Gs),
				X("div", Ks, [X("table", qs, [X("thead", null, [X("tr", null, [
					i[4] ||= X("th", { "aria-label": "Status" }, null, -1),
					X("th", null, P(a.value.from), 1),
					X("th", null, P(a.value.to), 1),
					X("th", null, P(a.value.price), 1)
				])]), X("tbody", null, [(q(!0), J(G, null, U(S.value, (e, t) => (q(), J("tr", {
					key: t,
					class: N({ "savings-current": ee(e) })
				}, [
					X("td", null, P(ee(e) ? a.value.now : ""), 1),
					X("td", null, P(D(e.start)), 1),
					X("td", null, P(D(e.end)), 1),
					X("td", null, P(g(e.price_eur_kwh)), 1)
				], 2))), 128)), X("tr", { class: N({ "savings-current": E.value }) }, [
					X("td", null, P(E.value ? a.value.now : ""), 1),
					X("td", Js, P(a.value.base), 1),
					X("td", null, P(g(b.value.base_price_eur_kwh)), 1)
				], 2)])])]),
				X("p", null, [X("strong", null, P(a.value.feed) + ":", 1), ui(" " + P(g(b.value.feed_in_price_eur_kwh)), 1)]),
				w.value ? b.value.next_price_change_at ? (q(), J("p", Zs, [X("strong", null, P(a.value.next) + ":", 1), ui(" " + P(_(b.value.next_price_change_at)), 1)])) : Z("", !0) : (q(), J("p", Ys, [ui(P(a.value.noPrice), 1), typeof C.value == "string" && C.value ? (q(), J("span", Xs, " (" + P(C.value) + ")", 1)) : Z("", !0)]))
			], 8, Ws)) : Z("", !0),
			u.value ? (q(), J("section", {
				key: 1,
				class: "savings-card savings-range",
				"aria-labelledby": `${V(r)}-range`
			}, [
				X("h2", { id: `${V(r)}-range` }, P(a.value.range), 9, $s),
				X("form", {
					class: "savings-dates",
					onSubmit: i[3] ||= Ga((e) => V(O).select(k.value, A.value), ["prevent"])
				}, [
					X("label", { for: `${V(r)}-from` }, [ui(P(a.value.from), 1), En(X("input", {
						id: `${V(r)}-from`,
						"onUpdate:modelValue": i[0] ||= (e) => k.value = e,
						type: "date",
						required: "",
						max: A.value || void 0
					}, null, 8, tc), [[ja, k.value]])], 8, ec),
					X("label", { for: `${V(r)}-to` }, [ui(P(a.value.to), 1), En(X("input", {
						id: `${V(r)}-to`,
						"onUpdate:modelValue": i[1] ||= (e) => A.value = e,
						type: "date",
						required: "",
						min: k.value || void 0
					}, null, 8, rc), [[ja, A.value]])], 8, nc),
					X("button", ic, P(a.value.apply), 1),
					X("button", {
						type: "button",
						disabled: V(O).loading.value,
						onClick: i[2] ||= (...e) => V(O).refresh && V(O).refresh(...e)
					}, P(a.value.refresh), 9, ac)
				], 32),
				V(O).loading.value ? (q(), J("p", oc, P(a.value.loading), 1)) : j.value ? (q(), J("p", sc, P(j.value), 1)) : V(O).data.value ? (q(), J(G, { key: 2 }, [
					X("p", cc, P(v(V(O).data.value.selected.start_date)) + " – " + P(v(V(O).data.value.selected.end_date)), 1),
					X("h3", null, P(a.value.selected), 1),
					X("p", lc, P(h(V(O).data.value.selected.change)), 1),
					X("h3", { id: `${V(r)}-chart` }, P(a.value.chart), 9, uc),
					X("p", dc, P(a.value.chartHint), 1),
					oe.value ? (q(), J(G, { key: 0 }, [(q(), J("svg", {
						ref_key: "chartElement",
						ref: ie,
						class: "savings-chart",
						viewBox: `0 0 ${ae.value} 240`,
						role: "img",
						"aria-labelledby": `${V(r)}-chart`,
						"aria-describedby": `${V(r)}-chart-description`
					}, [
						X("desc", { id: `${V(r)}-chart-description` }, P(a.value.net) + ": " + P(h(V(O).data.value.selected.change)) + ". " + P(a.value.table) + ". ", 9, pc),
						X("line", {
							x1: M.value.left - 2,
							x2: M.value.right + 2,
							y1: M.value.zero,
							y2: M.value.zero,
							class: "savings-chart__axis"
						}, null, 8, mc),
						X("text", {
							x: M.value.left - 8,
							y: "24",
							"text-anchor": "end"
						}, P(M.value.highLabel), 9, hc),
						X("text", {
							x: M.value.left - 8,
							y: "204",
							"text-anchor": "end"
						}, P(M.value.lowLabel), 9, gc),
						i[5] ||= X("text", {
							x: "10",
							y: "226"
						}, "EUR", -1),
						re.value.length ? (q(), J("text", {
							key: 0,
							x: M.value.left,
							y: "226"
						}, P(ce(M.value.start)), 9, _c)) : Z("", !0),
						re.value.length > 1 ? (q(), J("text", {
							key: 1,
							x: M.value.right,
							y: "226",
							"text-anchor": "end"
						}, P(ce(M.value.end)), 9, vc)) : Z("", !0),
						(q(!0), J(G, null, U(M.value.bars, (e, t) => (q(), J("rect", {
							key: t,
							x: e.x,
							y: e.y,
							width: e.width,
							height: e.height,
							class: N(["savings-chart__bar", { "savings-chart__bar--negative": (e.value ?? 0) < 0 }])
						}, [X("title", null, P(e.label) + ": " + P(h(e.value)), 1)], 10, yc))), 128))
					], 8, fc)), X("details", bc, [X("summary", null, P(a.value.table), 1), X("div", xc, [X("table", Sc, [X("thead", null, [X("tr", null, [
						X("th", null, P(a.value.from), 1),
						X("th", null, P(a.value.to), 1),
						X("th", null, P(a.value.net), 1)
					])]), X("tbody", null, [(q(!0), J(G, null, U(M.value.bars, (e, t) => (q(), J("tr", { key: t }, [
						X("td", null, P(e.label), 1),
						X("td", null, P(_(e.end)), 1),
						X("td", null, P(h(e.value)), 1)
					]))), 128))])])])])], 64)) : Z("", !0),
					!oe.value || V(O).data.value.selected.change === null ? (q(), J("p", Cc, P(V(O).data.value.selected.change === null ? a.value.noData : a.value.noChartData), 1)) : Z("", !0)
				], 64)) : Z("", !0)
			], 8, Qs)) : Z("", !0),
			X("details", wc, [
				X("summary", null, P(a.value.explain), 1),
				X("p", null, P(a.value.netHint), 1),
				X("p", null, P(a.value.calendarHint), 1),
				X("p", null, P(a.value.rangeHint), 1)
			]),
			y.value && V(n)?.ready.value ? (q(), J("p", Tc, P(y.value), 1)) : Z("", !0)
		]));
	}
}), [["styles", [".savings-view{gap:20px;min-width:0;margin-top:24px;display:grid}.savings-overview{display:contents}.savings-card{border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));min-width:0;box-shadow:var(--ha-card-box-shadow,none);color:var(--primary-text-color,#212121);padding:24px}.savings-card h2{margin:0 0 20px;font-size:18px;font-weight:500;line-height:1.5}.savings-card h3{margin:20px 0 8px;font-size:16px;font-weight:500}.savings-card p{overflow-wrap:anywhere;line-height:1.6}.savings-card p:last-child{margin-bottom:0}.savings-large{font-variant-numeric:tabular-nums;margin:0 0 12px;font-size:28px;font-weight:500}.savings-progress__track{background:var(--divider-color,#e0e0e0);border-radius:8px;height:16px;overflow:hidden}.savings-progress__track span{background:var(--info-color,#039be5);height:100%;display:block}.savings-rows{margin:20px 0 0}.savings-rows>div{border-bottom:1px solid var(--divider-color,#e0e0e0);justify-content:space-between;gap:16px;padding:12px 0;line-height:1.5;display:flex}.savings-rows>div:last-child{border-bottom:0;padding-bottom:0}.savings-rows dd{text-align:right;font-variant-numeric:tabular-nums;margin:0}.savings-periods{grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:16px;display:grid}.savings-periods h2{font-size:16px}.savings-table-scroll{overflow-x:auto}.savings-table{border-collapse:collapse;font-variant-numeric:tabular-nums;width:100%;line-height:1.5}.savings-table th,.savings-table td{text-align:left;border-bottom:1px solid var(--divider-color,#e0e0e0);padding:10px 8px}.savings-table th:last-child,.savings-table td:last-child{text-align:right}.savings-current{background:var(--secondary-background-color,color-mix(in srgb, currentColor 8%, transparent));font-weight:600}.savings-dates{flex-wrap:wrap;align-items:end;gap:16px;display:flex}.savings-dates label{flex:180px;gap:8px;min-width:0;display:grid}.savings-dates input,.savings-dates button{box-sizing:border-box;font:inherit;border:1px solid var(--divider-color,#bdbdbd);background:var(--ha-card-background,var(--card-background-color,#fff));min-height:44px;color:var(--primary-text-color,#212121);border-radius:6px;padding:10px 12px}.savings-dates input{--lightningcss-light:initial;--lightningcss-dark: ;color-scheme:light dark;width:100%}@media (prefers-color-scheme:dark){.savings-dates input{--lightningcss-light: ;--lightningcss-dark:initial}}.savings-dates button{cursor:pointer;color:var(--primary-color,#0288d1)}.savings-dates button:disabled{opacity:.6;cursor:default}.savings-dates :focus-visible,.savings-card summary:focus-visible{outline:2px solid var(--primary-color,#03a9f4);outline-offset:3px}.savings-selected-dates,.savings-empty{color:var(--secondary-text-color,#666)}.savings-chart{width:100%;height:auto;display:block;overflow:visible}.savings-chart text{fill:var(--secondary-text-color,#666);font-size:12px}.savings-chart__axis{stroke:var(--primary-text-color,#212121);stroke-width:1px}.savings-chart__bar{fill:var(--info-color,#039be5)}.savings-chart__bar--negative{fill:var(--error-color,#db4437)}.savings-card summary{cursor:pointer;min-height:24px;font-weight:500;line-height:1.6}.savings-chart-table{margin-top:16px}.savings-status{margin:0;line-height:1.6}@container sax-content (width>=860px){.savings-view{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;gap:16px;margin-top:16px}.savings-view>*{grid-column:1/-1}.savings-overview{gap:16px;min-width:0;display:grid}.savings-overview:empty{display:none}.savings-view:has(>.savings-overview>section):has(>.savings-tariff)>:is(.savings-overview,.savings-tariff){grid-column:auto}.savings-card{padding:18px}.savings-card h2{margin-bottom:12px;font-size:16px}.savings-card h3{margin-top:16px;font-size:14px}.savings-card p{margin-top:10px;line-height:1.5}.savings-progress h3{margin-top:0}.savings-card .savings-large{margin-top:0;margin-bottom:8px;font-size:24px}.savings-rows{margin-top:12px}.savings-rows>div{gap:12px;padding:8px 0}.savings-rows dt{min-width:0}.savings-rows dd{flex-shrink:0;max-width:58%}.savings-periods{grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.savings-view:has(>.savings-tariff) .savings-periods{grid-template-columns:repeat(2,minmax(0,1fr))}.savings-periods .savings-card{padding:14px 16px}.savings-periods h2{margin-bottom:6px;font-size:14px}.savings-periods .savings-large{margin-bottom:0;font-size:22px}.savings-table th,.savings-table td{padding:7px 8px}.savings-dates{gap:12px}.savings-dates label{flex:0 220px;gap:6px}.savings-range .savings-selected-dates{margin-bottom:8px}.savings-range .savings-chart-hint{margin-top:0;margin-bottom:8px}.savings-chart-table{margin-top:12px}}@media (max-width:600px){.savings-view{gap:16px}.savings-card{padding:20px}.savings-rows>div{flex-wrap:wrap;gap:4px 16px}.savings-rows dd{margin-left:auto}}"]]]), Dc = ["lang"], Oc = { class: "header" }, kc = ["aria-label"], Ac = ["aria-label"], jc = [
	"href",
	"aria-current",
	"onClick"
], Mc = {
	key: 0,
	class: "status",
	role: "alert"
}, Nc = { class: "introduction" }, Pc = {
	class: "section",
	"aria-labelledby": "section-heading"
}, Fc = {
	key: 0,
	class: "status",
	role: "status"
}, Ic = {
	key: 1,
	class: "status",
	role: "status"
}, Lc = {
	key: 7,
	class: "status"
}, Rc = ["href"], zc = /* @__PURE__ */ xa(/* @__PURE__ */ Do(/* @__PURE__ */ Bn({
	__name: "Panel.ce",
	props: {
		hass: { type: Object },
		narrow: { type: Boolean },
		panel: { type: Object },
		route: { type: Object }
	},
	setup(e) {
		let t = e, n = wa(), r = so(() => t.hass, () => t.panel?.config?.entry_id);
		On(ro, r);
		let i = $(() => t.hass?.language.toLowerCase().startsWith("de") ? "de" : "en"), a = $(() => to[i.value]), o = $(() => !t.hass?.kioskMode && (t.narrow || t.hass?.dockedSidebar === "always_hidden")), s = $(() => `/${t.panel?.url_path || "sax-power-vue"}`), c = /* @__PURE__ */ B(t.route?.path ?? window.location.pathname), l = $(() => eo(c.value, s.value)), u = $(() => $a.find((e) => e.path === l.value)), d = /* @__PURE__ */ B();
		Mn(() => t.route?.path, (e) => {
			e !== void 0 && (c.value = e);
		});
		function f() {
			c.value = window.location.pathname;
		}
		Zn(() => {
			window.addEventListener("popstate", f), window.addEventListener("location-changed", f);
		}), Qn(() => {
			window.removeEventListener("popstate", f), window.removeEventListener("location-changed", f);
		});
		function p(e, t) {
			e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || (e.preventDefault(), window.location.pathname !== t && (window.history.pushState(null, "", t), window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: !1 } }))), f(), pn(() => d.value?.focus()));
		}
		function m() {
			n?.dispatchEvent(new CustomEvent("hass-toggle-menu", {
				bubbles: !0,
				composed: !0
			}));
		}
		return (t, n) => (q(), J("div", {
			class: N(["dashboard", { narrow: e.narrow }]),
			lang: i.value
		}, [
			X("header", Oc, [o.value ? (q(), J("button", {
				key: 0,
				class: "menu-button",
				type: "button",
				"aria-label": a.value.menu,
				onClick: m
			}, [...n[1] ||= [X("svg", {
				viewBox: "0 0 24 24",
				"aria-hidden": "true"
			}, [X("path", { d: "M4 6h16M4 12h16M4 18h16" })], -1)]], 8, kc)) : Z("", !0), n[2] ||= X("div", { class: "brand" }, [X("svg", {
				class: "brand-icon",
				viewBox: "0 0 24 24",
				"aria-hidden": "true"
			}, [X("path", { d: "M9 3h6M8 5h8a1 1 0 0 1 1 1v14H7V6a1 1 0 0 1 1-1Z" }), X("path", { d: "m13 8-3 5h4l-3 5" })]), X("span", null, "SAX Power")], -1)]),
			X("nav", {
				class: "navigation",
				"aria-label": a.value.navigation
			}, [(q(!0), J(G, null, U(V($a), (e) => (q(), J("a", {
				key: e.path,
				href: `${s.value}/${e.path}`,
				"aria-current": l.value === e.path ? "page" : void 0,
				onClick: (t) => p(t, `${s.value}/${e.path}`)
			}, P(e[i.value]), 9, jc))), 128))], 8, Ac),
			X("main", null, [
				V(r).error.value ? (q(), J("p", Mc, P(V(r).error.value), 1)) : Z("", !0),
				X("p", Nc, P(a.value.introduction), 1),
				X("section", Pc, [X("h1", {
					id: "section-heading",
					ref_key: "heading",
					ref: d,
					tabindex: "-1"
				}, P(u.value?.[i.value] ?? a.value.notFound), 513), e.hass ? e.panel?.config?.entry_id ? l.value === "allgemein" ? (q(), Y(Jo, { key: 2 })) : l.value === "ladeautomatik" ? (q(), Y(_s, { key: 3 })) : l.value === "netzdienliches-laden" ? (q(), Y(vs, { key: 4 })) : l.value === "dynamisches-laden" ? (q(), Y(ys, { key: 5 })) : l.value === "ersparnis" ? (q(), Y(Ec, {
					key: 6,
					hass: e.hass,
					"entry-id": e.panel?.config?.entry_id
				}, null, 8, ["hass", "entry-id"])) : (q(), J("div", Lc, [X("p", null, P(a.value.notFoundDescription), 1), X("a", {
					href: `${s.value}/allgemein`,
					onClick: n[0] ||= (e) => p(e, `${s.value}/allgemein`)
				}, P(a.value.returnToOverview), 9, Rc)])) : (q(), J("p", Ic, P(a.value.missingEntry), 1)) : (q(), J("p", Fc, P(a.value.loading), 1))])
			])
		], 10, Dc));
	}
}), [["styles", [":host{height:100%;color:var(--primary-text-color,#212121);background:var(--primary-background-color,#fafafa);font-family:var(--paper-font-body1_-_font-family,Roboto, sans-serif);font-size:14px;display:block}*{box-sizing:border-box}.dashboard{min-height:100%;container:sax-panel/inline-size}.header{background:var(--app-header-background-color,var(--primary-color,#03a9f4));min-height:64px;color:var(--app-header-text-color,#fff);align-items:center;gap:14px;padding:8px 24px;display:flex}.brand{align-items:center;gap:10px;font-size:20px;font-weight:500;display:flex}.header svg{fill:none;stroke:currentColor;stroke-width:1.7px;stroke-linecap:round;stroke-linejoin:round}.brand-icon{width:30px;height:30px}.menu-button{width:44px;height:44px;color:inherit;cursor:pointer;background:0 0;border:0;border-radius:50%;place-items:center;margin-left:-10px;display:grid}.menu-button svg{width:24px;height:24px}.navigation{border-bottom:1px solid var(--divider-color,#e0e0e0);background:var(--card-background-color,#fff);padding:0 16px;display:flex;overflow-x:auto}.navigation a{min-height:56px;color:var(--secondary-text-color,#666);white-space:nowrap;border-bottom:3px solid #0000;align-items:center;padding:12px 16px;text-decoration:none;display:flex}.navigation a[aria-current=page]{border-color:var(--primary-color,#03a9f4);color:var(--primary-text-color,#212121);font-weight:600}a{color:var(--primary-text-color,#212121);text-underline-offset:3px}a:focus-visible,button:focus-visible{outline-offset:-4px;outline:2px solid}main{max-width:1120px;margin:0 auto;padding:28px 24px 48px}.introduction{color:var(--secondary-text-color,#666);margin:0 0 24px;line-height:1.6}.section{overflow-wrap:anywhere;border:var(--ha-card-border-width,1px) solid var(--ha-card-border-color,var(--divider-color,#e0e0e0));border-radius:var(--ha-card-border-radius,12px);background:var(--ha-card-background,var(--card-background-color,#fff));box-shadow:var(--ha-card-box-shadow,none);padding:28px;container:sax-content/inline-size}h1{margin:0;font-size:24px;font-weight:500;line-height:1.35}h1:focus{outline:none}h2{margin:0 0 12px;font-size:18px;font-weight:500;line-height:1.5}.status{margin-top:24px;line-height:1.7}.narrow .header{padding-left:16px;padding-right:16px}.narrow main{padding:16px 12px 32px}@container sax-panel (width>=940px){.header{min-height:56px;padding:6px 20px}.navigation a{min-height:48px;padding:8px 14px}main{max-width:1360px;padding:16px 20px 20px}.introduction{margin-bottom:12px}.section{padding:20px}h1{font-size:22px}}@media (max-width:600px){.header{gap:8px;padding:8px 16px}.brand{gap:6px;font-size:18px}.brand-icon{display:none}.navigation{padding:0 4px}main{padding:16px 12px 32px}.introduction{margin-bottom:16px}.section{padding:20px}h1{font-size:22px}}"]]]));
customElements.get("sax-power-vue-panel") || customElements.define("sax-power-vue-panel", zc);
//#endregion
export { zc as SaxPowerVuePanel };
