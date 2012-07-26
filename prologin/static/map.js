    //<![CDATA[
    var map;
    var mc;
    var markers = [];
    var infoWindow;
    var locationSelect;
    var ville = "";
    var biens;
    
    function load() {
      map = new google.maps.Map(document.getElementById("map"), {
        center: new google.maps.LatLng(48, 2),
        zoom: 5,
        mapTypeId: 'roadmap',
        mapTypeControlOptions: {style: google.maps.MapTypeControlStyle.DROPDOWN_MENU}
      });
      infoWindow = new google.maps.InfoWindow();
      villeSelect = document.getElementById("ville");
      villeSelect.onchange = function() {
      	ville = villeSelect.options[villeSelect.selectedIndex].value;
        updateLocations();
      }
      locationSelect = document.getElementById("locationSelect");
      updateLocations();
    }

   function searchLocations() {
     var address = "Paris";
     var geocoder = new google.maps.Geocoder();
     geocoder.geocode({address: address}, function(results, status) {
       if (status == google.maps.GeocoderStatus.OK) {
         searchLocationsNear(results[0].geometry.location);
       } else {
         alert(address + ' not found');
       }
     });
   }

   function trier() {
   	 biens = "";
   	 cases = document.getElementById("f").biens;
   	 for(i = 0 ; i < cases.length ; i++)
       if(cases[i].checked)
         biens += cases[i].value + ","
     updateLocations();
   }

   function clearLocations() {
     infoWindow.close();
     for (var i = 0; i < markers.length; i++) {
       markers[i].setMap(null);
     }
     markers.length = 0;

     locationSelect.innerHTML = "";
     var option = document.createElement("option");
     option.value = "none";
     option.innerHTML = "Voir les marqueurs";
     locationSelect.appendChild(option);
   }

   function updateLocations() {
     clearLocations();
     var searchUrl = '/centers/json/' + ville;
     downloadUrl(searchUrl, function(data) {
     json = JSON.parse(data);
       var bounds = new google.maps.LatLngBounds();
       for (var i = 0; i < json.length; i++) {
         var id = json[i].id;
         var name = json[i].name;
         var address = json[i].address;
         var phone_number = json[i].phone_number;
         var comments = json[i].comments;
         var latlng = new google.maps.LatLng(
              parseFloat(json[i].lat),
              parseFloat(json[i].lng));
         createOption(name, i);
         createMarker(latlng, id, name, address, phone_number, comments);
         bounds.extend(latlng);
       }
       if(json.length == 0) {
         alert("Désolé, aucun bien n'a été trouvé.");
         var darwin = new google.maps.LatLng(48, 2);
         map.setCenter(darwin);
         map.setZoom(5);
       } else
         map.fitBounds(bounds);
       locationSelect.style.visibility = "visible";
       locationSelect.onchange = function() {
         var markerNum = locationSelect.options[locationSelect.selectedIndex].value;
         google.maps.event.trigger(markers[markerNum], 'click');
       };
      });
    }
  
    function createMarker(latlng, id, name, address, phone_number, comments) {
      while(match = /(.*) <(.*)>/.exec(comments)) {
      	comments = comments.replace(match[1] + " <" + match[2] + ">", "<a href=\"mailto:" + match[2] + "\">" + match[1] + "</a>");
      }
      var html = "<b>" + name + "</b> <br />" + address + "<br />";
      for(i = 0 ; i < phone_number.length ; i++)
      	html += phone_number[i] + ((i % 2 == 1) ? " " : "");
      html += "<br />" + comments.replace(/\n/g, '<br />');
      var marker = new google.maps.Marker({
        map: map,
        position: latlng
      });
      google.maps.event.addListener(marker, 'click', function() {
        infoWindow.setContent(html);
        infoWindow.open(map, marker);
      });
      markers.push(marker);
    }

    function createOption(name, num) {
      var option = document.createElement("option");
      option.value = num;
      option.innerHTML = name;
      locationSelect.appendChild(option);
    }

    function downloadUrl(url, callback) {
      var request = window.ActiveXObject ?
          new ActiveXObject('Microsoft.XMLHTTP') :
          new XMLHttpRequest;

      request.onreadystatechange = function() {
        if (request.readyState == 4) {
          request.onreadystatechange = doNothing;
          callback(request.responseText, request.status);
        }
      };

      request.open('GET', url, true);
      request.send(null);
    }

    function doNothing() {}

    //]]>