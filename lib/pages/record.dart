import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:camera/camera.dart';
import 'package:camera_web/camera_web.dart';
import 'package:convert_native_img_stream/convert_native_img_stream.dart';
import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gal/gal.dart';
import 'package:image/image.dart' as imglib;
import 'package:image/image.dart';
import 'package:path_provider/path_provider.dart';
import 'package:web_socket_channel/web_socket_channel.dart';


import '../utils/functions.dart';
import '../utils/providers.dart';
import '../utils/variables.dart';

class RecordPage extends ConsumerStatefulWidget {
  const RecordPage({super.key});

  @override
  ConsumerState<RecordPage> createState() => _RecordPageState();
}



class _RecordPageState extends ConsumerState<RecordPage> with WidgetsBindingObserver {
  final convertNative = ConvertNativeImgStream();
  List<CameraDescription> cameras = [];
  CameraController? cameraController;
  late Timer videoFeedTimer;
  bool isStreaming = false;
  final videoChannel = WebSocketChannel.connect(
    Uri.parse('ws://10.217.23.251:8765'),
  );

  // final videoChannel = IOWebSocketChannel.connect('ws://10.217.23.251:8765');


  void checkConnection() {
    try {
      // videoChannel.sink.add('ping'); // Try sending a ping message
      print('WebSocket is connected.');
    } catch (e) {
      print('WebSocket is not connected: $e');
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    if (cameraController == null || cameraController?.value.isInitialized == false) return;
    if (state == AppLifecycleState.inactive) {
      cameraController?.dispose();
    } else if (state  == AppLifecycleState.resumed) {
      _setupCameraController();
    }
  }

  @override
  void initState() {
    super.initState();
    _setupCameraController();

    // videoFeedTimer = Timer.periodic(Duration(milliseconds: 42 /*Approx 24 fps*/), (timer) async {
    //   print("kuan is gay");
    //   XFile picture = await cameraController!.takePicture();
    //   Gal.putImage(
    //       picture.path
    //   );
    // });
  }


  @override
  void dispose() {
    super.dispose();
    // videoFeedTimer.cancel();
    // cameraController?.stopImageStream();
    // print("stream stopped");
    cameraController?.dispose();
  }

  void encodeToJpegFunction(imglib.Image bitmap) {
    // List<int> jpegBytes = imglib.encodeJpg(bitmap);
    // String base64String = base64Encode(jpegBytes);
  }

  Future<void> _setupCameraController() async {
    List<CameraDescription> _cameras = await availableCameras();
    if (_cameras.isNotEmpty) {
      setState(() {
        cameras = _cameras;
        final selectedCamera = cameras.first; //.firstWhere((camera) => camera.lensDirection == CameraLensDirection.front);
        print(_cameras);
        cameraController = CameraController(selectedCamera, ResolutionPreset.low, enableAudio: false, videoBitrate: 20);
      });
      cameraController?.initialize().then((_) {
        setState(() {
          videoChannel.sink.add(jsonEncode(ref.read(ChosenSongGenresProvider).toList()));
        });
      });
    }
  }

  int counter = 0;


  @override
  Widget build(BuildContext context) {
    print("start");
    print(DateTime.now().millisecondsSinceEpoch);
    if (cameraController == null || cameraController?.value.isInitialized == false) {
      return const Center(
        child: CircularProgressIndicator()
      );
    }

    print("begin");
    print(DateTime.now().millisecondsSinceEpoch);

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white,),
          onPressed: () {
            Navigator.pop(context);
          },
        ),
        title: const Text("Tracking", style: TextStyle(color: Colors.white)),
        backgroundColor: Colors.black,
      ),
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.only(left: 400, right: 400, top: 0, bottom: 0),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(20),
                child: CameraPreview(cameraController!),
              ),
            ),
            // Padding(
            //   padding: EdgeInsets.symmetric(horizontal: 400),
            //   child: SizedBox(
            //       height: 70,
            //       child: Row(
            //         children: [
            //           Expanded(child: Column(
            //             crossAxisAlignment: CrossAxisAlignment.center,
            //             children: [
            //               Text("Bicep Curl", style: Theme.of(context).textTheme.titleLarge?.copyWith(color: Colors.white, fontWeight: FontWeight.bold)),
            //               Text("Current Exercise", style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: Colors.white))
            //             ],
            //           )),
            //           Container(color: Colors.white, width: 2),
            //           Expanded(child: Column(
            //             crossAxisAlignment: CrossAxisAlignment.center,
            //             children: [
            //               Text("120", style: Theme.of(context).textTheme.titleLarge?.copyWith(color: Colors.white, fontWeight: FontWeight.bold)),
            //               Text("Pace", style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: Colors.white))
            //             ],
            //           ))
            //         ],
            //       )
            //   )
            // ),
            // StreamBuilder(
            //   stream: videoChannel.stream,
            //   builder: (context, snapshot) {
            //     return Text(snapshot.hasData ? '${snapshot.data}' : '');
            //   },
            // ),
            // TextButton(
            //   child: Text("Fuck your shit"),
            //   onPressed: () {
            //     videoChannel.sink.add('{"exercise":"bicep curl", "bpm":"69"}');
            //   },
            // ),
            Padding(
                padding: EdgeInsets.symmetric(horizontal: 400),
                child: StreamBuilder(
                  stream: videoChannel.stream,
                  builder: (context, snapshot) {
                    print("hello world");
                    print(snapshot.data);
                    // checkConnection();

                    if (!snapshot.hasData) {
                      return Text("Setting Up...", style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: Colors.white));
                    }

                    try {
                      print("hi");
                      final values = jsonDecode(snapshot.data);
                      print(values);
                      final String exercise = values['exercise'];
                      final String bpm = values['bpm'];

                      print(exercise);
                      print(bpm);

                      return SizedBox(
                          height: 70,
                          child: Row(
                            children: [
                              Expanded(child: Column(
                                crossAxisAlignment: CrossAxisAlignment.center,
                                children: [
                                  Text(exercise, /*"Bicep Curl",*/ style: Theme.of(context).textTheme.titleLarge?.copyWith(color: Colors.white, fontWeight: FontWeight.bold)),
                                  Text("Current Exercise", style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: Colors.white))
                                ],
                              )),
                              Container(color: Colors.white, width: 2),
                              Expanded(child: Column(
                                crossAxisAlignment: CrossAxisAlignment.center,
                                children: [
                                  Text(bpm, /*"120",*/ style: Theme.of(context).textTheme.titleLarge?.copyWith(color: Colors.white, fontWeight: FontWeight.bold)),
                                  Text("Pace", style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: Colors.white))
                                ],
                              ))
                            ],
                          )
                      );
                    } catch (e) {
                      return Text("Waiting for Results", style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: Colors.white));
                    }

                    return Center(
                      child: Text(snapshot.hasData ? '${snapshot.data}' : 'Nada', style: TextStyle(color: Colors.white)),
                    );
                  },
                ),
            )
            // ElevatedButton(
            //   child: Text("erm"),
            //   onPressed: () {
            //     videoChannel.sink.add("Hello world");
            //   }
            // )
          ]
        ),
      )
    );
  }


}