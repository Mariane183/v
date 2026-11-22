import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonContent, IonHeader, IonTitle, IonToolbar } from '@ionic/angular';

@Component({
  selector: 'app-cfa-view',
  templateUrl: './cfa-view.page.html',
  styleUrls: ['./cfa-view.page.scss'],
  imports: [IonContent, IonHeader, IonTitle, IonToolbar, CommonModule, FormsModule],
})
export class CfaViewPage implements OnInit {
  constructor() {}

  ngOnInit() {}
}
