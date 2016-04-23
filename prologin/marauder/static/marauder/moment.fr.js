moment.locale('fr', {
  months: "janvier_février_mars_avril_mai_juin_juillet_août_septembre_octobre_novembre_décembre".split("_"),
  monthsShort: "janv._févr._mars_avr._mai_juin_juil._août_sept._oct._nov._déc.".split("_"),
  weekdays: "dimanche_lundi_mardi_mercredi_jeudi_vendredi_samedi".split("_"),
  weekdaysShort: "dim._lun._mar._mer._jeu._ven._sam.".split("_"),
  weekdaysMin: "Di_Lu_Ma_Me_Je_Ve_Sa".split("_"),
  longDateFormat: {
    LT: "HH:mm",
    LTS: "HH:mm:ss",
    L: "DD/MM/YYYY",
    LL: "D MMMM YYYY",
    LLL: "D MMMM YYYY LT",
    LLLL: "dddd D MMMM YYYY LT"
  },
  calendar: {
    sameDay: "[Aujourd'hui à] LT",
    nextDay: '[Demain à] LT',
    nextWeek: 'dddd [à] LT',
    lastDay: '[Hier à] LT',
    lastWeek: 'dddd [dernier à] LT',
    sameElse: 'L'
  },
  relativeTime: {
    future: "dans %s",
    past: "%s",
    s: "à l'instant",
    m: "il y a une minute",
    mm: "il y a %d minutes",
    h: "il y a une heure",
    hh: "il y a %d heures",
    d: "il y a un jour",
    dd: "il y a %d jours",
    M: "il y a un mois",
    MM: "il y a %d mois",
    y: "il y a une année",
    yy: "il y a %d années"
  },
  ordinalParse: /\d{1,2}(er|ème)/,
  ordinal: function (number) {
    return number + (number === 1 ? 'er' : 'ème');
  },
  meridiemParse: /PD|MD/,
  isPM: function (input) {
    return input.charAt(0) === 'M';
  },
  // in case the meridiem units are not separated around 12, then implement
  // this function (look at locale/id.js for an example)
  // meridiemHour : function (hour, meridiem) {
  //     return /* 0-23 hour, given meridiem token and hour 1-12 */
  // },
  meridiem: function (hours, minutes, isLower) {
    return hours < 12 ? 'PD' : 'MD';
  },
  week: {
    dow: 1, // Monday is the first day of the week.
    doy: 4  // The week that contains Jan 4th is the first week of the year.
  }
});