const API_ROOT = "/marauder/api";
const appElement = document.querySelector('[ng-app=app]');

// Native interface (webview to app)
var nativeMock = function () {
  console.warn("Would call native function");
  setTimeout(Client.actionSuccess, 100);
};
var native = window.Native || {
    callPhoneNumber: nativeMock,
    startupCompleted: nativeMock,
  };

// Client interface (app to webview)
var Client = window.Client = {
  actionSuccess: function () {
    var $scope = angular.element(appElement).scope();
    $scope.$apply(function () {
      $scope.actionLoading = false;
    });
  }
};

angular.module('app', ['ionic', 'angularMoment'])
  .factory('webServices', ['$http', function ($http) {
    return {
      getTaskForces: function () {
        return $http.get(API_ROOT + '/taskforces/').then(function (response) {
          return response.data;
        });
      },
      sendUserPing: function (uid, reason) {
        return $http.post(API_ROOT + '/ping/user/', {id: uid, reason: reason}).then(function (response) {
          return response.data;
        });
      },
      sendTaskForcePing: function (tfid, reason) {
        return $http.post(API_ROOT + '/ping/taskforce/', {id: tfid, reason: reason}).then(function (response) {
          return response.data;
        });
      }
    }
  }])
  .directive('lastSeen', function () {
    return {
      restrict: 'E',
      replace: true,
      scope: {
        timestamp: "@"
      },
      template: '<span><em ng-if="!timestamp">Jamais vu</em>' +
      '<span ng-if="timestamp">Vu <span am-time-ago="timestamp | amFromUnix | amUtc"></span></span></span>'
    };
  })
  // TODO: directive for abstracting "loading" buttons
  .controller('MainCtrl', function (webServices, $rootScope, $scope, $timeout, $ionicPopover, $ionicPopup, $ionicModal) {

    $rootScope.actionLoading = false;
    $scope.ping = {to: null, reason: ''};

    function updateTaskForces(cb) {
      webServices.getTaskForces().then(function (response) {
        $scope.taskForces = response;
        if (cb) cb.call(this, response);
      });
    }

    $ionicPopover.fromTemplateUrl('templates/popover.html', {
      scope: $scope,
    }).then(function (popover) {
      $scope.popover = popover;
    });

    $ionicModal.fromTemplateUrl('templates/ping.html', {
      scope: $scope,
      animation: 'slide-in-up'
    }).then(function (modal) {
      $scope.pingModal = modal;
    });

    $scope.toggleAccordion = function (member) {
      if ($scope.isAccordionShown(member)) {
        $scope.shownAccordion = null;
      } else {
        $scope.shownAccordion = member;
      }
    };
    $scope.isAccordionShown = function (member) {
      return $scope.shownAccordion === member;
    };

    $scope.doRefresh = function () {
      // the hard way
      // window.location.reload();
      updateTaskForces(function () {
        $scope.$broadcast('scroll.refreshComplete');
      });
    };

    $scope.promptTaskForcePing = function (taskforce) {
      $scope.ping.to = "l'ensemble du groupe " + taskforce.name;
      $scope.ping.send = [webServices.sendTaskForcePing, taskforce.id];
      $scope.pingModal.show();
    };

    $scope.promptUserPing = function (member) {
      $scope.ping.to = member.fullName;
      $scope.ping.send = [webServices.sendUserPing, member.id];
      $scope.pingModal.show();
    };

    $scope.sendPing = function () {
      var reason = $scope.ping.reason.trim();
      if (!reason)
        return;
      $scope.ping.reason = '';
      $rootScope.actionLoading = true;
      $scope.pingModal.hide();
      $scope.ping.send[0].call(null, $scope.ping.send[1], reason).then(function () {
        $rootScope.actionLoading = false;
      }, function (err) {
        $ionicPopup.alert({
          title: "Erreur",
          template: "Impossible d'envoyer le ping."
        });
        $rootScope.actionLoading = false;
      });

    };

    $scope.callNumber = function (number) {
      $rootScope.actionLoading = true;
      native.callPhoneNumber(number);
    };

    $scope.reloadApp = function () {
      $scope.popover.hide();
      window.location.reload();
    };

    native.startupCompleted();
    updateTaskForces();

  });

// Map
/*
 var lineStyle = new ol.style.Style({
 stroke: new ol.style.Stroke({
 color: '#fafafa',
 width: 1
 })
 });

 var vectorSource = new ol.source.Vector({
 url: '/static/marauder/epita.geo.json',
 format: new ol.format.GeoJSON()
 });

 var view = new ol.View({
 center: ol.proj.fromLonLat([2.3631487758069007, 48.815166921320895]),
 minZoom: 18,
 maxZoom: 22,
 zoom: 18
 });

 var map = new ol.Map({
 layers: [
 new ol.layer.Vector({
 source: vectorSource,
 style: lineStyle
 })
 ],
 target: 'map',
 renderer: 'canvas',
 view: view
 });
 */
